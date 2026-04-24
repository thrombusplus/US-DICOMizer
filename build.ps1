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
    --clean `
    --name "US-DICOMizer" `
    --icon=icon.ico `
    --upx-exclude "*.pyd" `
    --upx-exclude "*.dll" `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    --add-data "icon.ico;." `
    --add-data "Logo_Blue_Green_small.png;." `
    --add-data "US-DICOMizer_manual.pdf;." `
    --add-data "VERSION;." `
    --add-data "RELEASE_DATE;." `
    --hidden-import pydicom `
    --hidden-import pydicom.pixels `
    --hidden-import pydicom.pixels.utils `
    --hidden-import pydicom.pixels.decoders `
    --hidden-import pydicom.pixels.decoders.gdcm `
    --hidden-import pydicom.pixels.decoders.pillow `
    --hidden-import pydicom.pixels.decoders.pylibjpeg `
    --hidden-import pydicom.pixels.encoders `
    --hidden-import pydicom.pixels.encoders.gdcm `
    --hidden-import pydicom.pixels.encoders.pylibjpeg `
    --hidden-import pydicom.encaps `
    --hidden-import pydicom.uid `
    --hidden-import pydicom.dataelem `
    --hidden-import pylibjpeg `
    --hidden-import pylibjpeg.utils `
    --hidden-import libjpeg `
    --hidden-import tkhtmlview `
    --hidden-import tkhtmlview.html_parser `
    --hidden-import tkhtmlview.utils `
    US-DICOMizer.py

Write-Host "==> Verifying bundled payload and size..." -ForegroundColor Cyan
$Exe = Get-Item "dist\US-DICOMizer.exe"
$ExeSizeMb = [Math]::Round($Exe.Length / 1MB, 2)
Write-Host "EXE size: $ExeSizeMb MB"

$ArchiveList = Join-Path $ScriptDir "build\archive-list.txt"
pyi-archive_viewer "dist\US-DICOMizer.exe" -l | Out-File -Encoding utf8 $ArchiveList

$RequiredEntryPatterns = @(
    "_libjpeg\.cp310-win_amd64\.pyd",
    "pylibjpeg_libjpeg-[^\\]+\.dist-info\\\\entry_points\.txt",
    "cv2\\\\cv2\.pyd",
    "numpy\\\\(?:_core|core)\\\\_multiarray_umath\.cp310-win_amd64\.pyd",
    "matplotlib\\\\_path\.cp310-win_amd64\.pyd",
    "charset_normalizer\\\\md__mypyc\.cp310-win_amd64\.pyd"
)

foreach ($Pattern in $RequiredEntryPatterns) {
    if (-not (Select-String -Path $ArchiveList -Pattern $Pattern -Quiet)) {
        Write-Host "Missing required bundled dependency matching: $Pattern" -ForegroundColor Red
        exit 1
    }
}

if (Select-String -Path $ArchiveList -Pattern "torch\\|torchvision\\|torchaudio\\" -Quiet) {
    Write-Host "Unexpected torch-family modules found in bundled payload." -ForegroundColor Red
    exit 1
}

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
