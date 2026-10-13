@echo off
setlocal
cd /d "%~dp0"
python build_demo.py %*
if errorlevel 1 (
  echo.
  echo A build falhou. Consulte a mensagem acima.
  pause
  exit /b 1
)
echo.
echo Demo gerada com sucesso na pasta dist.
pause
