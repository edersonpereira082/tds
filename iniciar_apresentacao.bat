@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Marquês e Aura - iniciador
set "PORTA=8765"
set "URL=http://localhost:%PORTA%/apresentacao-tds.html"

rem --- procura o Python ---
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY goto :sempython

rem --- liga o servidor local em outra janela (minimizada) ---
start "Servidor da apresentacao (feche para encerrar)" /min cmd /k "%PY% -m http.server %PORTA% --bind 127.0.0.1"
ping -n 4 127.0.0.1 >nul

rem --- procura o Google Chrome ---
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

echo.
echo  Apresentacao: %URL%
echo.
if defined CHROME (
  echo  Abrindo no Google Chrome...
  start "" "%CHROME%" "%URL%"
) else (
  echo  Chrome nao encontrado. Abrindo no navegador padrao...
  start "" "%URL%"
)
echo.
echo  Se a pagina nao abrir sozinha, copie o endereco acima e cole no Chrome.
echo  Para encerrar a apresentacao, feche a janela minimizada "Servidor da apresentacao".
echo.
pause
exit /b

:sempython
echo.
echo  Python nao encontrado. Instale em https://www.python.org/downloads/
echo  (marque a opcao "Add Python to PATH") e rode este arquivo de novo.
echo.
pause
