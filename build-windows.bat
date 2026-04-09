@echo off
REM Build script for Windows using PyInstaller
REM Run this in a Windows shell (PowerShell or CMD) inside the project folder

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Bundle the app into one executable and include templates/static folders
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py

echo Build finished. The exe will be in dist\
