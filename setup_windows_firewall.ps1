<#
.SYNOPSIS
    Configures Windows Defender Firewall rules for StockSense AI LAN Server.
.DESCRIPTION
    Creates or updates an inbound Windows Defender Firewall rule to allow TCP traffic
    on ports 3000 (Next.js Unified Web) and 8000 (FastAPI Backend) exclusively on
    Private (Home/Work) networks. Public network access is strictly disallowed.
#>

[CmdletBinding()]
param (
    [switch]$Remove
)

# Verify Administrator elevation
$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warning "Administrator rights required to configure Windows Firewall."
    Write-Host "Please right-click PowerShell and choose 'Run as Administrator', then run:" -ForegroundColor Yellow
    Write-Host '  & "D:\StockSenseAI\setup_windows_firewall.ps1"' -ForegroundColor Cyan
    Exit 1
}

$RuleName = "StockSense-AI-LAN-Server"

if ($Remove) {
    Write-Host "Removing firewall rule '$RuleName'..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    Write-Host "Rule removed successfully." -ForegroundColor Green
    Exit 0
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "      StockSense AI -- Windows Defender Firewall LAN Setup       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$ruleParams = @{
    DisplayName = $RuleName
    Direction   = "Inbound"
    Action      = "Allow"
    Protocol    = "TCP"
    LocalPort   = @("3005", "8005")
    Profile     = "Private"
    Description = "StockSense AI Native LAN Server - Unified Frontend (3005) and Backend (8005)"
}

$existing = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue

if ($existing) {
    Write-Host "[INFO] Updating existing rule '$RuleName'..." -ForegroundColor Yellow
    Set-NetFirewallRule @ruleParams
} else {
    Write-Host "[INFO] Creating new inbound firewall rule '$RuleName'..." -ForegroundColor Green
    New-NetFirewallRule @ruleParams | Out-Null
}

Write-Host ""
Write-Host "[SUCCESS] Windows Firewall configured successfully!" -ForegroundColor Green
Write-Host "  - Rule Name:  $RuleName"
Write-Host "  - Ports:      TCP 3005, 8005"
Write-Host "  - Profile:    Private (Home/Office Wi-Fi only)"
Write-Host "  - Public:     Blocked (No exposure on public Wi-Fi)"
Write-Host ""
Write-Host "You can now run 'start_stocksense_lan.bat' and connect from other devices on your Wi-Fi." -ForegroundColor Cyan
