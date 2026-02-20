"""
SafeKid Flash — Internationalization (i18n)
============================================
Sistem terjemahan sederhana untuk mendukung Bahasa Indonesia & English.

Usage:
    from safekid.i18n import t, set_lang
    set_lang("id")
    print(t("welcome", name="Budi"))    # -> "Halo, Budi!"
    set_lang("en")
    print(t("welcome", name="Budi"))    # -> "Hello, Budi!"
"""

from typing import Optional

# ─── Default Language ─────────────────────────────────────────────
_CURRENT_LANG = "id"

SUPPORTED_LANGS = ["id", "en"]

# ─── Translation Strings ──────────────────────────────────────────
TRANSLATIONS: dict = {
    "id": {
        # UI General
        "welcome":          "Halo, {name}!",
        "time_left":        "Sisa Waktu",
        "time_up":          "Waktu Habis!",
        "time_up_msg":      "Waktu bermain sudah selesai untuk hari ini. Sampai besok!",
        "streak_days":      "{n} Hari Berturut",
        "stars_earned":     "{n} Bintang",
        "open_app":         "Buka {name}",
        "all_categories":   "Semua",
        "edu":              "Belajar",
        "game":             "Main",
        "creative":         "Kreatif",
        "web":              "Internet",

        # Timer messages
        "timer_great":      "Luar biasa! Terus semangat!",
        "timer_good":       "Selamat main! Jaga waktu ya.",
        "timer_warning":    "Waktu hampir habis, segera selesaikan!",
        "timer_critical":   "Hanya {mins} menit lagi!",

        # Parent dashboard
        "parent_title":     "Panel Orang Tua",
        "parent_pin_prompt":"Masukkan PIN Orang Tua",
        "parent_login":     "Masuk",
        "add_time":         "Tambah Waktu",
        "end_session":      "Akhiri Sesi",
        "set_total":        "Atur Total Waktu",
        "activity_log":     "Log Aktivitas",
        "no_activity":      "Belum ada aktivitas hari ini.",

        # API messages
        "time_added":       "Ditambah {mins} menit!",
        "session_ended":    "Sesi diakhiri.",
        "app_enabled":      "{name} diaktifkan.",
        "app_disabled":     "{name} dinonaktifkan.",
        "wrong_pin":        "PIN salah.",
        "app_not_found":    "App '{id}' tidak ditemukan di katalog.",
        "app_launched":     "Membuka {name}...",
        "app_disabled_err": "App {name} tidak diaktifkan.",
        "launch_error":     "Gagal membuka {name}: {error}",

        # Setup
        "setup_title":      "SafeKid Flash - Pengaturan Awal",
        "setup_pin_prompt": "Masukkan PIN Orang Tua baru (4-8 digit): ",
        "setup_pin_confirm":"Konfirmasi PIN: ",
        "setup_pin_weak":   "PIN harus berupa angka minimal 4 digit.",
        "setup_pin_mismatch": "PIN tidak cocok. Coba lagi.",
        "setup_pin_ok":     "PIN berhasil disimpan!",
        "setup_pin_err":    "Gagal menyimpan config: {error}",

        # Update
        "update_available": "Tersedia versi baru: {version}. Kunjungi: {url}",
        "up_to_date":       "SafeKid Flash sudah versi terbaru ({version}).",
        "update_check_err": "Tidak dapat memeriksa pembaruan (offline?).",
    },

    "en": {
        # UI General
        "welcome":          "Hello, {name}!",
        "time_left":        "Time Left",
        "time_up":          "Time's Up!",
        "time_up_msg":      "Screen time is over for today. See you tomorrow!",
        "streak_days":      "{n} Day Streak",
        "stars_earned":     "{n} Stars",
        "open_app":         "Open {name}",
        "all_categories":   "All",
        "edu":              "Learn",
        "game":             "Play",
        "creative":         "Create",
        "web":              "Internet",

        # Timer messages
        "timer_great":      "Awesome! Keep it up!",
        "timer_good":       "Have fun! Watch the time.",
        "timer_warning":    "Time is almost up, finish what you're doing!",
        "timer_critical":   "Only {mins} minutes left!",

        # Parent dashboard
        "parent_title":     "Parent Control Panel",
        "parent_pin_prompt":"Enter Parent PIN",
        "parent_login":     "Login",
        "add_time":         "Add Time",
        "end_session":      "End Session",
        "set_total":        "Set Total Time",
        "activity_log":     "Activity Log",
        "no_activity":      "No activity today.",

        # API messages
        "time_added":       "Added {mins} minutes!",
        "session_ended":    "Session ended.",
        "app_enabled":      "{name} enabled.",
        "app_disabled":     "{name} disabled.",
        "wrong_pin":        "Wrong PIN.",
        "app_not_found":    "App '{id}' not found in catalog.",
        "app_launched":     "Opening {name}...",
        "app_disabled_err": "App {name} is not enabled.",
        "launch_error":     "Failed to open {name}: {error}",

        # Setup
        "setup_title":      "SafeKid Flash - Initial Setup",
        "setup_pin_prompt": "Enter new Parent PIN (4-8 digits): ",
        "setup_pin_confirm":"Confirm PIN: ",
        "setup_pin_weak":   "PIN must be numeric and at least 4 digits.",
        "setup_pin_mismatch": "PINs do not match. Try again.",
        "setup_pin_ok":     "PIN saved successfully!",
        "setup_pin_err":    "Failed to save config: {error}",

        # Update
        "update_available": "New version available: {version}. Visit: {url}",
        "up_to_date":       "SafeKid Flash is up to date ({version}).",
        "update_check_err": "Could not check for updates (offline?).",
    },
}


# ─── Public API ───────────────────────────────────────────────────

def set_lang(lang: str) -> None:
    """Set current language. Falls back to 'id' if unsupported."""
    global _CURRENT_LANG
    _CURRENT_LANG = lang if lang in SUPPORTED_LANGS else "id"


def get_lang() -> str:
    """Return current language code."""
    return _CURRENT_LANG


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Translate a key to the current language.
    
    Args:
        key:    Translation key (e.g. "welcome")
        lang:   Override language for this call only
        **kwargs: Variables to interpolate (e.g. name="Budi")
    
    Returns:
        Translated and formatted string.
        Falls back to key name if not found.
    
    Example:
        t("welcome", name="Budi")     -> "Halo, Budi!"
        t("time_added", mins=10)      -> "Ditambah 10 menit!"
    """
    use_lang = lang or _CURRENT_LANG
    lang_dict = TRANSLATIONS.get(use_lang, TRANSLATIONS["id"])
    
    # Fallback to "id" if key missing in current lang
    template = lang_dict.get(key) or TRANSLATIONS["id"].get(key, key)
    
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template


def t_all(key: str, **kwargs) -> dict:
    """Return translations in all supported languages."""
    return {lang: t(key, lang=lang, **kwargs) for lang in SUPPORTED_LANGS}
