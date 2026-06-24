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
