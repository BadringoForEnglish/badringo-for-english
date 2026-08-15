@echo off
title Publier une nouvelle version - Badringo for English
cd /d "%~dp0"
python publish_release.py
pause
