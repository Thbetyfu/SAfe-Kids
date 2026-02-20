# 🛡️ SafeKid Flash

<div align="center">

**Sistem parental control anak berbasis Linux**  
*Dibangun di atas [Little Brother](https://github.com/marcus67/little_brother) — aktif & open-source*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green?logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-GPL--3.0-orange)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Live%20USB-lightgrey)]()

</div>

---

## ✨ Apa Itu SafeKid Flash?

SafeKid Flash adalah **modifikasi dari Little Brother** yang mengubahnya menjadi sistem lengkap untuk melindungi anak-anak saat menggunakan komputer — bisa di-*boot* langsung dari flashdisk!

**Little Brother** sudah menyediakan:
- ⏰ Time limits harian & mingguan
- 📊 Monitoring proses aktif
- 🌐 Flask web dashboard
- 🗄️ SQLite/MySQL database

**SafeKid Flash menambahkan:**
- 🎨 **Kid-Friendly UI** — Launcher berwarna dengan timer visual besar
- 📱 **Apps Launcher** — 12+ app edukasi terintegrasi
- 🔒 **Content Filtering** — DNS + blocklist 200k+ domain
- 👨‍👩‍👧 **Parent Dashboard** — Kontrol waktu real-time berbasis PIN
- 🔌 **Live USB Boot** — Bisa langsung boot dari flashdisk

---

## 🚀 Quick Start (Windows — Demo Mode)

```bash
# Clone / download project
cd E:\SafeKidFlash

# Install dependencies
pip install flask requests

# Jalankan demo (tidak perlu Little Brother)
python safekid\kid_ui\launcher_server.py --demo --child-name "Budi" --total-minutes 90

# Buka browser
# Kid UI    → http://localhost:5556/
# Parent    → http://localhost:5556/parent  (PIN: 1234)
```

Atau **double-click** `start_demo.bat` untuk otomatis!

---

## 📁 Struktur Project

```
E:\SafeKidFlash\
│
├── 📄 start_demo.bat          ← Double-click untuk demo!
├── 📄 run_tests.py            ← Jalankan test suite
├── 📄 requirements.txt
├── 📄 README.md
├── 📄 CHANGELOG.md
│
├── 📁 safekid/
│   ├── 📁 kid_ui/             ← Kid Launcher UI
│   │   ├── launcher.html      ← Dashboard anak (HTML/CSS/JS)
│   │   └── launcher_server.py ← Flask server (port 5556)
│   │
│   ├── 📁 apps/               ← Apps Launcher
│   │   ├── apps_catalog.json  ← 12 app edukasi + game
│   │   └── apps_launcher.py   ← Cross-platform launcher
│   │
│   ├── 📁 content_filter/     ← Content Filtering
│   │   ├── dns_filter.py      ← DNS → OpenDNS/Cloudflare Family
│   │   ├── blocklist_manager.py ← 200k+ domain blocklist
│   │   └── filter_manager.py  ← Facade: enable/disable semua
│   │
│   └── 📁 integration/        ← Little Brother Integration
│       └── lb_api_client.py   ← REST API client
│
├── 📁 config/
│   └── safekid_default.conf   ← Konfigurasi lengkap (INI format)
│
├── 📁 tests/                  ← Automated Test Suite
│   ├── test_server.py         ← 8 tests: API endpoints
│   ├── test_apps_launcher.py  ← 5 tests: age & category filters
│   └── test_content_filter.py ← 3 tests: blocklist & age presets
│
└── 📁 live-usb/               ← Linux Deployment
    ├── safekid.service         ← Systemd unit (autorun backend)
    ├── kiosk.sh                ← Chromium kiosk mode launcher
    ├── setup_linux.sh          ← Installer otomatis (sudo)
    └── BUILD_GUIDE.md          ← Panduan membuat bootable USB
```

---

## 🌐 Halaman & API

| URL | Untuk | Keterangan |
|-----|-------|-----------|
| `http://localhost:5556/` | 👦 Anak | Dashboard utama dengan timer & app grid |
| `http://localhost:5556/parent` | 👨‍👩‍👧 Orang Tua | Kontrol waktu (PIN protected) |
| `http://localhost:5556/api/status` | API | Status waktu JSON |
| `http://localhost:5556/api/apps` | API | Daftar app dari catalog |
| `http://localhost:5556/api/launch` | API | Log launch app |
| `http://localhost:5556/api/admin/set-time` | Admin API | Tambah/kurangi waktu |

---

## 🎨 Screenshot Kid UI

```
┌─────────────────────────────────────────────────────┐
│  🛡️ SafeKid Flash        Halo, Budi! ✨    🔑 Orang Tua │
├──────────────────┬──────────────────────────────────┤
│  ⏳ Sisa Waktu   │  🎮 Pilih Aktivitas               │
│                  │  🌟 Semua  📚 Belajar  🎮 Main   │
│   [  44:23  ]    │  ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│     hijau         │  │ 🔢 │ │ 🎨 │ │ 🐱 │ │ ⛏️ │   │
│  Selamat main! 🎉│  │GCom│ │Tux │ │Scra│ │Mine│   │
│                  │  │pris│ │Pain│ │tch │ │test│   │
│  📊 Statistik   │  └────┘ └────┘ └────┘ └────┘   │
│  🔥5 Hari       │                                   │
│  3 App Dibuka   │  ⚡ Aktivitas Terakhir            │
│  45m Dipakai    │  🔢 GCompris — 14:30             │
│  ⭐ 12 Bintang  │  🎨 Tux Paint — 13:15            │
│                  │                                  │
│  💬 "Belajar     │                                  │
│   hal baru!"    │                                  │
└──────────────────┴──────────────────────────────────┘
```

---

## ⚙️ Konfigurasi

Edit `config/safekid_default.conf`:

```ini
[general]
child_name = Budi
child_age  = 9

[time_limits]
weekday_limit_minutes = 60   # 1 jam hari sekolah
weekend_limit_minutes = 120  # 2 jam akhir pekan
warning_before_end_minutes = 10

[content_filter]
enabled      = True
dns_provider = opendns_family   # Blokir konten dewasa otomatis
block_categories = adult, gambling, violence, malware

[ui]
theme = space   # space | ocean | forest | candy
```

---

## 🔒 Content Filtering

### DNS Provider yang Tersedia

| Provider | DNS IP | Blokir |
|----------|--------|--------|
| **OpenDNS FamilyShield** ⭐ | 208.67.222.123 | Adult + Gambling + Phishing |
| Cloudflare for Families | 1.1.1.3 | Adult + Malware |
| CleanBrowsing Family | 185.228.168.168 | Adult + VPN Bypass |
| Quad9 | 9.9.9.9 | Malware only |

### Blocklist Sources

| Source | Jumlah Domain | Kategori |
|--------|--------------|---------|
| StevenBlack Adult | ~100k | Adult, Gambling |
| OISD Small | ~75k | Ads, Malware, Phishing |
| URLHaus | ~50k | Malware URLs |
| Hagezi Adult | ~150k | Adult content |
| SafeKid Custom | Custom | Tambah sendiri |

---

## 📱 Apps Catalog

| App | Kategori | Usia |
|-----|----------|------|
| 🔢 GCompris | Edu | 3–10 |
| 🎨 Tux Paint | Creative | 3–12 |
| ⌨️ Tux Typing | Edu | 5–14 |
| 🐱 Scratch | Code | 7–16 |
| ⛏️ Minetest | Game | 6+ |
| 📺 YouTube Kids | Web | 3–12 |
| 📖 Wikipedia | Web | 8+ |
| 🎵 MuseScore | Creative | 8+ |
| ♟️ Catur | Game | 6+ |

Tambah app sendiri di `safekid/apps/apps_catalog.json`.

---

## 🛠️ Konfigurasi & Testing

### Konfigurasi
Semua pengaturan ada di `config/safekid_default.conf` yang mudah dibaca.
- **Nama & Usia Anak**: Ubah `child_name` dan `child_age` sesuai profil anak.
- **Waktu Main**: Atur `weekday_limit_minutes` dan `weekend_limit_minutes`.
- **PIN Admin**: Default `1234`.

### Testing (Developer)
SafeKid Flash dilengkapi dengan **Automated Test Suite**.
Jalankan script ini untuk memastikan semua komponen berfungsi dengan baik:

```bash
python run_tests.py
```
Hasil yang diharapkan: **OK (15 tests passed)**.

---

## 🚀 Deployment (Live USB)

Untuk membuat **SafeKid Flash Live USB** yang bisa di-boot di komputer manapun:

1. Baca panduan lengkap di: [`live-usb/BUILD_GUIDE.md`](live-usb/BUILD_GUIDE.md)
2. Gunakan script `setup_linux.sh` untuk otomatisasi instalasi di lingkungan Linux.


---

## 🤝 Kontribusi

Project ini open-source dan menerima kontribusi!

1. Fork repository ini
2. Buat branch baru: `git checkout -b feature/nama-fitur`
3. Commit: `git commit -m "Add: nama fitur"`
4. Push & Pull Request

---

## 📜 Lisensi

GPL-3.0 — sama dengan Little Brother (project induk).

---

## 🙏 Credit

- **Little Brother** by [marcus67](https://github.com/marcus67/little_brother) — core parental control engine
- **StevenBlack** — hosts blocklist
- **OISD** — comprehensive DNS blocklist
- **OpenDNS** — FamilyShield DNS service
- **GCompris, Tux Paint, Scratch** — educational apps

---

<div align="center">
Made with ❤️ for Indonesian children's digital safety
</div>
