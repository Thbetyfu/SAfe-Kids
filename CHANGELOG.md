# 📋 SafeKid Flash — Changelog

Semua perubahan signifikan pada project ini didokumentasikan di sini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased — v0.8.0+]

### Planned
- Screenshot real di README
- Panduan orang tua (`docs/PARENT_GUIDE.md`)
- Live USB ISO builder otomatis
- Integrasi Little Brother penuh (online mode)

---

## [0.7.0] — Priority 2 — Quality & Polish (2026-02-20)

### Added
- 🌐 **i18n (Internationalization)**: `safekid/i18n.py`
  - 38 translation keys untuk Bahasa Indonesia & English
  - `t("welcome", name="Budi")` → `"Halo, Budi!"`
  - `set_lang("en")` untuk ganti bahasa global
  - `/api/i18n?lang=en` endpoint untuk frontend
  - Bahasa dibaca dari `config/safekid_default.conf → [general] language`
- 🔄 **Auto-Update Checker**: `safekid/updater.py`
  - Memeriksa GitHub Releases API untuk versi terbaru
  - Cache 24 jam (`config/.update_cache`) — tidak spam API
  - `/api/update-check` endpoint (tambah `?force=true` untuk paksa cek)
  - Background thread saat startup — tidak memblokir server
  - `_is_newer()` perbandingan versi semantik

### Improved
- 📋 **Logging**: Dual handler — console + `safekid.log` file
  - Format lebih informatif: `%(levelname)-8s` aligned
  - Tangkap semua error ke file untuk debugging
- 🛡️ **Error Handlers**: JSON error responses untuk semua status
  - `404` → JSON dengan hint endpoint yang valid
  - `500` → JSON dengan detail error + log stack trace
  - `405` → JSON dengan daftar method yang valid

### Tests
- `tests/test_i18n_updater.py`: 13 tests baru (total: **28 tests**)
  - `TestI18n`: 8 tests — translation, fallback, bilingual key parity
  - `TestUpdater`: 4 tests — version format, comparison, tuple parsing

---

## [0.6.0] — Priority 1 — Security & Polish (2026-02-20)

### Added
- 🔐 **Hashed PIN System**: SHA256 `hashlib`
  - `hash_pin()` / `verify_pin()` helper
  - `admin_pin` → `admin_pin_hash` di config
  - `--setup` flag: wizard interaktif ganti PIN (disimpan ke config)
- 📄 **LICENSE**: GPL-3.0 resmi dari gnu.org
- 📦 **requirements-dev.txt**: pytest, pytest-cov, flake8, mypy, black

### Fixed
- 🪟 **UnicodeEncodeError**: Print banner menggunakan `_p()` helper ASCII-safe
- 🐛 **apps_catalog.json**: Rebuild dari awal setelah rusak saat test toggle

---


## [0.5.0] — Week 5 — Testing & Polish (2026-02-20)

### Added
- ✅ **Automated Test Suite**: 15 unit tests — `run_tests.py`
  - `tests/test_server.py` — semua API endpoint (auth, time control, apps)
  - `tests/test_apps_launcher.py` — age/category filtering logic
  - `tests/test_content_filter.py` — blocklist CRUD & age presets
- 🎨 **UI Polish**: CSS `font-family` emoji stack untuk render emoji konsisten di semua OS
  (`'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji'`)

### Fixed
- 🐛 **Bug**: `/api/apps?cat=edu` di fallback mode (tanpa `AppsLauncher`) mengembalikan
  semua kategori — kini memfilter dengan benar
- 🐛 **Bug**: `add_domain()` di `blocklist_manager.py` tidak langsung update in-memory set,
  sehingga `is_blocked()` tidak mendeteksi domain baru — kini langsung update memori
- 💪 **Config Robustness**: `get_int()` helper di `launcher_server.py` — nilai integer yang 
  tidak valid di config file kini ditangani dengan graceful fallback (tidak crash)
- 🌐 **Multilingual error**: Test error message diperbarui agar accept Bahasa Indonesia 
  ATAU English

### Changed
- `README.md`: Ditambahkan section "Konfigurasi & Testing" dengan instruksi `python run_tests.py`

---

## [0.4.0] — Week 4 — Live USB & Linux Integration (2026-02-20)

