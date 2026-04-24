# Build script for US-DICOMizer (local Windows build)
# Mirrors the steps in .github/workflows/build.yml

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Find-InnoSetupCompiler {
    $candidates = @()
    if (${env:ProgramFiles(x86)}) {
        $candidates += Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
    }
    if ($env:ProgramFiles) {
        $candidates += Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"
    }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $command = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "Inno Setup compiler (ISCC.exe) was not found. Install Inno Setup 6 and rerun build.ps1."
}

Write-Host "==> Installing / updating dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Write-Host "==> Building executable with PyInstaller..." -ForegroundColor Cyan
Stop-Process -Name "US-DICOMizer" -ErrorAction SilentlyContinue
Stop-Process -Name "US-DICOMizer-Updater" -ErrorAction SilentlyContinue

$IconPath = Join-Path $ScriptDir "icon.ico"
$LogoPath = Join-Path $ScriptDir "Logo_Blue_Green_small.png"
$ManualPath = Join-Path $ScriptDir "US-DICOMizer_manual.pdf"
$VersionPath = Join-Path $ScriptDir "VERSION"
$ReleaseDatePath = Join-Path $ScriptDir "RELEASE_DATE"

pyinstaller --noconfirm --onefile --windowed `
    --clean `
    --specpath "build\pyinstaller-specs" `
    --name "US-DICOMizer" `
    --icon="$IconPath" `
    --upx-exclude "*.pyd" `
    --upx-exclude "*.dll" `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    --add-data "$IconPath;." `
    --add-data "$LogoPath;." `
    --add-data "$ManualPath;." `
    --add-data "$VersionPath;." `
    --add-data "$ReleaseDatePath;." `
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

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

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

Write-Host "==> Building updater executable with PyInstaller..." -ForegroundColor Cyan
pyinstaller --noconfirm --onefile --windowed `
    --clean `
    --specpath "build\pyinstaller-specs" `
    --name "US-DICOMizer-Updater" `
    --icon="$IconPath" `
    us_dicomizer_updater.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Updater PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

if (-not (Test-Path "dist\US-DICOMizer-Updater.exe")) {
    Write-Host "Updater executable was not produced." -ForegroundColor Red
    exit 1
}

Write-Host "==> Compiling setup installer..." -ForegroundColor Cyan
$Version = (Get-Content -Path "VERSION" -Raw).Trim()
$Iscc = Find-InnoSetupCompiler
& $Iscc "/DAppVersion=$Version" "installer\US-DICOMizer.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Inno Setup failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$SetupName = "dist\installer\US-DICOMizer-Setup-v$Version.exe"
if (-not (Test-Path $SetupName)) {
    Write-Host "Setup installer was not produced: $SetupName" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "  Executable : dist\US-DICOMizer.exe"
Write-Host "  Updater    : dist\US-DICOMizer-Updater.exe"
Write-Host "  Setup      : $SetupName"
