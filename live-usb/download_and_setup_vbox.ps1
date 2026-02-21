<#
.SYNOPSIS
Otomatisasi FASE 1 - Mengunduh dan Menginstal VirtualBox & Mengunduh ISO Linux Mint XFCE

.DESCRIPTION
Script ini mendownload installer VirtualBox terbaru lalu menginstalnya secara diam-diam (silent install)
Sekaligus mengunduh ISO Linux Mint XFCE versi terbaru untuk Testing VM SafeKid Flash.
#>

$ErrorActionPreference = "Stop"

$workspaceDir = "E:\SafeKidFlash\iso_build_tools"
if (-Not (Test-Path $workspaceDir)) {
    New-Item -ItemType Directory -Force -Path $workspaceDir | Out-Null
    Write-Host "[+] Folder $workspaceDir dibuat." -ForegroundColor Green
}

# --- 1. DOWNLOAD VIRTUALBOX ---
$vboxUrl = "https://download.virtualbox.org/virtualbox/7.0.14/VirtualBox-7.0.14-161095-Win.exe"
$vboxInstaller = "$workspaceDir\VirtualBox_Installer.exe"

if (-Not (Test-Path $vboxInstaller)) {
    Write-Host "[*] Mendownload VirtualBox Installer (~106 MB)..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $vboxUrl -OutFile $vboxInstaller
    Write-Host "[+] VirtualBox berhasil diunduh." -ForegroundColor Green
} else {
    Write-Host "[-] VirtualBox sudah ada, melewabti proses download." -ForegroundColor Yellow
}

# --- 2. SILENT INSTALL VIRTUALBOX ---
Write-Host "[*] Memulai instalasi otomatis VirtualBox..." -ForegroundColor Cyan
# --silent agar tidak memunculkan popup instalasi Wizard, lalu --ignore-reboot
$process = Start-Process -FilePath $vboxInstaller -ArgumentList "--silent --ignore-reboot" -Wait -PassThru
if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
    Write-Host "[+] VirtualBox berhasil diinstall sistem." -ForegroundColor Green
} else {
    Write-Host "[X] Peringatan: Instalasi VBox berhenti dengan kode $($process.ExitCode)" -ForegroundColor Red
}

# --- 3. DOWNLOAD LINUX MINT XFCE ISO ---
# Menggunakan Mirror kernel.org yang lebih stabil
$isoUrl = "https://mirrors.edge.kernel.org/linuxmint/stable/21.3/linuxmint-21.3-xfce-64bit.iso"
$isoFile = "$workspaceDir\linuxmint-21.3-xfce-64bit.iso"

if (-Not (Test-Path $isoFile)) {
    Write-Host "[*] Mendownload ISO Linux Mint XFCE (~2.9 GB) - Bisa memakan waktu lama tergantung internet Anda..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $isoUrl -OutFile $isoFile
    Write-Host "[+] ISO Linux Mint XFCE berhasil diunduh!" -ForegroundColor Green
} else {
    Write-Host "[-] ISO file sudah ada." -ForegroundColor Yellow
}

Write-Host "`n============== FASE 1 SELESAI ==============" -ForegroundColor Green
Write-Host "VirtualBox Telah terinstall."
Write-Host "ISO tersimpan di: $isoFile"
Write-Host "============================================="