### Added
- 🐧 `live-usb/safekid.service` — Systemd unit file untuk autorun backend di Linux
- 🖥️ `live-usb/kiosk.sh` — Script Chromium kiosk mode (fullscreen, no browser UI)
- ⚙️ `live-usb/setup_linux.sh` — Installer otomatis: install dependencies, copy files, 
  enable service
- 📖 `live-usb/BUILD_GUIDE.md` — Panduan lengkap membuat bootable USB persistent

### Changed
- `launcher_server.py`:
  - Sekarang membaca `config/safekid_default.conf` sebagai sumber konfigurasi utama
  - Prioritas: CLI arg > Config file > Default hardcoded
  - Ditambahkan `--config` argumen untuk custom path config
- `config/safekid_default.conf`: Config file lengkap (General, Time Limits, Content Filter,
  UI, Apps, Little Brother, Notifications, Live USB)
- `start_demo.bat`: Diperbarui untuk v2.0 — buka browser otomatis, tampilkan info Live USB

---

## [0.3.0] — Week 3 — Content Filter Module (2026-02-20)

### Added
- 🔒 `safekid/content_filter/dns_filter.py`:
  - 4 provider DNS aman: OpenDNS FamilyShield, Cloudflare for Families, 
    CleanBrowsing, Quad9
  - Backup & restore DNS otomatis
  - Dry-run mode untuk testing di Windows
  - File immutable lock (`chattr +i`) untuk mencegah bypass
- 📋 `safekid/content_filter/blocklist_manager.py`:
  - Download blocklist dari StevenBlack, OISD, URLHaus, Hagezi
  - Parse format `hosts` dan `domains`
  - Gabungkan semua menjadi satu file
  - Custom domain add/remove
  - Subdomain matching (block `sub.badsite.com` via `badsite.com`)
- 🎛️ `safekid/content_filter/filter_manager.py`:
  - Facade yang mengintegrasikan DNS + Blocklist
  - Age-based presets (usia 0-6, 7-12, 13-17, 18+)
  - Status reporting
- `config/safekid_default.conf`: File konfigurasi INI lengkap
- `README.md`: Dokumentasi project lengkap

### Changed
- Package structure diperbaiki — semua folder kini punya `__init__.py`

---

## [0.2.0] — Week 2 — Apps Launcher & Parent Dashboard (2026-02-19)

### Added
- 📱 `safekid/apps/apps_catalog.json`: Katalog 12 app edukasi + game
  (GCompris, Tux Paint, Tux Typing, Scratch, Minetest, YouTube Kids, dll)
- 🚀 `safekid/apps/apps_launcher.py`:
  - Load catalog dari JSON
  - Filter by age & category
  - Windows: buka URL di browser
  - Linux: exec command
  - Toggle enable/disable per app
  - Persist state ke JSON
- 👨‍👩‍👧 `safekid/kid_ui/launcher_server.py` v2:
  - Parent Dashboard (PIN protected) di `/parent`
  - API `/api/apps` — daftar app dengan filtering
  - API `/api/launch` — launch app + log aktivitas
  - API `/api/activity` — riwayat aktivitas
  - API `/api/admin/set-time` — tambah/atur waktu
  - API `/api/admin/toggle-app` — enable/disable app
  - Background ticker (demo mode) & LB poller

---

## [0.1.0] — Week 1 — Kid UI (2026-02-19)

### Added
- 🎨 `safekid/kid_ui/launcher.html`:
  - Timer visual besar dengan ring SVG countdown
  - App grid dengan kategori tabs
  - Panel statistik (streak, bintang, waktu pakai)
  - Kutipan motivasi
  - Aktivitas terakhir
  - Dark space theme dengan glassmorphism
- 🌐 `safekid/kid_ui/launcher_server.py` v1:
  - Flask server port 5556
  - Serve `launcher.html`
  - API `/api/status` — status waktu anak
  - Background timer thread (demo mode)
- 🔗 `safekid/integration/lb_api_client.py`:
  - Client REST API untuk Little Brother
  - Sinkronisasi data user
- `start_demo.bat`: Launcher Windows satu klik
- `safekid/apps/apps_catalog.json` (versi awal)

---

*Dibuat dengan ❤️ untuk keamanan digital anak Indonesia*
