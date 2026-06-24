/**
 * Video Player Backend Server
 * Express + MySQL + ffmpeg
 */
const express = require('express')
const cors = require('cors')
const path = require('path')
const fs = require('fs')

const scanner = require('./services/scanner')
const db = require('./db')
const routes = require('./routes/videos')

const app = express()
const PORT = 3000

// Middleware
app.use(cors())
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// Routes
app.use(routes)

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    code: 0,
    data: {
      status: 'running',
      dbConnected: db.isAvailable(),
      videos: scanner.getVideos(1, 0).total,
      uptime: process.uptime()
    },
    msg: 'ok'
  })
})

// Ensure cache directory exists
const THUMB_DIR = path.join(__dirname, 'cache', 'thumbs')
if (!fs.existsSync(THUMB_DIR)) {
  fs.mkdirSync(THUMB_DIR, { recursive: true })
}

// Start server
async function start() {
  // Initialize database
  await db.initDB()

  // Load video cache
  scanner.loadCache()
  console.log(`[Server] ${scanner.getVideos(1, 0).total} videos indexed`)

  app.listen(PORT, () => {
    console.log(`[Server] Video Player backend running at http://localhost:${PORT}`)
    console.log(`[Server] API: http://localhost:${PORT}/api/videos`)

    // Generate thumbnails in background after server is listening
    const existingThumbs = new Set()
    try {
      fs.readdirSync(THUMB_DIR).forEach(f => existingThumbs.add(f))
    } catch {}
    const missingCount = scanner.getVideos(1, 0).total - existingThumbs.size
    if (missingCount > 0) {
      console.log(`[Server] ${missingCount} thumbnails missing, generating in background...`)
      scanner.generateAllThumbnails(8).then(result => {
        console.log(`[Server] Background thumbnail gen: ${result.generated} ok, ${result.failed} failed`)
      })
    }
  })
}

start().catch(err => {
  console.error('[Server] Fatal error:', err)
  process.exit(1)
})
