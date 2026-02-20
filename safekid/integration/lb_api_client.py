"""
SafeKid Flash — Little Brother API Client
==========================================
Wrapper sederhana untuk REST API Little Brother.
Digunakan oleh launcher_server.py untuk membaca
data waktu dan profil anak dari Little Brother.

Dokumentasi API Little Brother:
https://github.com/marcus67/little_brother/blob/master/API.md
"""

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger("safekid.lb_client")


# ────────────────────────────────────────────────────
#  Data Models
# ────────────────────────────────────────────────────

@dataclass
class UserStatus:
    """Status monitoring untuk satu user dari Little Brother."""
    username: str
    minutes_today: int         = 0   # sudah dipakai hari ini
    allowed_minutes: int       = 90  # batas harian
    active: bool               = False
    logged_in_since: Optional[str] = None
    warning_before_end: int    = 5   # menit peringatan sebelum habis
    max_activity_duration: int = 0   # maks sesi tanpa istirahat
    error: Optional[str]       = None

    @property
    def remaining_minutes(self) -> int:
        return max(0, self.allowed_minutes - self.minutes_today)

    @property
    def remaining_seconds(self) -> int:
        return self.remaining_minutes * 60

    @property
    def total_seconds(self) -> int:
        return self.allowed_minutes * 60

    @property
    def usage_ratio(self) -> float:
        if self.allowed_minutes == 0:
            return 1.0
        return self.minutes_today / self.allowed_minutes

    @property
    def is_time_up(self) -> bool:
        return self.remaining_minutes <= 0


@dataclass
class LBConfig:
    base_url: str     = "http://localhost:5555"
    username: str     = ""          # LB admin username
    password: str     = ""          # LB admin password
    timeout: int      = 5           # request timeout in seconds
    retry_count: int  = 3


# ────────────────────────────────────────────────────
#  Client
# ────────────────────────────────────────────────────

