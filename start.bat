@echo off
chcp 65001 >nul
title 暗黑视频流播放器
echo ====================================
echo    暗黑视频流播放器 - 启动中...
echo ====================================
echo.

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js
    pause
    exit /b
)

echo [信息] 清理残留进程...
taskkill /f /im ffmpeg.exe >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000"') do if %%p gtr 0 taskkill /f /pid %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080"') do if %%p gtr 0 taskkill /f /pid %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8081"') do if %%p gtr 0 taskkill /f /pid %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8082"') do if %%p gtr 0 taskkill /f /pid %%p >nul 2>&1

if not exist "node_modules" (
    echo [信息] 正在安装依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b
    )
)

set PY_CMD=python
where python3 >nul 2>&1
if %errorlevel% equ 0 set PY_CMD=python3
where %PY_CMD% >nul 2>&1
if %errorlevel% equ 0 (
    %PY_CMD% -c "import requests" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [信息] 启动缩略图监控窗口...
        start "" %PY_CMD% thumbnail_monitor.py
    ) else (
        echo [信息] requests未安装,跳过监控
    )
) else (
    echo [信息] Python未安装,跳过监控
)

echo.
echo [信息] 启动后端(3000) 前端(8080)...
echo 浏览器: http://localhost:8080
echo.

call npx concurrently "npm run server" "npm run dev"
pause
