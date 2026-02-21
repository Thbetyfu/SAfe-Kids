<#
.SYNOPSIS
Otomatisasi FASE 2 - Membuat Virtual Machine "SafeKid-Flash" di VirtualBox.

.DESCRIPTION
Script ini menggunakan VBoxManage terintegrasi untuk mendefinisikan & membangun spesifikasi
hardware Virtual Machine secara otomatis sesuai rekomendasi SafeKid (4GB RAM, 2 CPU, 25GB Storage)
sekaligus me-mount ISO Linux Mint.
#>

$ErrorActionPreference = "Stop"

# Lokasi program VBoxManage (CLI bawaan VirtualBox)
$vboxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

If (-Not (Test-Path $vboxManage)) {
    Write-Host "[X] ERROR: VBoxManage.exe tidak ditemukan. Harap pastikan VirtualBox sudah berhasil terinstall di PC Anda!" -ForegroundColor Red
    Exit
}

$vmName = "SafeKid-Flash"
$isoPath = "E:\SafeKidFlash\iso_build_tools\linuxmint-21.3-xfce-64bit.iso"
$ramMB = 4096
$cpus = 2
$vramMB = 128
$diskPath = "$env:USERPROFILE\VirtualBox VMs\$vmName\$vmName.vdi"
$diskSizeMB = 25000  # 25 GB

Write-Host "================= FASE 2 VIRTUALBOX ==================" -ForegroundColor Cyan
Write-Host "[*] Mengecek apakah VM dengan nama '$vmName' sudah ada..."

$vmExists = & $vboxManage list vms | Select-String -Pattern "`"$vmName`""
If ($vmExists) {
    Write-Host "[X] VM '$vmName' sudah ada! Dilarang menimpa. Silahkan hapus manual jika ingin mengulang." -ForegroundColor Yellow
    Exit
}

Write-Host "[+] (1/5) Membuat Virtual Machine baru: $vmName"
& $vboxManage createvm --name $vmName --ostype "Ubuntu_64" --register --basefolder "$env:USERPROFILE\VirtualBox VMs"

Write-Host "[+] (2/5) Mengatur Memori, CPU, Graphics (VMSVGA)..."
& $vboxManage modifyvm $vmName --memory $ramMB --cpus $cpus --vram $vramMB --graphicscontroller vmsvga --mouse usbtablet --boot1 dvd --boot2 disk --boot3 none --boot4 none --nic1 nat

Write-Host "[+] (3/5) Mengalokasi Disk Virtual Storage (25 GB)..."
& $vboxManage createmedium disk --filename $diskPath --size $diskSizeMB --format VDI
& $vboxManage storagectl $vmName --name "SATA Controller" --add sata --controller IntelAhci
& $vboxManage storageattach $vmName --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium $diskPath

Write-Host "[+] (4/5) Menyematkan ISO Linux Mint ke Optical CD/DVD..."
& $vboxManage storagectl $vmName --name "IDE Controller" --add ide
if (Test-Path $isoPath) {
    & $vboxManage storageattach $vmName --storagectl "IDE Controller" --port 1 --device 0 --type dvddrive --medium $isoPath
    Write-Host "    - [Sukses] ISO Termount: $isoPath" -ForegroundColor Green
} else {
    Write-Host "    - [Peringatan] ISO '$isoPath' belum ada, lewati attachment otomatis." -ForegroundColor Red
}

Write-Host "[+] (5/5) Selesai!" -ForegroundColor Green

Write-Host "`n============== VM BERHASIL DIBUAT ==============" -ForegroundColor Green
Write-Host "Buka aplikasi VirtualBox dan Anda sudah bisa menekan tombol 'START' pada VM '$vmName'!"
Write-Host "============================================="
