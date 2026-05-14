@echo off
echo Building Client EXE...
pip install pyinstaller
pyinstaller --onefile --console --name "ScannerClient" ^
    ..\client\main.py
echo Done. EXE in dist\ScannerClient.exe
pause
