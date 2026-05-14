@echo off
echo Building Admin Panel EXE...
pip install pyinstaller flask
pyinstaller --onefile --windowed --name "ScannerAdmin" ^
    --add-data "admin/templates;admin/templates" ^
    --add-data "admin/static;admin/static" ^
    --hidden-import flask ^
    ..\admin\main.py
echo Done. EXE in dist\ScannerAdmin.exe
pause
