<#
.SYNOPSIS
    Unified development startup script for Ichnoscope.
.DESCRIPTION
    Concurrently boots both the FastAPI backend gateway and the Next.js web dashboard.
    - FastAPI Backend: http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)
    - Next.js Dashboard: http://localhost:3000
    - Ollama LLM Bridge: http://127.0.0.1:11434 (model: qwen3:8b)
.EXAMPLE
    .\run_dev.ps1
    .\run_dev.ps1 -Unified
#>

param(
    [switch]$Unified = $false,
    [switch]$Tunnel = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Magenta
Write-Host "             ICHNOSCOPE - SRE Incident Triage System              " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Magenta
Write-Host ""

# 1. Resolve Python executable
$PythonPath = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = Join-Path $ScriptDir "backend\.venv\Scripts\python.exe"
}
if (-not (Test-Path $PythonPath)) {
    $pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $PythonPath = "python"
    } else {
        Write-Error "[ERROR] Python virtualenv not found in .venv. Please initialize .venv first."
        exit 1
    }
}
Write-Host "[OK] Using Python:" $PythonPath -ForegroundColor Green

# 2. Check Node & npm
$npmCmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    $npmCmd = Get-Command "npm" -ErrorAction SilentlyContinue
}
if (-not $npmCmd) {
    Write-Error "[ERROR] Node.js / npm not found in PATH."
    exit 1
}
Write-Host "[OK] Using npm:" $npmCmd.Source -ForegroundColor Green

# 3. Check Ollama Local LLM
Write-Host "[CHECK] Checking Ollama local LLM service..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    $models = $ollamaCheck.models | ForEach-Object { $_.name }
    Write-Host "[OK] Ollama is active at http://127.0.0.1:11434" -ForegroundColor Green
    if ($models -contains "qwen3:8b" -or ($models | Where-Object { $_ -like "qwen3:8b*" })) {
        Write-Host "      Found target model: qwen3:8b" -ForegroundColor Cyan
    } else {
        Write-Host "      Notice: 'qwen3:8b' not listed in active tags. Run 'ollama run qwen3:8b' if needed." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Ollama service not reachable at http://127.0.0.1:11434. The backend will use configured fallback provider/stub." -ForegroundColor DarkYellow
}

# 4. Check ports
$port8000Used = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000Used) {
    Write-Host "[WARN] Port 8000 is already in use by PID $($port8000Used[0].OwningProcess)." -ForegroundColor Yellow
}

$port3000Used = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000Used) {
    Write-Host "[WARN] Port 3000 is already in use by PID $($port3000Used[0].OwningProcess)." -ForegroundColor Yellow
}

# 5. Launch Backend
$BackendArgs = @("-m", "uvicorn", "ichnoscope.main:app", "--host", "127.0.0.1", "--port", "8000", "--app-dir", "backend", "--reload")
$backendProc = $null

Write-Host ""
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Starting FastAPI Gateway on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "API Interactive Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray

if ($Unified) {
    # Run backend as a background job
    $backendJob = Start-Job -ScriptBlock {
        param($py, $dir, $args)
        Set-Location $dir
        $env:PYTHONPATH = "backend"
        & $py @args
    } -ArgumentList $PythonPath, $ScriptDir, $BackendArgs
    Write-Host "[OK] Backend started as background job (Id: $($backendJob.Id))" -ForegroundColor Green
} else {
    # Run backend in a dedicated console window so reloads and logs are crystal clear
    $backendProc = Start-Process -FilePath $PythonPath -ArgumentList $BackendArgs -WorkingDirectory $ScriptDir -PassThru
    Write-Host "[OK] Backend started in separate window (PID: $($backendProc.Id))" -ForegroundColor Green
}

# Give FastAPI a moment to bind
Start-Sleep -Seconds 2

# 5b. Start ngrok Tunnel if requested
if ($Tunnel) {
    $tunnelScript = Join-Path $ScriptDir "scripts\start_tunnel.ps1"
    if (Test-Path $tunnelScript) {
        & $tunnelScript
    }
}

# 6. Launch Frontend
$WebDir = Join-Path $ScriptDir "web"
Write-Host ""
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Starting Next.js Dashboard on http://localhost:3000 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

try {
    Push-Location $WebDir
    & npm run dev
} finally {
    Pop-Location
    Write-Host ""
    Write-Host "[STOPPING] Shutting down development servers..." -ForegroundColor Yellow

    if ($backendProc -and (-not $backendProc.HasExited)) {
        Write-Host "Stopping FastAPI backend (PID: $($backendProc.Id))..." -ForegroundColor Gray
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($backendJob) {
        Write-Host "Stopping background job (Id: $($backendJob.Id))..." -ForegroundColor Gray
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }

    # Additional cleanup in case uvicorn child process remains
    $leftover = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($leftover) {
        $pids = $leftover | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $pids) {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host "[DONE] All servers stopped." -ForegroundColor Green
}
