@echo off
chcp 65001 >nul
title 暗黑视频流播放器
echo ====================================
echo    暗黑视频流播放器 - 启动中...
echo ====================================
echo.

:: Check node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b
)

:: Install deps if needed
if not exist "node_modules" (
    echo [信息] 正在安装依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b
    )
)

:: Check Python and launch monitor window
where python >nul 2>&1
if %errorlevel% equ 0 (
    python -c "import requests" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [信息] 启动缩略图生成监控窗口...
        start "缩略图监控" python thumbnail_monitor.py
    ) else (
        echo [信息] Python requests 库未安装，跳过监控窗口
        echo [信息] 可运行: pip install requests
    )
) else (
    echo [信息] Python 未安装，跳过监控窗口
)

echo.
echo [信息] 启动后端服务器 (端口 3000)...
echo [信息] 启动前端开发服务器 (端口 8080)...
echo.
echo 浏览器打开: http://localhost:8080
echo.
echo 首次启动需要扫描视频文件，请稍候...
echo.

:: Start both server and frontend
call npx concurrently "npm run server" "npm run dev"

pause