class LittleBrotherClient:
    """
    Client untuk Little Brother REST API.
    
    Contoh penggunaan:
        client = LittleBrotherClient(LBConfig(
            base_url="http://localhost:5555",
            username="admin",
            password="secret"
        ))
        status = client.get_user_status("budi")
        print(f"Remaining: {status.remaining_minutes} min")
    """

    API_PATH_STATUS   = "/api/v1/user-status"    # GET all users
    API_PATH_OVERRIDE = "/api/v1/override"         # POST override

    def __init__(self, config: Optional[LBConfig] = None):
        self.config = config or LBConfig()
        self._session = None
        self._last_connected = 0.0
        self._connected = False

        if not HAS_REQUESTS:
            logger.warning("'requests' not installed. LB integration disabled.")

    def _get_session(self):
        """Lazy-init requests.Session dengan auth."""
        if self._session is None and HAS_REQUESTS:
            self._session = requests.Session()
            if self.config.username and self.config.password:
                self._session.auth = (self.config.username, self.config.password)
        return self._session

    def _url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}{path}"

    def ping(self) -> bool:
        """Cek apakah Little Brother server berjalan."""
        if not HAS_REQUESTS:
            return False
        try:
            r = self._get_session().get(
                self._url("/"),
                timeout=self.config.timeout
            )
            self._connected = r.status_code < 500
            self._last_connected = time.time()
            return self._connected
        except Exception as e:
            logger.debug(f"LB ping failed: {e}")
            self._connected = False
            return False

    def get_user_status(self, child_name: str) -> UserStatus:
        """
        Ambil status waktu untuk satu user.
        Mengembalikan UserStatus dengan error jika tidak bisa connect.
        """
        status = UserStatus(username=child_name)

        if not HAS_REQUESTS:
            status.error = "requests not installed"
            return status

        for attempt in range(self.config.retry_count):
            try:
                r = self._get_session().get(
                    self._url(self.API_PATH_STATUS),
                    timeout=self.config.timeout
                )

                if r.status_code == 200:
                    data = r.json()
                    # LB returns dict of users
                    # Key format varies by version — try common formats
                    user_data = (
                        data.get(child_name)
                        or data.get(child_name.lower())
                        or self._find_user_in_response(data, child_name)
                    )

                    if user_data:
                        status.minutes_today      = self._safe_int(user_data, "minutes_today", 0)
                        status.allowed_minutes    = self._safe_int(user_data, "max_time_per_day", 90)
                        status.active             = user_data.get("active", False)
                        status.logged_in_since    = user_data.get("logged_in_since")
                        status.warning_before_end = self._safe_int(user_data, "min_time_of_day", 5)
                    else:
                        logger.warning(f"User '{child_name}' not found in LB response.")
                        status.error = f"User '{child_name}' not found"
                    return status

                elif r.status_code == 401:
                    status.error = "LB auth failed — check username/password"
                    return status
                else:
                    logger.warning(f"LB returned HTTP {r.status_code}")

            except requests.exceptions.ConnectionError:
                logger.debug(f"LB connection refused (attempt {attempt+1})")
                if attempt < self.config.retry_count - 1:
                    time.sleep(2)
            except requests.exceptions.Timeout:
                logger.debug("LB request timed out")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                status.error = str(e)
                return status

        status.error = "Could not connect to Little Brother"
        return status

    def override_add_time(self, child_name: str, minutes: int) -> bool:
        """
        Tambah waktu untuk anak (override).
        Membutuhkan admin cookie/session di LB.
        Returns True jika berhasil.
        """
        if not HAS_REQUESTS:
            return False
        try:
            r = self._get_session().post(
                self._url(self.API_PATH_OVERRIDE),
                json={"user": child_name, "add_minutes": minutes},
                timeout=self.config.timeout
            )
            return r.status_code == 200
        except Exception as e:
            logger.error(f"override_add_time error: {e}")
            return False

    def _find_user_in_response(self, data: dict, child_name: str) -> Optional[dict]:
        """Cari user data di berbagai format response LB."""
        # Format: {"users": [{name: "budi", ...}]}
        if "users" in data:
            for u in data["users"]:
                if u.get("name", "").lower() == child_name.lower():
                    return u
        # Format: {"data": {username: {...}}}
        if "data" in data and isinstance(data["data"], dict):
            return data["data"].get(child_name)
        return None

    @staticmethod
    def _safe_int(d: dict, key: str, default: int = 0) -> int:
        try:
            return int(d.get(key, default))
        except (ValueError, TypeError):
            return default

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __repr__(self):
        return f"LittleBrotherClient(url={self.config.base_url}, connected={self._connected})"


# ────────────────────────────────────────────────────
#  Convenience factory
# ────────────────────────────────────────────────────

def create_client_from_env() -> LittleBrotherClient:
    """
    Buat client dari environment variables:
        SAFEKID_LB_URL      = http://localhost:5555
        SAFEKID_LB_USER     = admin
        SAFEKID_LB_PASSWORD = secret
    """
    return LittleBrotherClient(LBConfig(
        base_url=os.environ.get("SAFEKID_LB_URL", "http://localhost:5555"),
        username=os.environ.get("SAFEKID_LB_USER", ""),
        password=os.environ.get("SAFEKID_LB_PASSWORD", ""),
    ))


# ────────────────────────────────────────────────────
#  Quick test (run directly)
# ────────────────────────────────────────────────────
if __name__ == "__main__":
    import json as _json

    logging.basicConfig(level=logging.DEBUG)

    print("SafeKid Flash — LB API Client Test")
    print("-" * 40)

    client = create_client_from_env()

    print(f"Pinging {client.config.base_url}...")
    if client.ping():
        print("✅ Little Brother is running!")

        child = input("Child username to check [budi]: ").strip() or "budi"
        status = client.get_user_status(child)

        print(f"\n📊 Status for '{child}':")
        print(f"   Used today  : {status.minutes_today} min")
        print(f"   Allowed     : {status.allowed_minutes} min")
        print(f"   Remaining   : {status.remaining_minutes} min")
        print(f"   Active now  : {status.active}")
        print(f"   Time up?    : {status.is_time_up}")
    else:
        print("❌ Little Brother not reachable.")
        print("   Run in demo mode: python launcher_server.py --demo")
