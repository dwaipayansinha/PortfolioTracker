# Portfolio Tracker - Professional Installer Script (v1.3.0)
# This script installs the application to Program Files and creates shortcuts.

$AppName = "Portfolio Tracker"
$InstallDir = "$env:ProgramFiles\$AppName"
$SourceDir = "$PSScriptRoot\frontend\release\win-unpacked"
$ExecutablePath = "$InstallDir\Portfolio Tracker.exe"

# 1. Check for Admin Privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this installer as Administrator."
    Pause
    Exit
}

Write-Host "Installing $AppName to $InstallDir..." -ForegroundColor Cyan

# 2. Create Install Directory
if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force
}

# 3. Copy Files
Write-Host "Copying application files..." -ForegroundColor Gray
Copy-Item -Path "$SourceDir\*" -Destination $InstallDir -Recurse -Force

# 4. Create Shortcuts
$WshShell = New-Object -ComObject WScript.Shell

# Desktop Shortcut
Write-Host "Creating Desktop shortcut..." -ForegroundColor Gray
$DesktopShortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\$AppName.lnk")
$DesktopShortcut.TargetPath = $ExecutablePath
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.Save()

# Start Menu Shortcut
Write-Host "Creating Start Menu shortcut..." -ForegroundColor Gray
$StartMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\$AppName"
if (!(Test-Path $StartMenuPath)) { New-Item -ItemType Directory -Path $StartMenuPath }
$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuPath\$AppName.lnk")
$StartMenuShortcut.TargetPath = $ExecutablePath
$StartMenuShortcut.WorkingDirectory = $InstallDir
$StartMenuShortcut.Save()

Write-Host "`nInstallation Complete!" -ForegroundColor Green
Write-Host "You can now find '$AppName' on your Desktop and Start Menu."
Write-Host "The backend will automatically start whenever you launch the app."
Pause
