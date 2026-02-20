"""
SafeKid Flash — Auto-Update Checker
=====================================
Memeriksa versi terbaru di GitHub Releases dan memberi notifikasi
jika ada update. Tidak melakukan update otomatis — hanya notifikasi.

Usage:
    from safekid.updater import check_update, CURRENT_VERSION
    result = check_update()
    if result["update_available"]:
        print(result["message"])
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("safekid.updater")

# ─── Constants ────────────────────────────────────────────────────
CURRENT_VERSION = "0.6.0"
GITHUB_API_URL  = "https://api.github.com/repos/Thbetyfu/SAfe-Kids/releases/latest"
CHECK_INTERVAL_HOURS = 24   # Cek update 1x per hari
_CACHE_FILE = Path(__file__).parent.parent / "config" / ".update_cache"

# ─── Cache Helper ─────────────────────────────────────────────────

def _should_check() -> bool:
    """Return True if enough time has passed since the last check."""
    if not _CACHE_FILE.exists():
        return True
    try:
        last_check_str = _CACHE_FILE.read_text().strip()
        last_check = datetime.fromisoformat(last_check_str)
        return datetime.now() - last_check > timedelta(hours=CHECK_INTERVAL_HOURS)
    except Exception:
        return True


def _save_check_time() -> None:
    try:
        _CACHE_FILE.write_text(datetime.now().isoformat())
    except Exception:
        pass


# ─── Version Comparison ──────────────────────────────────────────

def _version_tuple(v: str):
    """Convert version string to comparable tuple."""
    v = v.lstrip("v")
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0, 0, 0)


def _is_newer(latest: str, current: str) -> bool:
    return _version_tuple(latest) > _version_tuple(current)


# ─── Main Check ──────────────────────────────────────────────────

def check_update(force: bool = False) -> dict:
    """
    Check GitHub for a newer release.
    
    Args:
        force: Skip cache interval and check immediately.
    
    Returns:
        {
            "update_available": bool,
            "current_version": str,
            "latest_version": Optional[str],
            "release_url": Optional[str],
            "message": str,
            "error": Optional[str],
        }
    """
    result = {
        "update_available": False,
        "current_version": CURRENT_VERSION,
        "latest_version": None,
        "release_url": None,
        "message": "",
        "error": None,
    }

    if not force and not _should_check():
        result["message"] = f"Skipping update check (last checked recently)"
        return result

    try:
        # Use urllib (built-in) — no extra deps
        import urllib.request
        import json

        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "User-Agent": f"SafeKid-Flash/{CURRENT_VERSION}",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        latest_tag = data.get("tag_name", "").lstrip("v")
        html_url   = data.get("html_url", GITHUB_API_URL)
        body       = data.get("body", "")

        _save_check_time()

        if not latest_tag:
            result["message"] = "No releases found on GitHub yet."
            return result

        result["latest_version"] = latest_tag
        result["release_url"]    = html_url

        if _is_newer(latest_tag, CURRENT_VERSION):
            result["update_available"] = True
            result["message"] = (
                f"Update tersedia: v{CURRENT_VERSION} -> v{latest_tag}\n"
                f"Download: {html_url}"
            )
            logger.info(f"Update available: {CURRENT_VERSION} -> {latest_tag}")
        else:
            result["message"] = f"SafeKid Flash v{CURRENT_VERSION} sudah versi terbaru."
            logger.debug("No update available.")

    except Exception as e:
        result["error"] = str(e)
        result["message"] = "Tidak dapat memeriksa pembaruan (offline atau GitHub tidak tersedia)."
        logger.warning(f"Update check failed: {e}")

    return result


# ─── Quick Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    res = check_update(force=True)
    print(res["message"])
    if res["error"]:
        print(f"Error: {res['error']}")
    sys.exit(0 if not res["error"] else 1)
