@echo off
setlocal
set "TARGET_DIR=%APPDATA%\EcoTracker"

echo ===========================================
echo       EcoTracker Windows Installer
echo ===========================================

if not exist "EcoTracker.exe" (
    echo [Error] EcoTracker.exe not found!
    echo Please compile the app first by running PyInstaller or downloading a release.
    pause
    exit /b
)

echo Creating installation directory at %TARGET_DIR%...
mkdir "%TARGET_DIR%" >nul 2>&1
copy /y "EcoTracker.exe" "%TARGET_DIR%\EcoTracker.exe" >nul
if exist "ui\MaterialIcons-Regular.ttf" (
    mkdir "%TARGET_DIR%\ui" >nul 2>&1
    copy /y "ui\MaterialIcons-Regular.ttf" "%TARGET_DIR%\ui\MaterialIcons-Regular.ttf" >nul
)
if exist "tracker\rates.json" (
    mkdir "%TARGET_DIR%\tracker" >nul 2>&1
    copy /y "tracker\rates.json" "%TARGET_DIR%\tracker\rates.json" >nul
)

echo Creating Desktop Shortcut...
set "SCRIPT=%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> "%SCRIPT%"
echo sLinkFile = oWS.ExpandEnvironmentStrings("%%USERPROFILE%%\Desktop\EcoTracker.lnk") >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = oWS.ExpandEnvironmentStrings("%%APPDATA%%\EcoTracker\EcoTracker.exe") >> "%SCRIPT%"
echo oLink.WorkingDirectory = oWS.ExpandEnvironmentStrings("%%APPDATA%%\EcoTracker") >> "%SCRIPT%"
if exist "ui\app.ico" (
    echo oLink.IconLocation = oWS.ExpandEnvironmentStrings("%%APPDATA%%\EcoTracker\ui\app.ico") >> "%SCRIPT%"
    mkdir "%TARGET_DIR%\ui" >nul 2>&1
    copy /y "ui\app.ico" "%TARGET_DIR%\ui\app.ico" >nul
)
echo oLink.Save >> "%SCRIPT%"
cscript /nologo "%SCRIPT%"
del "%SCRIPT%"

echo Adding registry entry for Startup on Login...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "EcoTracker" /t REG_SZ /d "\"%TARGET_DIR%\EcoTracker.exe\"" /f >nul

echo.
echo EcoTracker has been successfully installed!
echo 1. Startup auto-run configured.
echo 2. Desktop shortcut created.
echo.
echo Starting EcoTracker...
start "" "%TARGET_DIR%\EcoTracker.exe"
pause
