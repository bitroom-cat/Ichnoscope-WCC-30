<#
.SYNOPSIS
    Starts a public tunnel forwarding traffic to local Ichnoscope FastAPI (port 8000).
.DESCRIPTION
    Exposes http://localhost:8000 via a secure public HTTPS tunnel so Sentry webhooks
    can deliver production error events to /webhook/sentry.
    Supports ngrok (primary) with automatic fallback to localtunnel.
.PARAMETER Port
    Local port to tunnel (default: 8000).
.PARAMETER Standalone
    If switch is present, keeps the PowerShell window open until Ctrl+C.
.EXAMPLE
    .\scripts\start_tunnel.ps1
    .\scripts\start_tunnel.ps1 -Port 8000 -Standalone
#>

param(
    [int]$Port = 8000,
    [switch]$Standalone = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Magenta
Write-Host "     ICHNOSCOPE - PUBLIC SENTRY WEBHOOK INGESTION TUNNEL         " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Magenta
Write-Host ""

function Get-ActiveNgrokTunnel {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($res.tunnels -and $res.tunnels.Count -gt 0) {
            $httpsTunnel = $res.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
            if ($httpsTunnel) {
                return $httpsTunnel.public_url
            }
            return $res.tunnels[0].public_url
        }
    } catch {
        return $null
    }
    return $null
}

# 1. Check if an ngrok tunnel is already active
$publicUrl = Get-ActiveNgrokTunnel
$tunnelProvider = "ngrok"

if ($publicUrl) {
    Write-Host "[OK] Existing ngrok tunnel detected!" -ForegroundColor Green
} else {
    # 2. Check if ngrok is installed
    $ngrokCmd = Get-Command "ngrok.exe" -ErrorAction SilentlyContinue
    if (-not $ngrokCmd) {
        $ngrokCmd = Get-Command "ngrok" -ErrorAction SilentlyContinue
    }

    $ngrokStarted = $false
    if ($ngrokCmd) {
        Write-Host "[CHECK] Attempting to launch ngrok on port $Port..." -ForegroundColor Yellow
        $tempLog = Join-Path $env:TEMP "ichnoscope_ngrok_$PID.log"
        $ngrokProc = Start-Process -FilePath $ngrokCmd.Source -ArgumentList "http", "$Port", "--log", $tempLog -PassThru -WindowStyle Hidden

        # Poll for public URL from local ngrok API
        $maxAttempts = 10
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            Start-Sleep -Milliseconds 600
            $publicUrl = Get-ActiveNgrokTunnel
            if ($publicUrl) {
                $ngrokStarted = $true
                break
            }
            if ($ngrokProc.HasExited) {
                break
            }
            $attempt++
        }

        if (-not $ngrokStarted) {
            # Inspect ngrok log to diagnose failure reason
            $errContent = ""
            if (Test-Path $tempLog) {
                $errContent = Get-Content $tempLog -Raw -ErrorAction SilentlyContinue
            }
            if ($errContent -match "ERR_NGROK_4018" -or $errContent -match "authentication failed") {
                Write-Host "[NOTICE] ngrok requires an authtoken on this machine (ERR_NGROK_4018)." -ForegroundColor Yellow
                Write-Host "         To authenticate ngrok:" -ForegroundColor White
                Write-Host "         1. Sign up free: https://dashboard.ngrok.com/signup" -ForegroundColor White
                Write-Host "         2. Run: ngrok config add-authtoken <YOUR_TOKEN>" -ForegroundColor White
                Write-Host ""
                Write-Host "[FALLBACK] Automatically starting localtunnel (no account required)..." -ForegroundColor Cyan
            } else {
                Write-Host "[WARN] ngrok did not establish a session. Falling back to localtunnel..." -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "[INFO] ngrok not found in PATH. Starting localtunnel fallback..." -ForegroundColor Cyan
    }

    # 3. Fallback: localtunnel
    if (-not $publicUrl) {
        $tunnelProvider = "localtunnel"
        $ltLog = Join-Path $env:TEMP "ichnoscope_localtunnel_$PID.log"
        $ltProc = Start-Process -FilePath "npx.cmd" -ArgumentList "--yes", "localtunnel", "--port", "$Port" -RedirectStandardOutput $ltLog -PassThru -WindowStyle Hidden

        $maxAttempts = 20
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            Start-Sleep -Milliseconds 600
            if (Test-Path $ltLog) {
                $lines = Get-Content $ltLog -ErrorAction SilentlyContinue
                foreach ($l in $lines) {
                    if ($l -match "your url is:\s*(https?://[^\s]+)") {
                        $publicUrl = $matches[1]
                        break
                    }
                }
            }
            if ($publicUrl) {
                break
            }
            $attempt++
        }
    }
}

if (-not $publicUrl) {
    Write-Host "[FAIL] Could not start public tunnel." -ForegroundColor Red
    Write-Host "You can manually run:" -ForegroundColor Yellow
    Write-Host "  ngrok http $Port" -ForegroundColor White
    Write-Host "  or: npx localtunnel --port $Port" -ForegroundColor White
    exit 1
}

# 4. Print URLs for Sentry Developer Settings
$webhookUrl = "$publicUrl/webhook/sentry"
$aliasUrl = "$publicUrl/api/webhook/sentry"

Write-Host ""
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " [TUNNEL PROVIDER]   -> $tunnelProvider" -ForegroundColor Magenta
Write-Host " [PUBLIC HOST]       -> $publicUrl" -ForegroundColor White
Write-Host " [SENTRY WEBHOOK URL]-> $webhookUrl" -ForegroundColor Green
Write-Host " [WEBHOOK ALIAS URL] -> $aliasUrl" -ForegroundColor Gray
if ($tunnelProvider -eq "ngrok") {
    Write-Host " [NGROK INSPECTOR]   -> http://127.0.0.1:4040" -ForegroundColor Cyan
}
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Sentry Configuration Instructions:" -ForegroundColor Cyan
Write-Host "  1. Open Sentry -> Settings -> Developer Settings -> Create New Integration" -ForegroundColor White
Write-Host "  2. Select 'Internal Integration'" -ForegroundColor White
Write-Host "  3. Paste Webhook URL: $webhookUrl" -ForegroundColor Green
Write-Host "  4. Permissions: Issue & Event -> Read" -ForegroundColor White
Write-Host "  5. Under Webhooks, enable: 'issue' and 'error'" -ForegroundColor White
Write-Host "  6. Copy 'Client Secret' and paste into backend/.env as:" -ForegroundColor White
Write-Host "     SENTRY_CLIENT_SECRET=<your_client_secret>" -ForegroundColor Yellow
Write-Host ""
Write-Host "Verification command:" -ForegroundColor Cyan
Write-Host "  python backend/scripts/test_webhook_ping.py --url $webhookUrl" -ForegroundColor White
Write-Host ""

if ($Standalone) {
    Write-Host "Tunnel is running. Press Ctrl+C to close." -ForegroundColor Yellow
    while ($true) {
        Start-Sleep -Seconds 5
    }
}
