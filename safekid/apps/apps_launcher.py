"""
SafeKid Flash — Apps Launcher
===============================
Membaca apps_catalog.json dan meluncurkan aplikasi edukasi
secara cross-platform (Linux + Windows).

Linux : gunakan 'linux_cmd' dari catalog
Windows: gunakan 'windows_url' (buka di browser) atau 'windows_cmd'
"""

import json
import logging
import os
import platform
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("safekid.apps_launcher")

CATALOG_PATH = Path(__file__).parent / "apps_catalog.json"
IS_WINDOWS   = platform.system() == "Windows"
IS_LINUX     = platform.system() == "Linux"


# ────────────────────────────────────────────────────
#  Data
# ────────────────────────────────────────────────────

class AppEntry:
    def __init__(self, data: dict):
        self.id          = data["id"]
        self.name        = data["name"]
        self.icon        = data.get("icon", "🔵")
        self.description = data.get("description", "")
        self.category    = data.get("category", "edu")
        self.color       = data.get("color", "#4ECDC4")
        self.badge       = data.get("badge", "App")
        self.min_age     = data.get("min_age", 0)
        self.max_age     = data.get("max_age", 99)
        self.linux_cmd   = data.get("linux_cmd", "")
        self.windows_url = data.get("windows_url", "")
        self.windows_cmd = data.get("windows_cmd", "")
        self.website     = data.get("website", "")
        self.enabled     = data.get("enabled", True)
        self.gradient    = data.get("gradient",
            f"linear-gradient(135deg, rgba(78,205,196,0.15), transparent)")

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "icon":        self.icon,
            "description": self.description,
            "category":    self.category,
            "color":       self.color,
            "badge":       self.badge,
            "min_age":     self.min_age,
            "max_age":     self.max_age,
            "enabled":     self.enabled,
            "gradient":    self.gradient,
            "launchable":  self._is_launchable(),
        }

    def _is_launchable(self) -> bool:
        if IS_WINDOWS:
            return bool(self.windows_url or self.windows_cmd)
        return bool(self.linux_cmd)


class LaunchResult:
    def __init__(self, success: bool, message: str, pid: Optional[int] = None):
        self.success = success
        self.message = message
        self.pid     = pid
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "success":   self.success,
            "message":   self.message,
            "pid":       self.pid,
            "timestamp": self.timestamp,
        }


# ────────────────────────────────────────────────────
#  Launcher
# ────────────────────────────────────────────────────

