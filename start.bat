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
