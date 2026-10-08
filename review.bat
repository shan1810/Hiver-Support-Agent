@echo off
REM Double-click this file to review labels, rate replies, and compute results.
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set LLM_CACHE_ONLY=1
set empty=0

:menu
echo.
echo ============================================
echo   SpotifyCares review tool
echo ============================================
echo   1. Check the labels        (about 45-60 min, 200 tweets)
echo   2. Rate the replies        (about 20-30 min, 51 replies)
echo   3. Calculate the results   (about 1 min)
echo   4. First-time setup        (only if 1-3 show an error)
echo   5. Quit
echo.
set "choice="
set /p "choice=Type a number and press Enter: "
if "%choice%"=="1" goto label
if "%choice%"=="2" goto rate
if "%choice%"=="3" goto results
if "%choice%"=="4" goto setup
if "%choice%"=="5" goto end
if "%choice%"=="" set /a empty+=1
if %empty% GEQ 5 goto end
echo Please type 1, 2, 3, 4 or 5.
goto menu

:label
python -m scripts.label
goto menu

:rate
python -m scripts.rate
goto menu

:results
echo Calculating, please wait...
python -m scripts.05_metrics > results\last_run.txt
if errorlevel 1 (echo Something went wrong. Please send results\last_run.txt to the owner.) else (echo Done. Results saved in results\metrics.md)
goto menu

:setup
python -m pip install -r requirements.txt
goto menu

:end
