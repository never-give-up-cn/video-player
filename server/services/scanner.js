/**
 * 视频文件扫描器
 * 递归扫描 E:\照片 下所有视频文件，生成视频列表
 * 只读模式 —— 绝不修改源文件夹
 */
const fs = require('fs')
const path = require('path')
const { execSync, exec } = require('child_process')

const VIDEO_DIR = 'E:/照片'
const CACHE_FILE = path.join(__dirname, '..', 'cache', 'video-cache.json')
const THUMB_DIR = path.join(__dirname, '..', 'cache', 'thumbs')
const FFMPEG_PATH = 'C:/Users/CYH/photo-tools/bin/ffmpeg.exe'

// Supported video extensions
const VIDEO_EXTS = new Set([
  '.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm',
  '.wmv', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts'
])

let videoCache = []
let scanProgress = { total: 0, current: 0, status: 'idle' }

// Thumbnail generation progress (for external monitoring)
let thumbnailProgress = {
  status: 'idle',   // 'idle' | 'generating' | 'done'
  total: 0,
  completed: 0,
  failed: 0,
  remaining: 0,
  currentFiles: [],  // files being processed right now
  startTime: null,
  elapsed: 0         // ms since start
}

function getThumbnailProgress() {
  if (thumbnailProgress.status === 'generating' && thumbnailProgress.startTime) {
    thumbnailProgress.elapsed = Date.now() - thumbnailProgress.startTime
  }
  return { ...thumbnailProgress }
}

/**
 * Scan directory recursively for video files
 */
function scanDirectory(dirPath, relativePath = '') {
  let results = []
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true })
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name)
      const relPath = relativePath ? path.join(relativePath, entry.name) : entry.name

      if (entry.isDirectory()) {
        // Skip hidden/system dirs
        if (!entry.name.startsWith('.')) {
          results = results.concat(scanDirectory(fullPath, relPath))
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase()
        if (VIDEO_EXTS.has(ext)) {
          const stat = fs.statSync(fullPath)
          results.push({
            id: Buffer.from(fullPath).toString('base64url'),
            fileName: entry.name,
            filePath: fullPath,
            relativePath: relPath,
            folder: path.dirname(relPath),
            size: stat.size,
            sizeFormatted: formatSize(stat.size),
            mtime: stat.mtimeMs,
            mtimeStr: stat.mtime.toISOString().replace('T', ' ').slice(0, 19),
            device: extractDevice(relPath)
          })
        }
      }
    }
  } catch (err) {
    console.error(`Error scanning ${dirPath}:`, err.message)
  }
  return results
}

function extractDevice(relPath) {
  const parts = relPath.split(path.sep)
  return parts.length > 1 ? parts[1] : 'unknown'
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + 'GB'
}

/**
 * Full rescan
 */
function rescan() {
  console.log('[Scanner] Starting full scan of:', VIDEO_DIR)
  scanProgress = { total: 0, current: 0, status: 'scanning' }
  const start = Date.now()

  if (!fs.existsSync(VIDEO_DIR)) {
    console.error('[Scanner] ERROR: Video directory not found:', VIDEO_DIR)
    scanProgress.status = 'error'
    return []
  }

  videoCache = scanDirectory(VIDEO_DIR)
  scanProgress.total = videoCache.length
  scanProgress.status = 'complete'
  const elapsed = ((Date.now() - start) / 1000).toFixed(1)
  console.log(`[Scanner] Scan complete: ${videoCache.length} videos found in ${elapsed}s`)

  // Cache to file
  try {
    fs.writeFileSync(CACHE_FILE, JSON.stringify(videoCache, null, 2))
  } catch (err) {
    console.error('[Scanner] Cache write error:', err.message)
  }

  return videoCache
}

/**
 * Load cache or rescan
 */
function loadCache() {
  try {
    if (fs.existsSync(CACHE_FILE)) {
      const data = fs.readFileSync(CACHE_FILE, 'utf-8')
      videoCache = JSON.parse(data)
      scanProgress.total = videoCache.length
      scanProgress.status = 'complete'
      console.log(`[Scanner] Loaded ${videoCache.length} videos from cache`)
      return videoCache
    }
  } catch (err) {
    console.error('[Scanner] Cache load error:', err.message)
  }
  return rescan()
}

/**
 * Get paginated videos
 */
function getVideos(page = 1, limit = 25, search = '') {
  let list = videoCache
  if (search) {
    const q = search.toLowerCase()
    list = list.filter(v =>
      v.fileName.toLowerCase().includes(q) ||
      v.relativePath.toLowerCase().includes(q) ||
      v.folder.toLowerCase().includes(q)
    )
  }
  const total = list.length
  const totalPages = Math.ceil(total / limit)
  const start = (page - 1) * limit
  const items = list.slice(start, start + limit).map(v => ({
    ...v,
    thumbnail: `/thumbnails/${v.id}.jpg`,
    streamUrl: `/video/${v.id}/stream`
  }))

  return { items, total, page, limit, totalPages }
}

/**
 * Get single video by ID
 */
function getVideoById(id) {
  return videoCache.find(v => v.id === id) || null
}

/**
 * Generate thumbnail using ffmpeg (async)
 */
