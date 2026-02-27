@echo off
echo Building EcoWipe Executable...
echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo Running PyInstaller...
venv\Scripts\pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --icon "app.ico" ^
    --name "EcoWipe" ^
    --uac-admin ^
    --hidden-import "qrcode" ^
    --clean ^
    main.py

echo Build Complete. Checking dist/ folder.
