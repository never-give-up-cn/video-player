/**
 * MySQL 数据库模块
 * 存储评论、弹幕、播放量、点赞、关注等数据
 * 连接: 127.0.0.1:3306, root/123456
 */
const mysql = require('mysql2/promise')

const DB_CONFIG = {
  host: '127.0.0.1',
  port: 3306,
  user: 'root',
  password: '123456',
  database: 'video_player',
  waitForConnections: true,
  connectionLimit: 10,
  charset: 'utf8mb4'
}

let pool = null
let dbAvailable = false

/**
 * Initialize database connection and create tables
 */
async function initDB() {
  try {
    // First connect without database to create it if needed
    const tempConn = await mysql.createConnection({
      host: DB_CONFIG.host,
      port: DB_CONFIG.port,
      user: DB_CONFIG.user,
      password: DB_CONFIG.password
    })
    await tempConn.execute(
      `CREATE DATABASE IF NOT EXISTS \`${DB_CONFIG.database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
    )
    await tempConn.end()

    // Now connect to the database
    pool = mysql.createPool(DB_CONFIG)

    // Create tables
    await pool.execute(`
      CREATE TABLE IF NOT EXISTS comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(512) NOT NULL,
        username VARCHAR(100) NOT NULL DEFAULT '匿名用户',
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_video_id (video_id(255)),
        INDEX idx_created_at (created_at)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `)

    await pool.execute(`
      CREATE TABLE IF NOT EXISTS danmaku (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(512) NOT NULL,
        username VARCHAR(100) NOT NULL DEFAULT '匿名用户',
        content VARCHAR(500) NOT NULL,
        time_sec FLOAT NOT NULL DEFAULT 0,
        color VARCHAR(7) DEFAULT '#ffffff',
        position INT DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_video_id (video_id(255)),
        INDEX idx_time_sec (time_sec)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `)

    await pool.execute(`
      CREATE TABLE IF NOT EXISTS play_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(512) NOT NULL,
        play_count INT DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_video_id (video_id(255))
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `)

    await pool.execute(`
      CREATE TABLE IF NOT EXISTS likes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(512) NOT NULL,
        username VARCHAR(100) NOT NULL DEFAULT '匿名用户',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_video_user (video_id(255), username)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `)

    await pool.execute(`
      CREATE TABLE IF NOT EXISTS follows (
        id INT AUTO_INCREMENT PRIMARY KEY,
        up_name VARCHAR(255) NOT NULL,
        username VARCHAR(100) NOT NULL DEFAULT '匿名用户',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_up_user (up_name, username)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `)

    dbAvailable = true
    console.log('[DB] MySQL connected and tables ready')
    return true
  } catch (err) {
    console.warn('[DB] MySQL unavailable (video_player will work without DB):', err.message)
    dbAvailable = false
    return false
  }
}

function isAvailable() {
  return dbAvailable && pool !== null
}

// ===== Comments =====
async function getComments(videoId, page = 1, limit = 20) {
  if (!isAvailable()) return { items: [], total: 0 }
  const offset = (page - 1) * limit
  const [rows] = await pool.execute(
    'SELECT * FROM comments WHERE video_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    [videoId, limit, offset]
  )
  const [[{ count }]] = await pool.execute(
    'SELECT COUNT(*) as count FROM comments WHERE video_id = ?',
    [videoId]
  )
  return { items: rows, total: count }
}

async function addComment(videoId, username, content) {
  if (!isAvailable()) {
    return { id: Date.now(), videoId, username, content, created_at: new Date().toISOString().slice(0, 19).replace('T', ' ') }
  }
  const [result] = await pool.execute(
    'INSERT INTO comments (video_id, username, content) VALUES (?, ?, ?)',
    [videoId, username, content]
  )
  return { id: result.insertId, videoId, username, content, created_at: new Date().toISOString().slice(0, 19).replace('T', ' ') }
}

async function deleteComment(commentId) {
  if (!isAvailable()) return false
  await pool.execute('DELETE FROM comments WHERE id = ?', [commentId])
  return true
}

// ===== Danmaku =====
async function getDanmaku(videoId) {
  if (!isAvailable()) return []
  const [rows] = await pool.execute(
    'SELECT content, time_sec, color, position FROM danmaku WHERE video_id = ? ORDER BY time_sec ASC',
    [videoId]
  )
  return rows
}

async function addDanmaku(videoId, username, content, timeSec, color = '#ffffff', position = 0) {
  if (!isAvailable()) return null
  const [result] = await pool.execute(
    'INSERT INTO danmaku (video_id, username, content, time_sec, color, position) VALUES (?, ?, ?, ?, ?, ?)',
    [videoId, username, content, timeSec, color, position]
  )
  return { id: result.insertId, content, time_sec: timeSec, color, position }
}

// ===== Play Count =====
async function recordPlay(videoId) {
  if (!isAvailable()) return
  try {
    await pool.execute('INSERT INTO play_history (video_id) VALUES (?)', [videoId])
  } catch {}
}

async function getPlayCount(videoId) {
  if (!isAvailable()) return 0
  const [[{ count }]] = await pool.execute(
    'SELECT COUNT(*) as count FROM play_history WHERE video_id = ?',
    [videoId]
  )
  return count
}

// ===== Likes =====
async function toggleLike(videoId, username) {
  if (!isAvailable()) return { liked: false, count: 0 }
  try {
    await pool.execute(
      'INSERT INTO likes (video_id, username) VALUES (?, ?)',
      [videoId, username]
    )
    const [[{ count }]] = await pool.execute(
      'SELECT COUNT(*) as count FROM likes WHERE video_id = ?',
      [videoId]
    )
    return { liked: true, count }
  } catch {
    // Already liked -> unlike
    await pool.execute(
      'DELETE FROM likes WHERE video_id = ? AND username = ?',
      [videoId, username]
    )
    const [[{ count }]] = await pool.execute(
      'SELECT COUNT(*) as count FROM likes WHERE video_id = ?',
      [videoId]
    )
    return { liked: false, count }
  }
}

async function getLikeCount(videoId) {
  if (!isAvailable()) return 0
  const [[{ count }]] = await pool.execute(
    'SELECT COUNT(*) as count FROM likes WHERE video_id = ?',
    [videoId]
  )
  return count
}

// ===== Follows =====
async function toggleFollow(upName, username) {
  if (!isAvailable()) return { followed: false }
  try {
    await pool.execute(
      'INSERT INTO follows (up_name, username) VALUES (?, ?)',
      [upName, username]
    )
    return { followed: true }
  } catch {
    await pool.execute(
      'DELETE FROM follows WHERE up_name = ? AND username = ?',
      [upName, username]
    )
    return { followed: false }
  }
}

async function isFollowing(upName, username) {
  if (!isAvailable()) return false
  const [rows] = await pool.execute(
    'SELECT id FROM follows WHERE up_name = ? AND username = ?',
    [upName, username]
  )
  return rows.length > 0
}

module.exports = {
  initDB,
  isAvailable: () => dbAvailable,
  getComments,
  addComment,
  deleteComment,
  getDanmaku,
  addDanmaku,
  recordPlay,
  getPlayCount,
  toggleLike,
  getLikeCount,
  toggleFollow,
  isFollowing
}
