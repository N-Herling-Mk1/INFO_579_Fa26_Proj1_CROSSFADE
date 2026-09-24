<#
  boot_site.ps1 - serve the CROSSFADE docs site locally.
  Scans loopback ports 8000-8020 for the first free one, starts python's
  http.server from the repo root, opens the browser, and shows the live
  request log. Ctrl+C stops the server.

  Usage:  .\boot_site.ps1            (auto port, opens browser)
          .\boot_site.ps1 -Port 8010
          .\boot_site.ps1 -NoOpen
#>
param([int]$Port = 0, [switch]$NoOpen)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "[1/3] checking python" -ForegroundColor Cyan
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { Write-Host "      python not found on PATH" -ForegroundColor Red; exit 1 }

Write-Host "[2/3] finding a free port" -ForegroundColor Cyan
function Test-Free([int]$p) {
  try { $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $p); $l.Start(); $l.Stop(); $true } catch { $false }
}
if ($Port -eq 0) {
  foreach ($p in 8000..8020) { if (Test-Free $p) { $Port = $p; break } }
  if ($Port -eq 0) { Write-Host "      no free port in 8000-8020" -ForegroundColor Red; exit 1 }
} elseif (-not (Test-Free $Port)) { Write-Host "      port $Port is in use" -ForegroundColor Red; exit 1 }
$url = "http://127.0.0.1:$Port/"
Write-Host "      serving $url" -ForegroundColor Green

Write-Host "[3/3] starting server (Ctrl+C to stop)" -ForegroundColor Cyan
if (-not $NoOpen) { Start-Process $url }
try { & $py.Source -m http.server $Port --bind 127.0.0.1 }
finally { Write-Host "server stopped" -ForegroundColor Yellow }
