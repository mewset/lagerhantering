@echo off
echo Startar om servern...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 >nul
python app.py