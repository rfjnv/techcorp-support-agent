# Push TechCorp Support Agent to Hugging Face Space
# Usage: .\deploy-to-hf.ps1

$ErrorActionPreference = "Stop"
$hf = "C:\Users\Noutbuk savdosi\.local\bin\hf.exe"
if (-not (Test-Path $hf)) { $hf = "hf" }

Write-Host "`n=== TechCorp → Hugging Face deploy ===`n" -ForegroundColor Cyan
Write-Host "1. Open https://huggingface.co/settings/tokens"
Write-Host "2. Create a token with WRITE access`n"

$token = Read-Host "Paste your Hugging Face token (input is hidden)" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
)

if ([string]::IsNullOrWhiteSpace($plain)) {
    Write-Host "No token entered. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host "`nLogging in..." -ForegroundColor Yellow
& $hf auth login --token $plain --add-to-git-credential

Write-Host "`nPushing to ynchzx/techcorp-support-agent ..." -ForegroundColor Yellow
Set-Location $PSScriptRoot
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone! Space: https://huggingface.co/spaces/ynchzx/techcorp-support-agent" -ForegroundColor Green
    Write-Host "Add secrets (ANTHROPIC_API_KEY, etc.) in Space Settings if you have not already.`n"
} else {
    Write-Host "`nPush failed. Check token permissions and that you own the Space.`n" -ForegroundColor Red
    exit $LASTEXITCODE
}
