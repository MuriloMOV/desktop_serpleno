param(
    [string]$Version = "",
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ProjectRoot
Set-Location -LiteralPath $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "[FALHA] $Message" -ForegroundColor Red
    exit 1
}

$Version = $Version.Trim()
if (-not $Version) {
    $Version = "v1.0.0"
}
if (-not $Version.StartsWith("v")) {
    $Version = "v$Version"
}

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReleaseDir = Join-Path $ProjectRoot "releases\$Version"
$DistDir = Join-Path $ProjectRoot "dist"

if (-not (Test-Path -LiteralPath $DistDir)) {
    Write-Failure "Pasta dist/ nao encontrada. Execute o build antes do release."
}

$Executables = @()
if (Test-Path -LiteralPath (Join-Path -Path $DistDir -ChildPath "SerPleno.exe")) {
    $Executables += Join-Path -Path $DistDir -ChildPath "SerPleno.exe"
}
if (Test-Path -LiteralPath (Join-Path -Path (Join-Path -Path $DistDir -ChildPath "SerPleno") -ChildPath "SerPleno.exe")) {
    $Executables += Join-Path -Path (Join-Path -Path $DistDir -ChildPath "SerPleno") -ChildPath "SerPleno.exe"
}

if ($Executables.Count -eq 0) {
    Write-Failure "Executavel nao encontrado em dist/. Execute o build primeiro."
}

Write-Step "Release iniciada: $Version ($Timestamp)"

if (-not $SkipTests) {
    Write-Step "Executando testes..."
    try {
        pytest tests/ -v --tb=short
        Write-Success "Testes OK"
    } catch {
        Write-Failure "Testes falharam: $_"
    }

    Write-Step "Executando ruff..."
    try {
        ruff check src/ser_pleno tests
        Write-Success "Ruff OK"
    } catch {
        Write-Failure "Ruff falhou: $_"
    }

    Write-Step "Executando mypy..."
    try {
        mypy src/ser_pleno
        Write-Success "Mypy OK"
    } catch {
        Write-Failure "Mypy falhou: $_"
    }
} else {
    Write-Step "Testes, lint e type-check pulados (SkipTests)"
}

Write-Step "Executando build do executavel..."
try {
    python scripts/build_exe.py
    Write-Success "Build OK"
} catch {
    Write-Failure "Build falhou: $_"
}

Write-Step "Criando estrutura de release..."
if (Test-Path -LiteralPath $ReleaseDir) {
    Remove-Item -Recurse -Force -LiteralPath $ReleaseDir
}
New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

Write-Step "Copiando executavel e assets para releases/$Version/..."
$Executables | ForEach-Object {
    $dest = Join-Path -Path $ReleaseDir -ChildPath (Split-Path -Leaf $_)
    Copy-Item -LiteralPath $_ -Destination $dest -Force
    Write-Success "Executavel copiado: $_ -> $dest"
}

if (Test-Path -LiteralPath (Join-Path -Path $DistDir -ChildPath "SerPleno")) {
    $dest = Join-Path -Path $ReleaseDir -ChildPath "SerPleno"
    Copy-Item -LiteralPath (Join-Path -Path $DistDir -ChildPath "SerPleno") -Destination $dest -Recurse -Force
    Write-Success "Pasta SerPleno copiada"
}
if (Test-Path -LiteralPath (Join-Path -Path $DistDir -ChildPath "_internal")) {
    $dest = Join-Path -Path $ReleaseDir -ChildPath "_internal"
    Copy-Item -LiteralPath (Join-Path -Path $DistDir -ChildPath "_internal") -Destination $dest -Recurse -Force
    Write-Success "Pasta _internal copiada"
}

$Assets = @(
    (Join-Path -Path $ProjectRoot -ChildPath "assets"),
    (Join-Path -Path $ProjectRoot -ChildPath "config"),
    (Join-Path -Path $ProjectRoot -ChildPath "sql"),
    (Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "src") -ChildPath (Join-Path -Path "ser_pleno" -ChildPath "assets")),
    (Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "src") -ChildPath (Join-Path -Path "ser_pleno" -ChildPath "sql"))
)
foreach ($asset in $Assets) {
    if (Test-Path -LiteralPath $asset) {
        $rel = $asset.Substring($ProjectRoot.Length + 1)
        $dest = Join-Path $ReleaseDir $rel
        $parentDir = Split-Path -Parent $dest
        if (-not (Test-Path -LiteralPath $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }
        Copy-Item -Recurse -LiteralPath $asset -Destination $dest -Force
        Write-Success "Asset copiado: $asset -> $dest"
    }
}

Write-Step "Release criada em: $ReleaseDir"
Write-Host ""
Write-Host "Conteudo da release:" -ForegroundColor Yellow
Get-ChildItem -Recurse -LiteralPath $ReleaseDir | ForEach-Object {
    Write-Host "  $($_.FullName.Substring($ReleaseDir.Length + 1))"
}
Write-Host ""
Write-Host "Release '$Version' pronta em releases/$Version/" -ForegroundColor Green
