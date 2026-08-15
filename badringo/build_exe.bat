@echo off
REM build_exe.bat
REM Compile Badringo for English en un seul fichier .exe (Windows).
REM A executer depuis le dossier du projet, avec l'environnement Python
REM ou les dependances (requirements.txt) sont installees.

pip install -r requirements.txt

pyinstaller --noconfirm --onefile --windowed ^
  --name "BadringoForEnglish" ^
  --add-data "version.json.example;." ^
  main.py

echo.
echo Termine. L'executable se trouve dans le dossier dist\BadringoForEnglish.exe
pause
