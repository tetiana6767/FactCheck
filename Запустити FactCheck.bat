@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto missing_environment

echo Запускаємо україномовний інтерфейс FactCheck...
echo Браузер відкриється автоматично після готовності сервера.
echo.
".venv\Scripts\python.exe" "scripts\run_app.py" %*
set "APP_EXIT_CODE=%ERRORLEVEL%"

if not "%APP_EXIT_CODE%"=="0" (
  echo.
  echo Не вдалося запустити FactCheck. Перевірте повідомлення вище.
  pause
)
exit /b %APP_EXIT_CODE%

:missing_environment
echo Віртуальне середовище ще не створене.
echo Виконайте у командному рядку з каталогу проєкту:
echo.
echo py -3.13 -m venv .venv
echo .venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
echo.
pause
exit /b 1
