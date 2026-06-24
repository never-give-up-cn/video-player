/**
 * Video API Routes
 */
const express = require('express')
const router = express.Router()
const path = require('path')
const fs = require('fs')
const scanner = require('../services/scanner')
const db = require('../db')

const THUMB_DIR = path.join(__dirname, '..', 'cache', 'thumbs')

// GET /api/videos - paginated video list
router.get('/api/videos', (req, res) => {
  const page = parseInt(req.query.page) || 1
  const limit = parseInt(req.query.limit) || 25
  const search = req.query.q || ''
  const result = scanner.getVideos(page, limit, search)

  res.json({
    code: 0,
    data: result,
    msg: 'success'
  })
})

// GET /api/video/:id - single video detail
router.get('/api/video/:id', async (req, res) => {
  const video = scanner.getVideoById(req.params.id)
  if (!video) {
    return res.status(404).json({ code: 1, msg: 'Video not found' })
  }

  const [playCount, likeCount] = await Promise.all([
    db.getPlayCount(req.params.id),
    db.getLikeCount(req.params.id)
  ])

  const duration = video.duration || await scanner.getVideoDuration(video.filePath)
  if (duration) video.duration = duration

  res.json({
    code: 0,
    data: {
      ...video,
      thumbnail: `/thumbnails/${video.id}.jpg`,
      streamUrl: `/video/${video.id}/stream`,
      playCount,
      likeCount
    },
    msg: 'success'
  })
})

// POST /api/video/:id/play - record play
router.post('/api/video/:id/play', async (req, res) => {
  await db.recordPlay(req.params.id)
  res.json({ code: 0, msg: 'ok' })
})

