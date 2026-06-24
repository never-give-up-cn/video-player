#!/usr/bin/env bash
#
# 暗黑视频流播放器 - Linux / macOS 一键启动脚本
# 用法: chmod +x start.sh && ./start.sh
#
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "    暗黑视频流播放器 - 启动中..."
echo -e "========================================${NC}"
echo ""

# Check Node.js
if ! command -v node &>/dev/null; then
    echo -e "${YELLOW}[错误] 未找到 Node.js，请先安装 Node.js${NC}"
    exit 1
fi

# Install deps if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[信息] 正在安装依赖...${NC}"
    npm install
fi

# Kill old processes (ffmpeg, port 3000, old Vite ports)
echo -e "${YELLOW}[信息] 清理残留进程...${NC}"
pkill -f ffmpeg 2>/dev/null || true
for port in 3000 8080 8081 8082 8083; do
    if command -v lsof &>/dev/null; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    elif command -v fuser &>/dev/null; then
        fuser -k "${port}/tcp" 2>/dev/null || true
    fi
done

# Determine Python command
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

# Launch monitor if Python + requests available
if [ -n "$PYTHON_CMD" ]; then
    if $PYTHON_CMD -c "import requests" 2>/dev/null; then
        echo -e "${GREEN}[信息] 启动缩略图生成监控窗口...${NC}"
        if command -v xdg-open &>/dev/null; then
            # Linux: launch in new terminal window
            if command -v gnome-terminal &>/dev/null; then
                gnome-terminal -- bash -c "$PYTHON_CMD thumbnail_monitor.py; exec bash" &
            elif command -v xterm &>/dev/null; then
                xterm -e "$PYTHON_CMD thumbnail_monitor.py" &
            elif command -v konsole &>/dev/null; then
                konsole --hold -e "$PYTHON_CMD thumbnail_monitor.py" &
            else
                # fallback: run in background
                $PYTHON_CMD thumbnail_monitor.py &
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            osascript -e "tell app \"Terminal\" to do script \"cd $(pwd) && $PYTHON_CMD thumbnail_monitor.py\"" &
        else
            $PYTHON_CMD thumbnail_monitor.py &
        fi
    else
        echo -e "${YELLOW}[信息] Python requests 库未安装，跳过监控窗口${NC}"
        echo -e "${YELLOW}  可运行: pip install requests${NC}"
    fi
else
    echo -e "${YELLOW}[信息] Python 未安装，跳过监控窗口${NC}"
fi

echo ""
echo -e "${GREEN}[信息] 启动后端服务器 (端口 3000)...${NC}"
echo -e "${GREEN}[信息] 启动前端开发服务器 (端口 8080)...${NC}"
echo ""
echo -e "${CYAN}浏览器打开: http://localhost:8080${NC}"
echo ""

# Start both server and frontend
npx concurrently "npm run server" "npm run dev"
