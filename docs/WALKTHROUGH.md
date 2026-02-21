# 🚀 Panduan Lengkap Instalasi SafeKid Flash (VM & Live USB)

Panduan ini berisi langkah demi langkah untuk memindahkan pengujian SafeKid Flash dari Windows ke lingkungan Linux yang sebenarnya, menggunakan VirtualBox untuk *testing* sebelum disalin ke USB fisik untuk penggunaan sehari-hari oleh anak.

---

## FASE 1: Persiapan (di Windows)

### Step 1.1 — Download Software yang Dibutuhkan
Anda perlu mendownload 2 file ini:

| Software | Link Download | Ukuran |
|----------|---------------|--------|
| **VirtualBox** | [virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads) → pilih "Windows hosts" | ~100 MB |
| **Linux Mint XFCE ISO** | [linuxmint.com/download.php](https://linuxmint.com/download.php) → pilih XFCE Edition (64-bit) | ~2.5 GB |

💡 *Kenapa Linux Mint XFCE? Karena paling ringan, cocok untuk VM dan instalasi Live USB, serta sudah diuji dan direkomendasikan secara resmi oleh proyek SafeKid Flash.*

### Step 1.2 — Install VirtualBox
1. Jalankan installer VirtualBox yang sudah didownload.
2. Klik **Next** → **Next** → **Next** → **Install**.
3. Jika ditanya untuk menginstall network driver, klik **Yes**.
4. Selesai → buka VirtualBox.

---

## FASE 2: Membuat Virtual Machine

### Step 2.1 — Buat VM Baru di VirtualBox
1. Buka VirtualBox → klik **New**.
2. Isi pengaturan berikut:

| Pengaturan | Isi |
|------------|-----|
| Name | `SafeKid-Flash` |
| Folder | *(biarkan default)* |
| ISO Image | Klik browse → pilih file Linux Mint XFCE ISO yang didownload |
| Type | Linux |
| Version | Ubuntu (64-bit) |

3. Klik **Next**.

### Step 2.2 — Alokasi Resource
Berikan resource yang cukup agar lancar saat testing.

| Pengaturan | Rekomendasi | Minimum |
|------------|-------------|---------|
| RAM | 4096 MB (4 GB) | 2048 MB (2 GB) |
| CPU | 2 core | 1 core |
| Disk | 25 GB (Dynamic) | 15 GB |

Klik **Next** → **Finish**.

### Step 2.3 — Pengaturan Tambahan (Penting!)
Sebelum menjalankan (Start) VM, klik **Settings**:
- **Display**: 
  - Video Memory → **128 MB**
  - Graphics Controller → **VMSVGA**
- **Network**: 
  - Adapter 1 → Attached to: **NAT** *(agar VM bisa akses internet & filter)*
- **System**: 
  - Boot Order → Pastikan **Optical** centangnya aktif dan berada di atas.
Klik **OK**.

---

## FASE 3: Install Linux Mint di VM

### Step 3.1 — Boot VM
1. Klik **Start** pada VM SafeKid-Flash.
2. Linux Mint akan otomatis boot dari file ISO.
3. Pilih "Start Linux Mint" di boot menu grub.
4. Tunggu sampai masuk ke desktop Linux Mint.

### Step 3.2 — Install Linux Mint ke Disk Virtual
⚠️ *Ini tahap penting agar data Anda persistent (tersimpan permanen dan tidak hilang saat VM di-restart).*

1. Di desktop Linux Mint, double-click icon **"Install Linux Mint"**.
2. Ikuti wizard instalasi:

| Langkah | Instruksi |
|---------|-----------|
| Bahasa | English atau Indonesian |
| Keyboard | US (default) |
| Multimedia codecs | ✅ Centang "Install multimedia codecs" |
| Installation type | Pilih **"Erase disk and install Linux Mint"** *(Ini %100 aman, perintah ini hanya menghapus disk virtual berukuran 25GB yang kita buat di Step 2.2, bukan hardisk asli Windows Anda!)* |
| Timezone | Jakarta (UTC+7) |
| User | Isi nama Anda, username, dan password |

3. Klik **Install Now** → tunggu sekitar ~10-15 menit.
4. Setelah selesai → klik **Restart Now**.

### Step 3.3 — Lepas ISO
Saat layar menampilkan pesan "Please remove the installation medium, then press ENTER":
1. Di menu bar jendela VirtualBox (atas) → **Devices** → **Optical Drives** → Klik **Remove disk from virtual drive**.
2. Pada keyboard Anda: Tekan **Enter**.
VM akan restart dan langsung menuju sistem Linux Mint Anda yang sudah terinstal secara stabil ✅

---

## FASE 4: Install SafeKid Flash di VM

### Step 4.1 — Buka Terminal
Setelah login ke desktop Linux Mint yang baru:
- Klik logo **Menu** (di pojok kiri bawah) → ketik dan cari "Terminal" → lalu buka.
- Atau cukup tekan tombol `Ctrl + Alt + T` bersamaan.

### Step 4.2 — Update Sistem & Install Git
Copy paste perintah ini ke Terminal:
```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install git
sudo apt install -y git
```

### Step 4.3 — Clone Repository SafeKid Flash
```bash
# Pastikan Anda berada di home directory
cd ~

# Download repository SafeKid dari GitHub secara otomatis
git clone https://github.com/Thbetyfu/SAfe-Kids.git SafeKidFlash

# Masuk ke folder project
cd SafeKidFlash
```

### Step 4.4 — Lihat Isi Project (Verifikasi)
```bash
ls -la
```
Cek daftar file. Anda pasti melihat folder `safekid/` (kode sumber backend), `config/` (kumpulan setelan), `live-usb/` (script bash), file `README.md`, `run_tests.py`, dll.

### Step 4.5 — Jalankan Installer Otomatis
Sekarang, panggil build-script Linux bawaan dari repo ini agar sistem mengkonfigurasi otomatis:
```bash
# Masuk ke folder bash script deployment
cd ~/SafeKidFlash/live-usb

# Beri izin eksekusi kepada Linux
chmod +x setup_linux.sh kiosk.sh

# Eksekusi installer setup_linux (HARUS diawali kata "sudo")
sudo ./setup_linux.sh
```
Akan tampil logging sistem di Terminal Anda. Script `setup_linux.sh` bekerja secara mandiri dan otomatis mendownload paket dependensi (`python3`, `flask`, browser GUI via Chromium), membuat symlink direktori ke `/opt/safekid` dan setelan ke `/etc/safekid`, menambahkan program startup Chromium Kiosk, dan menautkan *daemon service* Linux.

### Step 4.6 — Konfigurasi Parameter (Nama, Jatah Waktu, Filter)
```bash
# Edit file konfigurasi sistem SafeKid menggunakan mode TUI text-editor Nano
sudo nano /etc/safekid/safekid.conf
```
Ganti konfigurasi yang diperlukan dengan panduan ini:
```ini
[general]
child_name = Rina              # ← [PENTING] Ganti dengan nama anak Anda
child_age = 8                  # ← Ganti dengan usia anak agar rekomendasi app relevan
language = id                  # ← id = Bahasa Indonesia, en = Inggris
theme = space                  # Pilihan warna antarmuka: space | ocean | forest | candy

[time_limits]
weekday_limit_minutes = 60     # ← Berapa menit izin bermain main setiap hari sekolah?
weekend_limit_minutes = 120    # ← Berapa menit jatah di hari libur/akhir pekan?
earliest_start = 07:00         # ← Jam aplikasi menyala otomatis?
latest_end = 21:00             # ← Jam wajib istirahat total (seluruh tab mati otomatis)?

[content_filter]
enabled = True                 # ← Blokir konten dewasa & malware di internet (Browser)
dns_provider = opendns_family
```
Untuk Simpan lalu Keluar dari Nano: Tekan `Ctrl + O` → `Enter` → Tekan `Ctrl + X`.

---

## FASE 5: Validasi Testing di Lingkungan VM

### Step 5.1 — Uji Coba Server Lokal di Linux Service Daemon
```bash
# Nyalakan service di background secara terisolasi tanpa mengganggu terminal GUI
sudo systemctl start safekid.service

# Cek apakah modul sudah online (hijau / running)
sudo systemctl status safekid.service
```
Jika sukses akan ada indikator: `Active: active (running)` ✅

### Step 5.2 — Uji Tampilan Browser Frontend
Buka saja aplikasi browser **Firefox** bawaan Linux Mint VM Anda, cek baris berikut ini:

| HTTP Server URL Route | Apa yang akan / wajib muncul? |
|-----|-----------------|
| `http://localhost:5556/` | 🧒 **Panel UI Kids** — Anda akan melihat sisa perhitungan mundur harian (Timer), daftar ikon app launcher, background "bintang/lautan/hutan", mode layar penuh |
| `http://localhost:5556/parent` | 👨‍👩‍👧 **Dashboard Induk** — Form isian PIN (Default `1234` jika belum di hash pada VM Anda). Berisi pengaturan Analitik penggunaan (Chart visual bar per minggu), tombol tambah/akhiri menit penggunaan instan. |

### Step 5.3 — Uji Coba Modul Cek API (Backend REST Validation)
Masi di terminal, kita validasi sistem responsif Flask lewat Curl GET:
```bash
curl http://localhost:5556/api/status
curl http://localhost:5556/api/apps
```

### Step 5.4 — Uji Kiosk Mode Autostart (Layar Penuh Terkunci / Safe Boot)
Ini untuk mensimulasikan persis bagaimana anak Anda menyalakan komputer dan browser terkunci tanpa bisa di X / klik minimize.
```bash
bash /opt/safekid/live-usb/kiosk.sh
```
Aplikasi GUI Kid Dashboard lewat "Chromium Kiosk Mode" akan meng-cover total 100% monitor Anda.
Untuk uji coba tekan paksa shortcut: `Alt + F4` untuk memaksa keluar dari mode ini.

### Step 5.5 — Jalankan Test Coverage (Health System Check)
Kita akan jalankan Unit Test otomatis standar pengembangan perangkat lunak TDD Python:
```bash
cd ~/SafeKidFlash

# Install modul bantu testing pytest di sistem Linux
pip3 install pytest pytest-cov requests flake8 --break-system-packages

# Mulai verifikasi
python3 run_tests.py
```
Output wjaib yang akan tertampil ke layar secara berurut ke bawah adalah: `28 tests passed` yang artinya kode 100% stabil. ✅

---

## FASE 6: Tambahan Tweaking Ekstra & Kustomisasi (Opsional)

### 6.1 — Mengganti Konfigurasi PIN Administrasi Hashed
Karena mode default pada `/api/admin` akan me-reject PIN konvensional *plain text* dari awal setup instalasi Anda untuk keamanan yang tangguh, SafeKid sudah dilengkapi **CLI Setup Configuration Wizard**.
```bash
sudo python3 /opt/safekid/safekid/kid_ui/launcher_server.py --setup
```

### 6.2 — Tambah/Matikan Listing Katalog Apps Launcher (Manual File-tree)
Jika sekiranya ingin memodulasi file lokal aplikasi anak:
```bash
nano ~/SafeKidFlash/safekid/apps/apps_catalog.json
```

---

## FASE 7: Tancap USB Ke Hardware Fisik (Laptop Anak - After Sandbox Tests OK!)

Jika seluruh pengujian modul UI Kiosk, Waktu Time-limits, dan Analytics Chart dari VirtualBox sudah sangat stabil / terintegrasi matang dengan spesifikasi profil kehendak batasan anak, Saatnya membuat OS Live Bootable fisiknya!

**Di Komputer Tuan Rumah (Windows Anda saat ini):**
1. Install / Download **Rufus Portable** gratis melalui web referensi → [rufus.ie](https://rufus.ie/)
2. Pasang USB Flashdisk Kosong yang cukup leluasa (16 GB+)
3. Buka Program Aplikasi **Rufus**:
   - Device: *Isi arah drive USB Target (Hati hati pastikan ini flashdisk yang kosongan, Rufus akan memformat total isinya!).*
   - Boot selection: *Arahkan dan Select menuju ISO Linux Mint XFCE (yang sama seperti Step 1).*
   - **Persistent partition size**: Geser ukuran bar ini secara dramatis menjadi agak luas **minimal 4GB / 6GB**. Data konfigurasi waktu anak akan tertampung permanen disana selama komputer offline tanpa jaringan eksternal.
   - Klik **START**.
4. Shutdown paksa komputer fisik Anda > Hidupkan > Masuk BIOS SETUP (Tekan tombol DEL/F2 berulang-ulang sangat cepat) > Ganti *First HDD Boot Option Priority* menjadi "USB Flashdisk Linux Mint".
5. Kini layaknya Anda menguasai instruksi VirtualBox FASE 4, lakukan Step berurut instalasi (Step **4.2 - 4.6**) saat sedang aktif boot langsung di sistem UEFI fisiknya.
6. Reboot → Mode "Kiosk Chromium SafeKid Flash" akan otomatis merebut total layarnya.
7. Selamat! Kini Komputer Portable yang bebas pengawasan Anda 100% Aman Terkendali secara mutlak untuk lingkungan permainan sehat sang buah hati! ✅🎉 

---

## 📋 Checklist Progress Akhir Anda
Anda bisa cetak, tangkap layar, atau checklist progress dari bawah ini sebagai jurnal Anda:

- [ ] **FASE 1 — TAHAP DOWNLOAD**
  - [ ] Installer VirtualBox Siap.
  - [ ] Linux Mint XFCE ISO terdownload penuh (Verified size ~2.5GB).
- [ ] **FASE 2 — VM CONFIGURATION**
  - [ ] Virtual Machine Storage dialokasi 25GB, Memory RAM 4GB.
  - [ ] Parameter Network diganti NAT, Boot System diarah ke Optical priority.
- [ ] **FASE 3 — SANDBOX RUNTIME (Mint Install)**
  - [ ] Proses OS Virtual instalation via "Erase Disk" Ubuntu/Mint installer.
  - [ ] Akun admin user `root/password` terselesaikan. Boot loader normal.
- [ ] **FASE 4 — MODULAR DEPLOYMENT**
  - [ ] Apt package updates & git repository pull operation `Thbetyfu/SAfe-Kids.git`.
  - [ ] Run Bash Script `setup_linux.sh` lancar tanpa *Dependency Missing Packages*.
  - [ ] Target Edit TUI parameters pada child `safekid.conf`.
- [ ] **FASE 5 — EVALUATE HEALTH-CHECK API**
  - [ ] Systemctl *Background daemon process* melapor `Active` state! ✅
  - [ ] Firefox buka endpoint `/` merespon UI Dash & endpoint `/parent` valid! ✅
  - [ ] Python TDD Test `pytest run_tests.py` = All tests 100% Green ✅
- [ ] **FASE 7 — PRODUCTION (To Hardware Medium)**
  - [ ] Konfigurasi Partisi Flashdisk lewat Rufus (Format MBR/GPT UEFI & Persistence Mode minimum 4GB+).
  - [ ] Deploy Sandbox Step Linux (Phase 4) di dalam environment OS aslinya (Flashdisk Live OS).
  - [ ] BIOS Hardware target dipaksa urutan "Boot first" ke mode USB Flashdisk!
  - [ ] Final Quality Control Selesai 🎉
