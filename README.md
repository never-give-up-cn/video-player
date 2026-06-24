# 暗黑视频流播放器

> 深色暗黑模式视频卡片流播放器，自动扫描 `E:\照片` 目录下的所有视频文件

## 功能特性

- 🎬 **10,000+ 视频自动索引** — 扫描 `E:\照片` 目录下所有 MP4/MOV/MKV 等视频文件
- 🌙 **深色暗黑主题** — 纯深灰黑底色，突出彩色视频封面
- 🎴 **5×5 卡片流** — 每行5个视频缩略图，每页25个卡片，规整排列
- 🔽 **下拉无限加载** — 自动检测滚动位置，加载更多视频
- 🎯 **视频封面黄字标题** — 大号黄色标题叠加在封面上方
- ⏱ **播放时长 + 播放量** — 封面角落显示时长和统计数据
- 🔥 **热门标签** — 部分视频带橙色"X万点赞"标签
- 💬 **弹幕系统** — 实时弹幕发送与显示
- 💭 **评论功能** — 发表和查看评论
- 👍 **点赞 + 关注** — 视频点赞和UP主关注功能
- 🔍 **视频搜索** — 按文件名搜索
- 📁 **设备分类** — 按手机设备筛选

## 技术栈

- **前端**: Vue 3 + Vite + Vue Router
- **后端**: Node.js + Express
- **数据库**: MySQL (可选，评论/弹幕/播放量)
- **缩略图**: ffmpeg

## 快速启动

### 1. 安装依赖

```bash
npm install
```

### 2. 启动

双击 `start.bat`，或运行：

```bash
npm run start
```

### 3. 访问

浏览器打开: **http://localhost:8080**

> 如果 8080 端口被占用，Vite 会自动切换到下一个可用端口（8081/8082...），启动日志中会显示实际地址。

## 单独启动

```bash
# 仅启动后端
npm run server

# 仅启动前端开发服务器
npm run dev
```

## 数据库 (可选)

项目支持 MySQL 数据库存储评论、弹幕、播放量数据。
如果不需要数据库功能，服务器会在无 MySQL 的情况下正常运行，
评论和弹幕数据将存储在内存中（重启后丢失）。

如需使用数据库，请确保 MySQL 运行在 `127.0.0.1:3306`，
用户名 `root`，密码 `123456`，数据库 `video_player` 会自动创建。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/videos | 视频列表（分页） |
| GET | /api/video/:id | 视频详情 |
| GET | /video/:id/stream | 视频流播放 |
| GET | /thumbnails/:id.jpg | 视频封面缩略图 |
| POST | /api/video/:id/play | 记录播放 |
| GET | /api/video/:id/comments | 获取评论 |
| POST | /api/video/:id/comments | 发表评论 |
| GET | /api/video/:id/danmaku | 获取弹幕 |
| POST | /api/video/:id/danmaku | 发送弹幕 |
| POST | /api/video/:id/like | 点赞/取消 |
| POST | /api/video/:id/follow | 关注/取消 |
| GET | /api/health | 服务健康检查 |

## 性能优化

### 缩略图生成

首次启动时，服务器会为所有视频生成缩略图（后台任务，不影响服务响应）：

- **并发控制**: 默认 1 个 ffmpeg 进程并发，避免 CPU 过载
- **生成策略**: 先取视频第 2 秒画面，失败则回退到首帧
- **缓存复用**: 已有缩略图自动跳过，重启不重复生成

服务器启动后会立即开始监听端口，缩略图生成在后台静默进行。

## 项目结构

```
video-player/
├── index.html              # 入口 HTML
├── package.json
├── vite.config.js          # Vite 配置（含 API 代理）
├── start.bat               # Windows 快捷启动脚本
├── src/                    # 前端 Vue 源码
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   ├── views/
│   ├── components/
│   └── api/
├── server/                 # 后端 Express 服务
│   ├── index.js
│   ├── db.js
│   ├── routes/
│   ├── services/
│   │   └── scanner.js      # 视频扫描 + 缩略图生成
│   └── cache/              # 视频缓存 + 缩略图
└── public/
```