function generateThumbnail(videoId, callback) {
  const video = videoCache.find(v => v.id === videoId)
  if (!video) {
    if (callback) callback(new Error('Video not found'))
    return
  }

  const thumbPath = path.join(THUMB_DIR, `${videoId}.jpg`)

  // Check if already exists
  if (fs.existsSync(thumbPath)) {
    if (callback) callback(null, thumbPath)
    return
  }

  // Generate thumbnail at 25% mark
  const cmd = `"${FFMPEG_PATH}" -ss 00:00:02 -i "${video.filePath}" -vframes 1 -vf "scale=480:-1" -q:v 5 "${thumbPath}" -y 2>nul`
  exec(cmd, { timeout: 30000 }, (err) => {
    if (err) {
      // fallback: try first frame
      const cmd2 = `"${FFMPEG_PATH}" -i "${video.filePath}" -vframes 1 -vf "scale=480:-1" -q:v 5 "${thumbPath}" -y 2>nul`
      exec(cmd2, { timeout: 30000 }, (err2) => {
        if (callback) callback(err2, err2 ? null : thumbPath)
      })
    } else {
      if (callback) callback(null, thumbPath)
    }
  })
}

/**
 * Get video duration using ffprobe
 */
function getVideoDuration(filePath) {
  return new Promise((resolve) => {
    const ffprobe = FFMPEG_PATH.replace('ffmpeg.exe', 'ffprobe.exe')
    exec(`"${ffprobe}" -v error -show_entries format=duration -of csv=p=0 "${filePath}" 2>nul`,
      { timeout: 10000 },
      (err, stdout) => {
        if (err || !stdout) resolve(null)
        const secs = parseFloat(stdout.trim())
        if (isNaN(secs)) resolve(null)
        else resolve(formatDuration(secs))
      }
    )
  })
}

function formatDuration(secs) {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * Batch generate missing thumbnails
 */
function generateAllThumbnails(concurrency = 4) {
  let idx = 0
  let active = 0
  let generated = 0
  let failed = 0

  return new Promise((resolve) => {
    if (!videoCache.length) {
      thumbnailProgress = { status: 'done', total: 0, completed: 0, failed: 0, remaining: 0, currentFiles: [], startTime: null, elapsed: 0 }
      resolve({ generated: 0, failed: 0 })
      return
    }

    // Ensure thumb dir
    if (!fs.existsSync(THUMB_DIR)) {
      fs.mkdirSync(THUMB_DIR, { recursive: true })
    }

    const existing = new Set()
    try {
      fs.readdirSync(THUMB_DIR).forEach(f => existing.add(f))
    } catch {}

    const pending = videoCache.filter(v => !existing.has(`${v.id}.jpg`))
    if (!pending.length) {
      console.log('[Scanner] All thumbnails already generated')
      thumbnailProgress = { status: 'done', total: 0, completed: 0, failed: 0, remaining: 0, currentFiles: [], startTime: null, elapsed: 0 }
      resolve({ generated: 0, failed: 0 })
      return
    }

    // Init progress tracking
    thumbnailProgress.status = 'generating'
    thumbnailProgress.total = pending.length
    thumbnailProgress.completed = 0
    thumbnailProgress.failed = 0
    thumbnailProgress.remaining = pending.length
    thumbnailProgress.currentFiles = []
    thumbnailProgress.startTime = Date.now()
    thumbnailProgress.elapsed = 0

    console.log(`[Scanner] Generating ${pending.length} missing thumbnails (concurrency: ${concurrency})`)

    function next() {
      if (idx >= pending.length) return
      const video = pending[idx++]
      active++

      // Track active file
      const fileLabel = video.relativePath || video.fileName
      thumbnailProgress.currentFiles.push(fileLabel)

      const thumbPath = path.join(THUMB_DIR, `${video.id}.jpg`)
      const cmd = `"${FFMPEG_PATH}" -ss 00:00:02 -i "${video.filePath}" -vframes 1 -vf "scale=480:-1" -q:v 5 "${thumbPath}" -y 2>nul`
      exec(cmd, { timeout: 30000 }, (err) => {
        active--

        // Remove from active files
        const fi = thumbnailProgress.currentFiles.indexOf(fileLabel)
        if (fi !== -1) thumbnailProgress.currentFiles.splice(fi, 1)

        if (err) {
          // try first frame
          const cmd2 = `"${FFMPEG_PATH}" -i "${video.filePath}" -vframes 1 -vf "scale=480:-1" -q:v 5 "${thumbPath}" -y 2>nul`
          exec(cmd2, { timeout: 30000 }, (err2) => {
            if (err2) {
              failed++
              thumbnailProgress.failed = failed
            } else {
              generated++
              thumbnailProgress.completed = generated
            }
            thumbnailProgress.remaining = pending.length - (generated + failed)
            if (generated + failed >= pending.length) {
              thumbnailProgress.status = 'done'
              thumbnailProgress.elapsed = Date.now() - thumbnailProgress.startTime
              console.log(`[Scanner] Thumbnails done: ${generated} generated, ${failed} failed`)
              resolve({ generated, failed })
            } else {
              next()
            }
          })
        } else {
          generated++
          thumbnailProgress.completed = generated
          thumbnailProgress.remaining = pending.length - (generated + failed)
          if (generated + failed >= pending.length) {
            thumbnailProgress.status = 'done'
            thumbnailProgress.elapsed = Date.now() - thumbnailProgress.startTime
            console.log(`[Scanner] Thumbnails done: ${generated} generated, ${failed} failed`)
            resolve({ generated, failed })
          } else {
            next()
          }
        }
      })
    }

    // Start N concurrent workers
    for (let i = 0; i < Math.min(concurrency, pending.length); i++) {
      next()
    }
  })
}

module.exports = {
  rescan,
  loadCache,
  getVideos,
  getVideoById,
  generateThumbnail,
  getVideoDuration,
  generateAllThumbnails,
  getScanProgress: () => scanProgress,
  getThumbnailProgress,
  VIDEO_DIR
}
