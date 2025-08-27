<#
.SYNOPSIS
  Bind and attach an RTL-SDR USB device to WSL using usbipd-win.

.DESCRIPTION
  This script automates common usbipd tasks: list devices, bind a device by BUSID,
  attach to a WSL distro, or detach a device. It attempts to auto-detect RTL-SDR
  devices (strings containing 'RTL', 'Realtek', or '2832') but accepts an explicit
  -BusId parameter for automation.

.EXAMPLES
  # Auto-detect and attach the first RTL device to default WSL distro
  .\attach_rtlsdr_wsl.ps1 -AutoAttach

  # Attach a specific bus id to a named distro
  .\attach_rtlsdr_wsl.ps1 -BusId 1-4 -Distro Ubuntu-22.04

  # Detach a bus id
  .\attach_rtlsdr_wsl.ps1 -BusId 1-4 -Detach
#>

param (
    [string]$BusId = '',
    [string]$Distro = '',
    [switch]$AutoAttach,
    [switch]$Detach,
    [switch]$List
)

function Require-Usbipd {
    if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
        Write-Error "usbipd not found. Install usbipd-win and run PowerShell as Administrator."
        exit 2
    }
}

function Get-UsbipdList {
    $out = & usbipd list 2>&1
    return $out -join "`n"
}

function Parse-BusIdsForRtl {
    param([string[]]$Lines)
    $matches = @()
    foreach ($line in $Lines) {
        if ($line -match 'RTL|Realtek|2832' -and $line -match '([0-9]+-[0-9]+)') {
            $bid = $Matches[1]
            $matches += [pscustomobject]@{ BusId = $bid; Line = $line }
        }
    }
    return $matches
}

function Choose-BusIdInteractive {
    param([array]$Candidates)
    if ($Candidates.Count -eq 0) { return $null }
    if ($Candidates.Count -eq 1) { return $Candidates[0].BusId }
    Write-Host "Multiple candidate devices found:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $Candidates.Count; $i++) {
        Write-Host "[$i] $($Candidates[$i].BusId) - $($Candidates[$i].Line)"
    }
    $sel = Read-Host "Enter index of device to use"
    if ($sel -as [int] -ge 0 -and $sel -as [int] -lt $Candidates.Count) {
        return $Candidates[$sel].BusId
    }
    return $null
}

function Attach-BusId {
    param([string]$BusId, [string]$Distro)
    if (-not $BusId) { Write-Error "No BusId supplied"; return 1 }
    Write-Host "Binding device $BusId (bind may be no-op if already bound)..."
    & usbipd bind --busid $BusId
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "usbipd bind returned non-zero exit code ($LASTEXITCODE). Continuing to attach may still work."
    }
    if ($Distro) {
        Write-Host "Attaching $BusId to WSL distro '$Distro'..."
        & usbipd attach --wsl $Distro --busid $BusId
    } else {
        Write-Host "Attaching $BusId to default WSL distro..."
        & usbipd attach --wsl --busid $BusId
    }
    if ($LASTEXITCODE -eq 0) { Write-Host "Attach succeeded."; return 0 }
    Write-Error "Attach failed with exit code $LASTEXITCODE"; return $LASTEXITCODE
}

function Detach-BusId {
    param([string]$BusId, [string]$Distro)
    if (-not $BusId) { Write-Error "No BusId supplied"; return 1 }
    if ($Distro) {
        & usbipd detach --wsl $Distro --busid $BusId
    } else {
        & usbipd detach --wsl --busid $BusId
    }
    if ($LASTEXITCODE -eq 0) { Write-Host "Detach succeeded."; return 0 }
    Write-Error "Detach failed with exit code $LASTEXITCODE"; return $LASTEXITCODE
}

# --- Main flow ---
Require-Usbipd

if ($List) {
    Write-Host (Get-UsbipdList)
    exit 0
}

if ($Detach) {
    if (-not $BusId) {
        Write-Error "-Detach requires -BusId <busid>"
        exit 2
    }
    exit (Detach-BusId -BusId $BusId -Distro $Distro)
}

if ($BusId) {
    exit (Attach-BusId -BusId $BusId -Distro $Distro)
}

if ($AutoAttach) {
    $out = Get-UsbipdList
    $lines = $out -split "`n" | Where-Object { $_ -ne '' }
    $cands = Parse-BusIdsForRtl -Lines $lines
    if ($cands.Count -eq 0) {
        Write-Error "No RTL-SDR candidate devices found in usbipd list output. Run 'usbipd list' to inspect devices."
        Write-Host $out
        exit 3
    }
    $bus = Choose-BusIdInteractive -Candidates $cands
    if (-not $bus) { Write-Error "No device selected"; exit 4 }
    exit (Attach-BusId -BusId $bus -Distro $Distro)
}

Write-Host "Usage: attach_rtlsdr_wsl.ps1 [-BusId <busid>] [-Distro <name>] [-AutoAttach] [-Detach] [-List]"
Write-Host "Examples:`n  .\attach_rtlsdr_wsl.ps1 -AutoAttach`n  .\attach_rtlsdr_wsl.ps1 -BusId 1-4 -Distro Ubuntu-22.04"
exit 0