class AppsLauncher:
    """
    Mengelola katalog aplikasi dan peluncurannya.

    Usage:
        launcher = AppsLauncher()
        result = launcher.launch("gcompris")
        print(result.message)
    """

    def __init__(self, catalog_path: Path = CATALOG_PATH, child_age: int = 0):
        self.catalog_path  = catalog_path
        self.child_age     = child_age
        self._apps: Dict[str, AppEntry] = {}
        self._categories: Dict[str, dict] = {}
        self._running_procs: Dict[str, subprocess.Popen] = {}
        self.launch_log: List[dict] = []   # history
        self._load_catalog()

    def _load_catalog(self):
        """Load apps dari JSON catalog."""
        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                data = json.load(f)
            for app_data in data.get("apps", []):
                entry = AppEntry(app_data)
                self._apps[entry.id] = entry
            self._categories = data.get("categories", {})
            logger.info(f"Loaded {len(self._apps)} apps from catalog")
        except FileNotFoundError:
            logger.error(f"Catalog not found: {self.catalog_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Catalog JSON error: {e}")

    def reload_catalog(self):
        """Hot-reload catalog (useful for admin changes)."""
        self._apps.clear()
        self._load_catalog()

    # ── Getters ──────────────────────────────────────

    def get_all_apps(self, only_enabled: bool = True,
                     age: Optional[int] = None) -> List[AppEntry]:
        age = age or self.child_age
        apps = list(self._apps.values())
        if only_enabled:
            apps = [a for a in apps if a.enabled]
        if age > 0:
            apps = [a for a in apps if a.min_age <= age <= a.max_age]
        return apps

    def get_apps_by_category(self, category: str,
                              only_enabled: bool = True) -> List[AppEntry]:
        return [a for a in self.get_all_apps(only_enabled)
                if a.category == category]

    def get_app(self, app_id: str) -> Optional[AppEntry]:
        return self._apps.get(app_id)

    def get_categories(self) -> dict:
        return self._categories

    def apps_as_dict(self, only_enabled: bool = True,
                     age: Optional[int] = None) -> List[dict]:
        return [a.to_dict() for a in self.get_all_apps(only_enabled, age)]

    # ── Launch ───────────────────────────────────────

    def launch(self, app_id: str) -> LaunchResult:
        """
        Luncurkan aplikasi berdasarkan ID.
        - Windows: buka URL di browser, atau jalankan .exe
        - Linux  : jalankan perintah shell
        """
        app = self.get_app(app_id)
        if not app:
            return LaunchResult(False, f"App '{app_id}' not found in catalog")

        if not app.enabled:
            return LaunchResult(False, f"App '{app.name}' is disabled")

        # Log the launch regardless of success
        self._log_launch(app)

        try:
            if IS_WINDOWS:
                return self._launch_windows(app)
            else:
                return self._launch_linux(app)
        except Exception as e:
            logger.error(f"Failed to launch {app_id}: {e}")
            return LaunchResult(False, f"Launch error: {e}")

    def _launch_windows(self, app: AppEntry) -> LaunchResult:
        # Prefer windows_cmd (e.g. path to .exe), then fallback to URL
        if app.windows_cmd:
            try:
                proc = subprocess.Popen(
                    app.windows_cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self._running_procs[app.id] = proc
                logger.info(f"[WIN] Launched {app.name} PID={proc.pid}")
                return LaunchResult(True, f"Membuka {app.name}...", proc.pid)
            except Exception as e:
                logger.warning(f"windows_cmd failed: {e}, trying URL...")

        if app.windows_url:
            webbrowser.open(app.windows_url)
            logger.info(f"[WIN] Opened browser: {app.windows_url}")
            return LaunchResult(True, f"Membuka {app.name} di browser...", None)

        return LaunchResult(False,
            f"{app.name} belum tersedia di Windows. "
            f"Download di: {app.website or 'lihat website'}")

    def _launch_linux(self, app: AppEntry) -> LaunchResult:
        if not app.linux_cmd:
            return LaunchResult(False, f"No Linux command for {app.name}")

        # Check if command exists
        cmd_name = app.linux_cmd.split()[0]
        if not self._cmd_exists(cmd_name):
            return LaunchResult(False,
                f"{app.name} belum terinstall.\n"
                f"Install: sudo apt install {cmd_name}")

        try:
            proc = subprocess.Popen(
                app.linux_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self._running_procs[app.id] = proc
            logger.info(f"[LNX] Launched {app.name} PID={proc.pid}")
            return LaunchResult(True, f"Membuka {app.name}...", proc.pid)
        except Exception as e:
            return LaunchResult(False, f"Gagal membuka {app.name}: {e}")

    # ── App Management ───────────────────────────────

    def toggle_app(self, app_id: str, enabled: bool) -> bool:
        """Enable/disable app. Returns True if successful."""
        app = self.get_app(app_id)
        if not app:
            return False
        app.enabled = enabled
        # Persist to catalog JSON
        self._save_catalog()
        return True

    def _save_catalog(self):
        """Save current state back to catalog JSON."""
        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                data = json.load(f)
            for app_data in data.get("apps", []):
                app = self._apps.get(app_data["id"])
                if app:
                    app_data["enabled"] = app.enabled
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Catalog saved.")
        except Exception as e:
            logger.error(f"Failed to save catalog: {e}")

    # ── Utilities ────────────────────────────────────

    def _log_launch(self, app: AppEntry):
        entry = {
            "app_id":    app.id,
            "name":      app.name,
            "icon":      app.icon,
            "timestamp": datetime.now().isoformat(),
            "time_str":  datetime.now().strftime("%H:%M"),
            "platform":  "windows" if IS_WINDOWS else "linux",
        }
        self.launch_log.insert(0, entry)
        self.launch_log = self.launch_log[:50]

    @staticmethod
    def _cmd_exists(cmd: str) -> bool:
        """Check if a command is available in PATH."""
        import shutil
        return shutil.which(cmd) is not None

    def kill_app(self, app_id: str) -> bool:
        """Kill a running app by ID."""
        proc = self._running_procs.get(app_id)
        if proc and proc.poll() is None:
            proc.terminate()
            del self._running_procs[app_id]
            return True
        return False

    def get_running_apps(self) -> List[str]:
        """Return list of currently running app IDs."""
        alive = []
        for app_id, proc in list(self._running_procs.items()):
            if proc.poll() is None:
                alive.append(app_id)
            else:
                del self._running_procs[app_id]
        return alive

    def __repr__(self):
        return f"AppsLauncher({len(self._apps)} apps, {len(self._running_procs)} running)"


# ────────────────────────────────────────────────────
#  Quick Test
# ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    launcher = AppsLauncher()
    print(f"\n📚 {launcher}")
    print(f"\nApps tersedia:")
    for app in launcher.get_all_apps():
        status = "✅" if app._is_launchable() else "🔗"
        print(f"  {status} [{app.category:8}] {app.icon} {app.name} (usia {app.min_age}-{app.max_age})")

    print(f"\n🎮 Apps kategori 'game':")
    for app in launcher.get_apps_by_category("game"):
        print(f"  {app.icon} {app.name}")
