<template>
  <div class="player-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-spinner" style="min-height: 60vh;" />

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>视频未找到</p>
      <router-link to="/" class="back-link">← 返回首页</router-link>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Video Player Section -->
      <div class="player-section">
        <div class="player-container" ref="playerContainer">
          <div class="danmaku-canvas" ref="danmakuCanvas">
            <!-- Danmaku items rendered as absolutely positioned spans -->
            <span
              v-for="dm in activeDanmaku"
              :key="dm.id"
              class="danmaku-item"
              :style="{ color: dm.color, animationDuration: dm.duration + 's', top: dm.top + '%' }"
            >
              {{ dm.content }}
            </span>
          </div>
          <video
            ref="videoEl"
            class="video-element"
            :src="streamUrl"
            controls
            @timeupdate="onTimeUpdate"
            @loadedmetadata="onLoaded"
            @ended="onEnded"
            @play="onPlay"
            @error="onVideoError"
            autoplay
          ></video>
          <!-- Overlay controls -->
          <div class="video-info-bar">
            <div class="video-info-left">
              <h1 class="video-title">{{ video.title }}</h1>
            </div>
            <div class="video-info-right">
              <button class="action-btn" @click="toggleLike" :class="{ liked: liked }">
                👍 {{ likeCount }}
              </button>
              <button class="action-btn" @click="toggleFollowVideo" :class="{ followed: followed }">
                {{ followed ? '✅ 已关注' : '+ 关注' }}
              </button>
              <span class="play-count">▶ {{ formatCount(playCount) }}次播放</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Danmaku Input -->
      <div class="danmaku-input-bar">
        <input
          v-model="danmakuText"
          type="text"
          class="danmaku-input"
          placeholder="发个弹幕吧~"
          @keyup.enter="sendDanmaku"
        />
        <button class="send-btn" @click="sendDanmaku" :disabled="!danmakuText.trim()">
          发送弹幕
        </button>
      </div>

      <!-- Info & Comments Section -->
      <div class="detail-section">
        <!-- Left: Video Info -->
        <div class="detail-left">
          <div class="video-meta">
            <span class="meta-item">📁 {{ video.relativePath }}</span>
            <span class="meta-item">💾 {{ video.sizeFormatted }}</span>
            <span class="meta-item">📅 {{ video.mtimeStr?.slice(0, 10) }}</span>
            <span class="meta-item">📱 {{ video.device }}</span>
          </div>
        </div>

        <!-- Right: Comments -->
        <div class="detail-right">
          <h3 class="section-title">评论 ({{ commentTotal }})</h3>
          <div class="comment-input-area">
            <input
              v-model="commentText"
              type="text"
              class="comment-input"
              placeholder="说点什么吧..."
              @keyup.enter="postComment"
            />
            <button class="comment-send-btn" @click="postComment" :disabled="!commentText.trim()">
              发表
            </button>
          </div>

          <!-- Comments list -->
          <div class="comments-list" v-if="comments.length > 0">
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <div class="comment-avatar">{{ c.username[0] }}</div>
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-user">{{ c.username }}</span>
                  <span class="comment-time">{{ formatTime(c.created_at) }}</span>
                </div>
                <div class="comment-content">{{ c.content }}</div>
              </div>
            </div>
          </div>
          <div v-else class="no-comments">暂无评论，来发第一条吧~</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getVideoDetail, getVideoStream, recordPlay,
  getComments, postComment,
  getDanmaku, sendDanmaku as apiSendDanmaku,
  likeVideo, followUp
} from '@/api/index.js'

const route = useRoute()
const router = useRouter()
const videoId = route.params.id

const video = ref({})
const loading = ref(true)
const error = ref(false)
const videoEl = ref(null)
const playerContainer = ref(null)
const danmakuCanvas = ref(null)
const streamUrl = ref('')

// Video state
const currentTime = ref(0)
const playCount = ref(0)
const likeCount = ref(0)
const liked = ref(false)
const followed = ref(false)

