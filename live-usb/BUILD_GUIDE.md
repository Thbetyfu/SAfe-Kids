# 🛠️ Panduan Membuat SafeKid Flash Live USB

SafeKid Flash dirancang untuk dijalankan langsung dari USB drive tanpa mengganggu sistem operasi utama komputer (Windows/Mac). Fitur **Persistence** memungkinkan pengaturan & data anak tersimpan antar sesi.

---

## 📋 Prasyarat

1. **USB Flashdisk** (Minimal 8GB, disarankan 16GB+ USB 3.0).
2. **File ISO Linux** (Rekomendasi: **Linux Mint XFCE** atau **Lubuntu** — ringan & cepat).
3. **Software Pembuat Live USB** (Rekomendasi: **Rufus** di Windows).
4. **Koneksi Internet** (untuk download paket saat proses setup pertama kali).

---

## 🚀 Langkah 1: Membuat Bootable USB dengan Persistence

Menggunakan **Rufus (Windows)**:
1. Download [Rufus](https://rufus.ie/).
2. Pasang Flashdisk.
3. Buka Rufus, pilih Flashdisk target.
4. Klik **Select** dan pilih file ISO Linux Mint/Lubuntu yang sudah didownload.
5. **PENTING**: Geser slider **Persistent partition size** ke maksimal (misal 4GB atau lebih). Ini tempat kita menyimpan SafeKid Flash & data anak.
6. Klik **START**. Tunggu sampai selesai.

---

## 📂 Langkah 2: Menyalin File Project

Setelah USB jadi, salin folder project `SafeKidFlash` ini ke dalam partition *data/persistence* di USB tersebut.
Biasanya partisi Persistence tidak terbaca di Windows secara default.

**Opsi Mudah:**
1. Boot komputer menggunakan USB tersebut (Masuk BIOS/UEFI, pilih boot from USB).
2. Masuk ke desktop Linux (Live Session).
3. Pasang Flashdisk kedua berisi folder project `SafeKidFlash`, ATAU download ulang repository ini dari dalam Linux.

---

## ⚙️ Langkah 3: Instalasi di Lingkungan Linux (Live Session)

Jalankan langkah ini **di dalam desktop Linux Live USB**:

1. Buka Terminal.
2. Masuk ke folder project `SafeKidFlash/live-usb`:
   ```bash
   cd /path/to/SafeKidFlash/live-usb
   ```
3. Beri izin eksekusi pada script setup:
   ```bash
   chmod +x setup_linux.sh kiosk.sh
   # Pastikan backend punya izin execute juga
   chmod +x ../safekid/kid_ui/launcher_server.py
   ```
4. Jalankan Setup Script dengan `sudo` (root):
   ```bash
   sudo ./setup_linux.sh
   ```
   *Script ini akan otomatis menginstall Python, Flask, Chromium, dan mengatur agar SafeKid Flash berjalan otomatis saat booting.*

5. **Restart** komputer (atau logout/login) untuk melihat hasilnya!
   - Browser akan otomatis terbuka full-screen (Kiosk Mode).
   - Backend server berjalan di background.
   - Timer mulai menghitung mundur.

---

## 🔧 Troubleshooting

### Browser Tidak Muncul Otomatis?
Cek autostart entry:
`ls -l ~/.config/autostart/safekid-kiosk.desktop`
Pastikan file ada dan mengarah ke `/opt/safekid/live-usb/kiosk.sh`.

### Backend Server Error?
Cek status service systemd:
`sudo systemctl status safekid.service`
Lihat log error:
`sudo journalctl -u safekid.service -n 50`

### Data Hilang Saat Restart?
Berarti **Persistence** tidak bekerja. Pastikan saat membuat USB dengan Rufus, Anda sudah mengatur "Persistent partition size". Jika menggunakan `dd` atau tools lain yang tidak support persistence, data akan hilang setiap reboot.

---

## 🔒 Tips Keamanan Tambahan

1. **Set Password BIOS/UEFI**: Agar anak tidak bisa mengubah boot order kembali ke hardisk utama tanpa izin.
2. **Kunci Desktop Linux**: Set password user (default biasanya user `mint` atau `ubuntu` tanpa password) agar anak tidak bisa menutup browser kiosk dengan mudah (Alt+F4 atau Super key).

Selamat mencoba! 🚀
