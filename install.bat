@echo off
set "INSTALL_DIR=%LOCALAPPDATA%\ColorPicker"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Downloading ColorPicker...

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://github.com/bluenotthecolor/ColorPicker/releases/download/v1.0/ColorPicker.exe' -OutFile '%INSTALL_DIR%\ColorPicker.exe'"

echo.
echo ColorPicker installed!
echo Location: %INSTALL_DIR%\ColorPicker.exe
pause