// Video stream with range support
router.get('/video/:id/stream', (req, res) => {
  const video = scanner.getVideoById(req.params.id)
  if (!video) {
    return res.status(404).json({ code: 1, msg: 'Video not found' })
  }

  const filePath = video.filePath
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ code: 1, msg: 'File not found' })
  }

  const stat = fs.statSync(filePath)
  const fileSize = stat.size
  const range = req.headers.range

  if (range) {
    const parts = range.replace(/bytes=/, '').split('-')
    const start = parseInt(parts[0], 10)
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1
    const chunkSize = end - start + 1

    const stream = fs.createReadStream(filePath, { start, end })
    const ext = path.extname(filePath).toLowerCase()
    const mimeTypes = {
      '.mp4': 'video/mp4', '.mkv': 'video/x-matroska', '.avi': 'video/x-msvideo',
      '.mov': 'video/quicktime', '.flv': 'video/x-flv', '.webm': 'video/webm',
      '.wmv': 'video/x-ms-wmv', '.m4v': 'video/mp4', '.mpg': 'video/mpeg',
      '.mpeg': 'video/mpeg', '.3gp': 'video/3gpp', '.ts': 'video/mp2t', '.mts': 'video/mp2t'
    }
    const contentType = mimeTypes[ext] || 'video/mp4'

    res.writeHead(206, {
      'Content-Range': `bytes ${start}-${end}/${fileSize}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': chunkSize,
      'Content-Type': contentType
    })
    stream.pipe(res)
  } else {
    const ext = path.extname(filePath).toLowerCase()
    const mimeTypes = {
      '.mp4': 'video/mp4', '.mkv': 'video/x-matroska', '.avi': 'video/x-msvideo',
      '.mov': 'video/quicktime', '.flv': 'video/x-flv', '.webm': 'video/webm',
      '.wmv': 'video/x-ms-wmv', '.m4v': 'video/mp4', '.mpg': 'video/mpeg',
      '.mpeg': 'video/mpeg', '.3gp': 'video/3gpp', '.ts': 'video/mp2t', '.mts': 'video/mp2t'
    }
    const contentType = mimeTypes[ext] || 'video/mp4'

    res.writeHead(200, {
      'Content-Length': fileSize,
      'Content-Type': contentType
    })
    fs.createReadStream(filePath).pipe(res)
  }
})

// Thumbnail generation and serving
router.get('/thumbnails/:id.jpg', (req, res) => {
  const thumbPath = path.join(THUMB_DIR, `${req.params.id}.jpg`)

  if (fs.existsSync(thumbPath)) {
    return res.sendFile(thumbPath)
  }

  // Generate thumbnail on demand
  scanner.generateThumbnail(req.params.id, (err, genPath) => {
    if (err || !genPath) {
      // Return a placeholder
      const placeholder = path.join(__dirname, '..', 'cache', 'placeholder.jpg')
      if (fs.existsSync(placeholder)) {
        return res.sendFile(placeholder)
      }
      // Create a simple placeholder
      res.status(200).set('Content-Type', 'image/svg+xml').send(
        `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270">
          <rect width="480" height="270" fill="#1a1a1a"/>
          <text x="240" y="135" text-anchor="middle" fill="#555" font-size="18">🎬</text>
        </svg>`
      )
    } else {
      res.sendFile(genPath)
    }
  })
})

// ===== Comments =====
router.get('/api/video/:id/comments', async (req, res) => {
  const page = parseInt(req.query.page) || 1
  const limit = parseInt(req.query.limit) || 20
  const result = await db.getComments(req.params.id, page, limit)
  res.json({ code: 0, data: result, msg: 'success' })
})

router.post('/api/video/:id/comments', async (req, res) => {
  const { content, username } = req.body
  if (!content || !content.trim()) {
    return res.json({ code: 1, msg: '评论内容不能为空' })
  }
  const comment = await db.addComment(req.params.id, username || '匿名用户', content.trim())
  res.json({ code: 0, data: comment, msg: '评论成功' })
})

router.delete('/api/comment/:id', async (req, res) => {
  await db.deleteComment(req.params.id)
  res.json({ code: 0, msg: '已删除' })
})

// ===== Danmaku =====
router.get('/api/video/:id/danmaku', async (req, res) => {
  const list = await db.getDanmaku(req.params.id)
  res.json({ code: 0, data: list, msg: 'success' })
})

router.post('/api/video/:id/danmaku', async (req, res) => {
  const { content, username, time_sec, color, position } = req.body
  if (!content || !content.trim()) {
    return res.json({ code: 1, msg: '弹幕内容不能为空' })
  }
  const dm = await db.addDanmaku(
    req.params.id,
    username || '匿名用户',
    content.trim(),
    parseFloat(time_sec) || 0,
    color || '#ffffff',
    parseInt(position) || 0
  )
  res.json({ code: 0, data: dm, msg: '弹幕已发送' })
})

// ===== Likes =====
router.post('/api/video/:id/like', async (req, res) => {
  const { username } = req.body
  const result = await db.toggleLike(req.params.id, username || '匿名用户')
  res.json({ code: 0, data: result, msg: result.liked ? '已点赞' : '已取消点赞' })
})

// ===== Follows =====
router.post('/api/video/:id/follow', async (req, res) => {
  const { username } = req.body
  // Get video to find up name
  const video = scanner.getVideoById(req.params.id)
  const upName = video ? video.device : '未知UP主'
  const result = await db.toggleFollow(upName, username || '匿名用户')
  res.json({ code: 0, data: result, msg: result.followed ? '已关注' : '已取消关注' })
})

// ===== Scanner control =====
router.post('/api/admin/rescan', (req, res) => {
  const result = scanner.rescan()
  res.json({ code: 0, data: { count: result.length }, msg: 'Scan complete' })
})

router.get('/api/admin/scan-progress', (req, res) => {
  res.json({ code: 0, data: scanner.getScanProgress() })
})

router.post('/api/admin/generate-thumbnails', async (req, res) => {
  const result = await scanner.generateAllThumbnails(4)
  res.json({ code: 0, data: result, msg: 'Thumbnail generation started' })
})

module.exports = router
