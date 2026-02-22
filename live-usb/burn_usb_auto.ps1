<#
.SYNOPSIS
Otomatisasi Instalasi Live USB - SafeKid Flash (Phase 7)

.DESCRIPTION
Script ini mendownload Rufus Portable 4.4 secara otomatis dan membukakan
bantuan visual interaktif untuk memandu pembuatan "Persistent Partition"
(ruang penyimpanan abadi untuk game dan timer The SafeKid).
#>

$ErrorActionPreference = "Stop"

$workspaceDir = "E:\SafeKidFlash\iso_build_tools"
$rufusUrl = "https://github.com/pbatard/rufus/releases/download/v4.4/rufus-4.4p.exe"
$rufusFile = "$workspaceDir\rufus-portable.exe"
$isoFile = "$workspaceDir\linuxmint-21.3-xfce-64bit.iso"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   🔥 SAFEKID FLASH - LIVE USB MASTER BLASTER 🔥" -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Pastikan folder workspace ada
if (-Not (Test-Path $workspaceDir)) {
    Write-Host "Error: Folder $workspaceDir tidak ditemukan. Pastikan Anda sudah menjalankan Phase 1." -ForegroundColor Red
    Pause
    exit
}

# 2. Pastikan ISO Linux Mint ada
if (-Not (Test-Path $isoFile)) {
    Write-Host "Error: File ISO Linux Mint tidak ditemukan di $isoFile." -ForegroundColor Red
    Write-Host "Silahkan jalankan download_and_setup_vbox.ps1 terlebih dahulu." -ForegroundColor Red
    Pause
    exit
} else {
    Write-Host "[OK] ISO Linux Mint ditemukan: $isoFile" -ForegroundColor Green
}

# 3. Mendownload Rufus Portable Jika Belum Ada
if (-Not (Test-Path $rufusFile)) {
    Write-Host "[*] Mendownload Rufus Portable..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $rufusUrl -OutFile $rufusFile
        Write-Host "[OK] Rufus berhasil didownload." -ForegroundColor Green
    } catch {
        Write-Host "[!] Gagal mendownload Rufus: $($_.Exception.Message)" -ForegroundColor Red
        Pause
        exit
    }
} else {
    Write-Host "[OK] Rufus Portable sudah tersedia." -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " 🛑 INSTRUKSI PENTING SEBELUM RUFUS TERBUKA 🛑" -ForegroundColor Red
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "1. Pastikan Anda SUDAH MENCUKUR / MEMASANG Flashdisk kosong ke laptop ini."
Write-Host "2. Saat Rufus terbuka, perhatikan bagian berikut:"
Write-Host "   - Device: (Pilih Flashdisk target Anda - AWAS JANGAN SALAH PISAU!)"
Write-Host "   - Boot selection: Klik [SELECT] dan arahkan ke file ISO ini:"
Write-Host "     => $isoFile" -ForegroundColor Magenta
Write-Host "   - Persistent partition size: GESER SLIDER INI SAMPAI MENTOK (Maksimal)!" -ForegroundColor Yellow
Write-Host "     (Inilah wadah tempat dimana Game Anak & Setelan akan abadi tersimpan)"
Write-Host ""
Write-Host "Jika sudah jelas, tekan tombol (ENTER) untuk Membuka RUFUS sekarang!"
Write-Host "=========================================================" -ForegroundColor Cyan

Pause

Write-Host "[*] Membuka Rufus..." -ForegroundColor Yellow
Start-Process -FilePath $rufusFile -ArgumentList "/iso ""$isoFile""" -Wait

Write-Host ""
Write-Host "✅ Pembuatan Live USB USB Selesai (Jika Anda menekan START di Rufus tadi)." -ForegroundColor Green
Write-Host "Cabut Flashdisk Anda, colok ke laptop/komputer target, lalu Restart!"
Write-Host "Pilih Boot Menu menuju USB Flashdisk Anda, dan Selamat menikmati SafeKid Flash!" -ForegroundColor Cyan
Write-Host ""
Pause
