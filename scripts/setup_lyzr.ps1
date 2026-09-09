$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
$key = Read-Host "Paste your Lyzr API key"
$lines = Get-Content ".env" | Where-Object { $_ -notmatch '^LYZR_API_KEY=' }
@("LYZR_API_KEY=$key") + $lines | Set-Content ".env"
$env:PYTHONPATH = "$(Get-Location);$(Join-Path (Get-Location) "backend")"
python -m agents.lyzr_bootstrap
Write-Host "`nLyzr setup complete. Run the backend and open /api/lyzr/status."
