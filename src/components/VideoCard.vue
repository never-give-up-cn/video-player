<template>
  <div class="video-card" @click="goToPlayer">
    <!-- Cover area -->
    <div class="card-cover">
      <img
        :src="video.thumbnail"
        :alt="video.title"
        class="cover-img"
        loading="lazy"
        @error="onImgError"
      />
      <!-- Title overlay on cover -->
      <div class="cover-title-overlay">
        <span class="cover-title-text">{{ shortTitle }}</span>
      </div>
      <!-- Duration badge -->
      <span class="duration-badge">{{ displayDuration }}</span>
      <!-- Bottom-left stats -->
      <div class="cover-stats">
        <span class="stat-item">▶ {{ formatCount(video.playCount || randomPlay) }}</span>
        <span class="stat-item">💬 {{ formatCount(video.danmakuCount || randomDanmaku) }}</span>
      </div>
      <!-- Hot badge -->
      <span v-if="isHot" class="hot-badge">🔥 {{ randomLikes }}万点赞</span>
    </div>

    <!-- Title -->
    <div class="card-title" :title="video.title">{{ video.title }}</div>

    <!-- Bottom info -->
    <div class="card-footer">
      <div class="footer-left">
        <span class="up-name">{{ video.device || '未知UP主' }}</span>
        <span class="publish-date">{{ displayDate }}</span>
      </div>
      <div class="footer-right">
        <button
          v-if="isHot"
          class="follow-btn"
          :class="{ followed: followed }"
          @click.stop="toggleFollow"
        >
          {{ followed ? '已关注' : '+ 关注' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { followUp } from '@/api/index.js'

const props = defineProps({
  video: { type: Object, required: true }
})

const router = useRouter()
const followed = ref(false)
const imgError = ref(false)

// Generate deterministic but varied random values based on video id
const seed = computed(() => {
  let hash = 0
  const str = props.video.id || props.video.fileName || ''
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
})

const randomPlay = computed(() => (seed.value % 90000) + 1000)
const randomDanmaku = computed(() => (seed.value % 5000) + 10)
const randomLikes = computed(() => ((seed.value % 20) + 1))
const isHot = computed(() => (seed.value % 5) === 0)

const shortTitle = computed(() => {
  const t = props.video.title || ''
  return t.length > 20 ? t.slice(0, 18) + '...' : t
})

const displayDuration = computed(() => {
  return props.video.duration || `${(seed.value % 30) + 1}:${String((seed.value % 59)).padStart(2, '0')}`
})

const displayDate = computed(() => {
  if (props.video.mtimeStr) {
    return props.video.mtimeStr.slice(0, 10)
  }
  return '2024-01-01'
})

function formatCount(num) {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

function onImgError() {
  imgError.value = true
}

function goToPlayer() {
  router.push(`/video/${encodeURIComponent(props.video.id)}`)
}

async function toggleFollow() {
  followed.value = !followed.value
  try {
    await followUp(props.video.id)
  } catch {}
}
</script>

<style scoped>
.video-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}
.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

.card-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #111;
}
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.video-card:hover .cover-img {
  transform: scale(1.05);
}

/* Yellow title overlay */
.cover-title-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 12px 10px 6px;
  background: linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.2) 70%, transparent 100%);
}
.cover-title-text {
  color: #ffd700;
  font-size: 18px;
  font-weight: 800;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
  line-height: 1.3;
  display: block;
  letter-spacing: 1px;
}

/* Duration badge */
.duration-badge {
  position: absolute;
  bottom: 32px;
  right: 8px;
  background: rgba(0,0,0,0.8);
  color: #fff;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

/* Bottom-left stats */
.cover-stats {
  position: absolute;
  bottom: 32px;
  left: 8px;
  display: flex;
  gap: 10px;
}
.stat-item {
  color: rgba(255,255,255,0.9);
  font-size: 12px;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
}

/* Hot badge */
.hot-badge {
  position: absolute;
  top: 50px;
  right: 8px;
  background: linear-gradient(135deg, #ff6a00, #ee0979);
  color: #fff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 12px;
  font-weight: 700;
}

/* Card title */
.card-title {
  padding: 10px 10px 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  flex: 1;
}

/* Footer */
.card-footer {
  padding: 6px 10px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.footer-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.up-name {
  font-size: 12px;
  color: var(--text-secondary);
}
.publish-date {
  font-size: 11px;
  color: var(--text-muted);
}
.follow-btn {
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 14px;
  border: 1px solid var(--accent-orange);
  background: transparent;
  color: var(--accent-orange);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.follow-btn:hover {
  background: var(--accent-orange);
  color: #fff;
}
.follow-btn.followed {
  background: #333;
  color: var(--text-secondary);
  border-color: #444;
}
</style>
