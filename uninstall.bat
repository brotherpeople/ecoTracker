@echo off
setlocal

echo ===========================================
echo       EcoTracker Windows Uninstaller
echo ===========================================
echo.

echo Terminating running EcoTracker processes...
taskkill /f /im EcoTracker.exe >nul 2>&1

echo Removing registry entry for Startup on Login...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EcoTracker" /f >nul 2>&1

echo Deleting Desktop shortcut...
if exist "%USERPROFILE%\Desktop\EcoTracker.lnk" (
    del /f /q "%USERPROFILE%\Desktop\EcoTracker.lnk" >nul 2>&1
)

echo Deleting installation folder at %APPDATA%\EcoTracker...
if exist "%APPDATA%\EcoTracker" (
    rmdir /s /q "%APPDATA%\EcoTracker" >nul 2>&1
)

echo.
echo EcoTracker has been successfully uninstalled!
pause