// Danmaku
const danmakuText = ref('')
const allDanmaku = ref([])
const activeDanmaku = ref([])
const danmakuQueue = ref([])
let danmakuTimer = null
let danmakuIdCounter = 0

// Comments
const comments = ref([])
const commentTotal = ref(0)
const commentText = ref('')

onMounted(async () => {
  try {
    const res = await getVideoDetail(videoId)
    if (res.data.code !== 0 || !res.data.data) {
      error.value = true
      loading.value = false
      return
    }
    video.value = res.data.data
    streamUrl.value = getVideoStream(videoId)
    playCount.value = res.data.data.playCount || 0
    likeCount.value = res.data.data.likeCount || 0
    loading.value = false

    // Record play
    recordPlay(videoId)
    playCount.value++

    // Load comments
    loadComments()

    // Load danmaku
    loadDanmaku()
  } catch (err) {
    console.error('Failed to load video:', err)
    error.value = true
    loading.value = false
  }
})

onUnmounted(() => {
  if (danmakuTimer) clearInterval(danmakuTimer)
})

function formatCount(num) {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

function formatTime(t) {
  if (!t) return ''
  return t.slice(11, 19)
}

// ===== Video Events =====
function onTimeUpdate() {
  if (!videoEl.value) return
  currentTime.value = videoEl.value.currentTime
}

function onLoaded() {
  // Autoplay
  if (videoEl.value) videoEl.value.play().catch(() => {})
}

function onPlay() {
  // Start danmaku engine
  startDanmakuEngine()
}

function onEnded() {
  if (danmakuTimer) clearInterval(danmakuTimer)
}

function onVideoError(e) {
  console.error('Video error:', e)
}

// ===== Danmaku =====
async function loadDanmaku() {
  try {
    const res = await getDanmaku(videoId)
    if (res.data.code === 0 && res.data.data) {
      allDanmaku.value = res.data.data
      // Queue them sorted by time
      danmakuQueue.value = [...allDanmaku.value].sort((a, b) => a.time_sec - b.time_sec)
    }
  } catch {}
}

function startDanmakuEngine() {
  if (danmakuTimer) return
  danmakuTimer = setInterval(() => {
    if (!videoEl.value || videoEl.value.paused) return
    const ct = videoEl.value.currentTime
    // Emit danmaku that should appear at this time
    while (danmakuQueue.value.length > 0 && danmakuQueue.value[0].time_sec <= ct) {
      const dm = danmakuQueue.value.shift()
      emitDanmaku(dm)
    }
  }, 200)
}

function emitDanmaku(dm) {
  const id = ++danmakuIdCounter
  const top = Math.random() * 70 + 5
  const duration = Math.random() * 3 + 5
  const item = {
    id,
    content: dm.content,
    color: dm.color || '#ffffff',
    top,
    duration
  }
  activeDanmaku.value.push(item)
  // Remove after animation
  setTimeout(() => {
    activeDanmaku.value = activeDanmaku.value.filter(d => d.id !== id)
  }, duration * 1000)
}

async function sendDanmaku() {
  const text = danmakuText.value.trim()
  if (!text || !videoEl.value) return

  const timeSec = Math.round(videoEl.value.currentTime)
  try {
    const res = await apiSendDanmaku(videoId, {
      content: text,
      time_sec: timeSec,
      color: '#ffd700',
      username: '匿名用户'
    })
    if (res.data.code === 0) {
      // Also show immediately
      emitDanmaku({ content: text, color: '#ffd700' })
      danmakuText.value = ''
    }
  } catch {}
}

// ===== Comments =====
async function loadComments() {
  try {
    const res = await getComments(videoId)
    if (res.data.code === 0) {
      comments.value = res.data.data.items || []
      commentTotal.value = res.data.data.total || 0
    }
  } catch {}
}

async function postComment() {
  const text = commentText.value.trim()
  if (!text) return
  try {
    const res = await postComment(videoId, text)
    if (res.data.code === 0) {
      comments.value.unshift(res.data.data)
      commentTotal.value++
      commentText.value = ''
    }
  } catch {}
}

// ===== Likes & Follow =====
async function toggleLike() {
  liked.value = !liked.value
  likeCount.value += liked.value ? 1 : -1
  try {
    const res = await likeVideo(videoId)
    if (res.data.code === 0) {
      liked.value = res.data.data.liked
      likeCount.value = res.data.data.count
    }
  } catch {}
}

async function toggleFollowVideo() {
  followed.value = !followed.value
  try {
    const res = await followUp(videoId)
    if (res.data.code === 0) {
      followed.value = res.data.data.followed
    }
  } catch {}
}
</script>

<style scoped>
.player-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 80px 24px 40px;
}

