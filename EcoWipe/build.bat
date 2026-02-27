@echo off
echo ========================================================
echo EcoWipe Enterprise - Secure Build Script
echo ========================================================

echo [1/3] Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo [2/3] Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

echo [3/3] Building executable...
:: --uac-admin forces the executable to request Administrator privileges
:: --noconsole hides the command prompt window
:: --onefile packages everything into a single .exe
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --icon=app.ico ^
    --name="EcoWipe_Enterprise" ^
    --clean ^
    main.py

echo ========================================================
echo Build Complete! Executable is located in the 'dist' folder.
echo ========================================================
pause
