# Yeni bilgisayarda tek komutla kurulum: .\kurulum.ps1
# Gereksinimler yoksa winget ile kurar, Python ortamini ve yuz modelini hazirlar.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Yenile-Yol {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Gerekli($komut, $paket) {
    if (Get-Command $komut -ErrorAction SilentlyContinue) { Write-Host "[tamam] $komut"; return }
    Write-Host "[kuruluyor] $paket"
    winget install --id $paket -e --accept-source-agreements --accept-package-agreements
    Yenile-Yol
    if (-not (Get-Command $komut -ErrorAction SilentlyContinue)) {
        throw "$komut kuruldu ama bulunamadi. PowerShell penceresini kapatip acin ve tekrar calistirin."
    }
}

Gerekli 'uv' 'astral-sh.uv'
Gerekli 'ffmpeg' 'Gyan.FFmpeg'

Write-Host '[kuruluyor] Python ortami (ilk seferde birkac GB iner)'
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw 'uv sync basarisiz.' }

$model = 'modeller\yunet\face_detection_yunet_2023mar.onnx'
if (-not (Test-Path $model)) {
    Write-Host '[indiriliyor] yuz modeli'
    New-Item -ItemType Directory -Force (Split-Path $model) | Out-Null
    curl.exe -fsSL -o $model 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx'
    if ($LASTEXITCODE -ne 0) { throw 'Yuz modeli indirilemedi.' }
}
if ((Get-Item $model).Length -lt 100000) { throw 'Yuz modeli eksik indi, dosyayi silip tekrar calistirin.' }

Write-Host '[kontrol] GPU ve video kodlayici'
.\.venv\Scripts\python.exe -c "import torch; ok=torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0) if ok else 'YOK'); raise SystemExit(0 if ok else 1)"
if ($LASTEXITCODE -ne 0) { throw 'NVIDIA GPU bulunamadi; surucuyu kontrol edin.' }
ffmpeg -v error -f lavfi -i color=c=black:s=320x240:d=0.2 -c:v h264_nvenc -f null -
if ($LASTEXITCODE -ne 0) { throw 'NVENC calismiyor; NVIDIA surucusunu guncelleyin.' }

Write-Host ''
Write-Host 'Kurulum tamam. Claude Code ile bu klasorde acin ve /bolum-isle komutunu kullanin.'
Write-Host 'Whisper modeli (yaklasik 3 GB) ilk dokumde otomatik iner.'
