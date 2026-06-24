<template>
  <div class="home">
    <!-- Category filter -->
    <div class="category-bar">
      <span
        v-for="cat in categories"
        :key="cat.key"
        class="category-tag"
        :class="{ active: activeCategory === cat.key }"
        @click="switchCategory(cat.key)"
      >
        {{ cat.label }}
        <span v-if="cat.count" class="cat-count">({{ cat.count }})</span>
      </span>
    </div>

    <!-- Video grid -->
    <div class="video-grid" v-if="items.length > 0">
      <VideoCard
        v-for="video in items"
        :key="video.id"
        :video="video"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-spinner" style="padding: 60px;" />

    <!-- Empty state -->
    <div v-if="!loading && items.length === 0" class="empty-state">
      <div class="empty-icon">📹</div>
      <p v-if="searchQuery">未找到 "{{ searchQuery }}" 相关视频</p>
      <p v-else>正在扫描视频文件...</p>
      <button v-if="!searchQuery" class="retry-btn" @click="loadVideos(true)">
        刷新视频列表
      </button>
    </div>

    <!-- Load more trigger -->
    <div ref="loadMoreRef" class="load-more-trigger" v-if="hasMore">
      <div v-if="loadingMore" class="loading-spinner" style="padding: 30px;" />
      <div v-else class="load-hint">下拉加载更多</div>
    </div>

    <!-- End marker -->
    <div v-if="!hasMore && items.length > 0" class="end-marker">
      已显示全部 {{ total }} 个视频
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import VideoCard from '@/components/VideoCard.vue'
import { getVideos } from '@/api/index.js'

const route = useRoute()

const items = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(1)
const total = ref(0)
const limit = 25 // 5×5
const searchQuery = ref('')
const activeCategory = ref('all')

const categories = ref([
  { key: 'all', label: '全部' },
  { key: 'HONOR 50', label: 'HONOR 50' },
  { key: 'NX769J', label: 'NX769J' },
  { key: 'V2171A', label: 'V2171A' },
  { key: 'bw', label: '卡片机' },
])

const hasMore = computed(() => items.value.length < total.value)
const loadMoreRef = ref(null)
let observer = null

onMounted(async () => {
  // Check for search query
  if (route.query.q) {
    searchQuery.value = route.query.q
  }
  await loadVideos(true)
  setupInfiniteScroll()
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})

async function loadVideos(reset = false) {
  if (reset) {
    page.value = 1
    items.value = []
    loading.value = true
  }

  try {
    const params = { page: page.value, limit }
    if (searchQuery.value) params.q = searchQuery.value

    const res = await getVideos(page.value, limit)
    const data = res.data.data

    if (reset) {
      items.value = data.items.map(enhanceVideo)
    } else {
      items.value = [...items.value, ...data.items.map(enhanceVideo)]
    }
    total.value = data.total
  } catch (err) {
    console.error('Failed to load videos:', err)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Enhance video with computed display data
function enhanceVideo(video) {
  // Extract title from filename
  let title = video.fileName || ''
  const extIdx = title.lastIndexOf('.')
  if (extIdx > 0) title = title.slice(0, extIdx)
  // Clean up title
  title = title.replace(/[_-]/g, ' ').trim()
  if (!title) title = video.fileName || '未命名视频'
  video.title = title
  return video
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  await loadVideos(false)
}

function setupInfiniteScroll() {
  nextTick(() => {
    if (!loadMoreRef.value) return
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore.value && !loadingMore.value) {
          loadMore()
        }
      },
      { rootMargin: '200px' }
    )
    observer.observe(loadMoreRef.value)
  })
}

function switchCategory(key) {
  activeCategory.value = key
  // Filter logic - for now just show all, can be extended
  loadVideos(true)
}
</script>

<style scoped>
.home {
  max-width: 1600px;
  margin: 0 auto;
  padding: 80px 24px 40px;
}

/* Category bar */
.category-bar {
  display: flex;
  gap: 10px;
  padding: 10px 0 20px;
  flex-wrap: wrap;
}
.category-tag {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.category-tag:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.category-tag.active {
  background: var(--accent-yellow);
  color: #000;
  font-weight: 600;
  border-color: var(--accent-yellow);
}
.cat-count {
  font-size: 11px;
  opacity: 0.7;
}

/* Video grid - 5 columns */
.video-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 100px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.retry-btn {
  margin-top: 16px;
  padding: 10px 24px;
  background: var(--accent-yellow);
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  font-weight: 600;
}
.retry-btn:hover {
  opacity: 0.9;
}

/* Load more */
.load-more-trigger {
  margin-top: 30px;
}
.load-hint {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}
.end-marker {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 13px;
  border-top: 1px solid var(--border-color);
  margin-top: 30px;
}

/* Responsive */
@media (max-width: 1400px) {
  .video-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 1100px) {
  .video-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .video-grid { grid-template-columns: repeat(2, 1fr); }
  .home { padding: 70px 12px 20px; }
}
</style>
