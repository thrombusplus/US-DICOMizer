# Build script for US-DICOMizer (local Windows build)
# Mirrors the steps in .github/workflows/build.yml

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==> Installing / updating dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Write-Host "==> Building executable with PyInstaller..." -ForegroundColor Cyan
Stop-Process -Name "US-DICOMizer" -ErrorAction SilentlyContinue

pyinstaller --noconfirm --onefile --windowed `
    --name "US-DICOMizer" `
    --icon=icon.ico `
    --add-data "icon.ico;." `
    --add-data "Logo_Blue_Green_small.png;." `
    --add-data "US-DICOMizer_manual.pdf;." `
    --add-data "VERSION;." `
    --hidden-import pydicom `
    --hidden-import pydicom.pixels `
    --hidden-import pydicom.pixels.utils `
    --hidden-import pydicom.pixels.encoders `
    --hidden-import pydicom.pixels.encoders.gdcm `
    --hidden-import pydicom.pixels.encoders.pylibjpeg `
    --hidden-import pydicom.encaps `
    --hidden-import pydicom.uid `
    --hidden-import pydicom.dataelem `
    --hidden-import tkhtmlview `
    --hidden-import tkhtmlview.html_parser `
    --hidden-import tkhtmlview.utils `
    US-DICOMizer.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "==> Packaging..." -ForegroundColor Cyan
$Version = (Get-Content -Path "VERSION" -Raw).Trim()
$ZipName = "US-DICOMizer-Windows-v$Version.zip"
Compress-Archive -Force -Path "dist\US-DICOMizer.exe" -DestinationPath $ZipName

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "  Executable : dist\US-DICOMizer.exe"
Write-Host "  Archive    : $ZipName"
