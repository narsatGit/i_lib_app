@echo off
:: Arrête tous les processus Python en cours
taskkill /f /im pythonw.exe > nul 2>&1
echo Application fermée.
timeout /t 2 /nobreak > nul