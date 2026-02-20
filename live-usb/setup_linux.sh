#!/bin/bash
# =================================================================
# SafeKid Flash - Linux Installer Script
#
# Fungsi:
# 1. Update OS & Install dependencies (Python, Flask, Chromium)
# 2. Setup user 'safekid' (opsional, jika belum ada)
# 3. Copy project files ke /opt/safekid
# 4. Copy config ke /etc/safekid
# 5. Enable systemd service & autostart GUI
#
# Usage:
#   sudo ./setup_linux.sh
# =================================================================

set -e  # Exit on error

# Pastikan running as root
if [ "$EUID" -ne 0 ]; then
  echo "Harap jalankan sebagai root (sudo ./setup_linux.sh)"
  exit
fi

echo "🚀 Memulai Instalasi SafeKid Flash..."

# 1. Install Dependencies
echo "📦 Install paket sistem..."
apt-get update
# Menggunakan python3-flask dan chromium
apt-get install -y python3-pip python3-flask python3-requests chromium-browser x11-xserver-utils unzip chattr

# 2. Setup direktori
echo "📂 Konfigurasi direktori..."
mkdir -p /opt/safekid
mkdir -p /etc/safekid
mkdir -p /var/log/safekid

# 3. Copy files (asumsi script dijalankan dari folder project)
#    Sesuaikan path sumber (source) jika berbeda
SOURCE_DIR="$(dirname "$0")/.."  # Parent folder dari live-usb/
echo "📂 Menyalin file project dari $SOURCE_DIR ke /opt/safekid..."

cp -r "$SOURCE_DIR/safekid" /opt/safekid/
cp "$SOURCE_DIR/config/safekid_default.conf" /etc/safekid/safekid.conf

# 4. Permissions
echo "🔒 Mengatur permissions..."
# Buat user safekid jika belum ada (opsional, skip jika sudah login user biasa)
if ! id "safekid" &>/dev/null; then
    useradd -r -s /bin/false safekid
fi

chown -R safekid:safekid /opt/safekid
chown -R safekid:safekid /var/log/safekid
chmod -R 755 /opt/safekid

# 5. Enable Backend Service
echo "🔌 Mengaktifkan service backend..."
cp "$SOURCE_DIR/live-usb/safekid.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable safekid.service
# systemctl start safekid.service (opsional, start sekarang)

# 6. Setup DNS Filter (opsional, bisa manual nanti)
#    Perlu dijalankan sekali untuk inisialisasi permission
#    python3 /opt/safekid/safekid/content_filter/dns_filter.py --init

# 7. Setup GUI Autostart (untuk user desktop saat ini, misal 'mint' atau 'ubuntu')
#    Cari user non-root yang sedang login (perkiraan)
DESKTOP_USER=$(logname || echo $SUDO_USER)
if [ -z "$DESKTOP_USER" ]; then
    DESKTOP_USER="safekid" # fallback, mungkin salah
fi
echo "🖥️  Mengatur autostart GUI untuk user: $DESKTOP_USER..."

AUTOSTART_DIR="/home/$DESKTOP_USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat <<EOF > "$AUTOSTART_DIR/safekid-kiosk.desktop"
[Desktop Entry]
Type=Application
Name=SafeKid Kiosk
Exec=/opt/safekid/live-usb/kiosk.sh
X-GNOME-Autostart-enabled=true
EOF

chown -R "$DESKTOP_USER:$DESKTOP_USER" "$AUTOSTART_DIR"
# Copy script kiosk juga
mkdir -p /opt/safekid/live-usb
cp "$SOURCE_DIR/live-usb/kiosk.sh" /opt/safekid/live-usb/
chmod +x /opt/safekid/live-usb/kiosk.sh

echo "✅ Instalasi Selesai!"
echo "   - Backend service aktif (cek: systemctl status safekid)"
echo "   - GUI akan mulai otomatis saat login user '$DESKTOP_USER'"
echo "   - Config file ada di /etc/safekid/safekid.conf"
echo "   - Reboot untuk menguji!"
