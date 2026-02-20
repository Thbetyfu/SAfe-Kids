#!/bin/bash
# =================================================================
# SafeKid Flash - Kiosk Launcher Script
#
# Fungsi:
# 1. Nonaktifkan screen blanking (DPMS) agar layar tidak mati
# 2. Hapus file "Preference" Chromium agar tidak muncul "Restore pages?"
# 3. Jalankan Chromium browser dalam mode KIOSK (fullscreen, no UI)
#    diarahkan ke http://localhost:5556
# =================================================================

# 1. Nonaktifkan Screen Saver / Blanking
xset s noblank
xset s off
xset -dpms

# 2. Hapus error "Restore pages?" Chromium
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences

# 3. Jalankan Chromium Kiosk Mode
# --kiosk               : Fullscreen, no window controls
# --noerrdialogs        : Suppress error dialogs
# --disable-infobars    : No "Chrome is being controlled..."
# --check-for-update-interval=31536000 : Disable auto-update check
# http://localhost:5556 : URL target (SafeKid Backend)

/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 "http://localhost:5556" &
