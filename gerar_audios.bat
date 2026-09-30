@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando/atualizando componentes de voz (precisa de internet)...
python -m pip install --quiet --disable-pip-version-check edge-tts miniaudio
python gerar_audios.py
echo.
pause
