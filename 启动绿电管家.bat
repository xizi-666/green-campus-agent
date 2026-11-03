@echo off
chcp 65001 >nul 2>&1
title 绿电管家 - Streamlit 演示
cd /d "%~dp0"
echo ========================================
echo   绿电管家 · 绿色校园节能助手
echo   正在启动 Streamlit...
echo ========================================
echo.
set PYTHON=C:\Users\希杍\Desktop\demo_5\.venv\Scripts\python.exe
if not exist "%PYTHON%" (
    echo [错误] 找不到 Python: %PYTHON%
    echo 请确认 demo_5 目录存在且 venv 已安装
    pause
    exit /b 1
)
"%PYTHON%" -m streamlit run web.py
pause