/* Player */
.player-section {
  margin-bottom: 16px;
}
.player-container {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}
.video-element {
  width: 100%;
  max-height: 75vh;
  display: block;
  background: #000;
}

/* Danmaku Canvas */
.danmaku-canvas {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 70%;
  z-index: 5;
  pointer-events: none;
  overflow: hidden;
}
.danmaku-item {
  position: absolute;
  white-space: nowrap;
  font-size: 16px;
  font-weight: 600;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
  left: 100%;
  animation: danmakuScroll linear forwards;
  pointer-events: none;
}
@keyframes danmakuScroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-200vw); }
}

/* Video info bar */
.video-info-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: linear-gradient(0deg, rgba(0,0,0,0.85) 0%, transparent 100%);
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  pointer-events: none;
}
.video-info-bar > * {
  pointer-events: auto;
}
.video-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
}
.video-info-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.action-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.3);
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover {
  background: rgba(255,255,255,0.15);
}
.action-btn.liked {
  background: var(--accent-red);
  border-color: var(--accent-red);
}
.action-btn.followed {
  background: #333;
  border-color: #555;
}
.play-count {
  color: rgba(255,255,255,0.8);
  font-size: 13px;
}

/* Danmaku input */
.danmaku-input-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
}
.danmaku-input {
  flex: 1;
  height: 40px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 0 20px;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}
.danmaku-input:focus {
  border-color: var(--accent-yellow);
}
.send-btn {
  padding: 0 24px;
  border-radius: 20px;
  border: none;
  background: var(--accent-yellow);
  color: #000;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.send-btn:not(:disabled):hover {
  opacity: 0.9;
}

/* Detail section */
.detail-section {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}
.detail-left {
  min-height: 200px;
}
.video-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius);
  margin-bottom: 16px;
}
.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Comments */
.detail-right {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 20px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}
.comment-input-area {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.comment-input {
  flex: 1;
  height: 36px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  padding: 0 14px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}
.comment-input:focus {
  border-color: var(--accent-yellow);
}
.comment-send-btn {
  padding: 0 16px;
  border-radius: 18px;
  border: none;
  background: var(--accent-yellow);
  color: #000;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}
.comment-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.comments-list {
  max-height: 500px;
  overflow-y: auto;
}
.comment-item {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}
.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--text-primary);
  flex-shrink: 0;
}
.comment-body {
  flex: 1;
}
.comment-header {
  display: flex;
  gap: 10px;
  margin-bottom: 4px;
}
.comment-user {
  font-size: 13px;
  color: var(--accent-yellow);
  font-weight: 500;
}
.comment-time {
  font-size: 11px;
  color: var(--text-muted);
}
.comment-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}
.no-comments {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 14px;
}

/* Error state */
.error-state {
  text-align: center;
  padding: 100px 20px;
  color: var(--text-muted);
}
.back-link {
  display: inline-block;
  margin-top: 16px;
  color: var(--accent-yellow);
  text-decoration: none;
}

/* Responsive */
@media (max-width: 900px) {
  .detail-section {
    grid-template-columns: 1fr;
  }
}
</style>
