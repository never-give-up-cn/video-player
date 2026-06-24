<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="nav-logo">
        <span class="logo-icon">▶</span>
        <span class="logo-text">暗黑视频流</span>
      </router-link>
      <div class="nav-search">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索视频..."
          @keyup.enter="doSearch"
        />
        <button class="search-btn" @click="doSearch">🔍</button>
      </div>
      <div class="nav-stats" v-if="totalVideos > 0">
        <span class="stat-count">{{ totalVideos }} 个视频</span>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getVideos } from '@/api/index.js'

const router = useRouter()
const searchQuery = ref('')
const totalVideos = ref(0)

onMounted(async () => {
  try {
    const res = await getVideos(1, 1)
    totalVideos.value = res.data.total || 0
  } catch {}
})

function doSearch() {
  if (searchQuery.value.trim()) {
    router.push({ path: '/', query: { q: searchQuery.value.trim() } })
  }
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: rgba(10, 10, 10, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  z-index: 1000;
}
.nav-inner {
  max-width: 1600px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 24px;
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--text-primary);
  flex-shrink: 0;
}
.logo-icon {
  font-size: 22px;
  color: var(--accent-yellow);
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
}
.nav-search {
  flex: 1;
  display: flex;
  max-width: 480px;
  margin: 0 auto;
}
.nav-search input {
  flex: 1;
  height: 36px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-right: none;
  border-radius: 18px 0 0 18px;
  padding: 0 16px;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}
.nav-search input:focus {
  border-color: var(--accent-yellow);
}
.nav-search input::placeholder {
  color: var(--text-muted);
}
.search-btn {
  width: 44px;
  height: 36px;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 0 18px 18px 0;
  cursor: pointer;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
.search-btn:hover {
  background: #333;
}
.nav-stats {
  flex-shrink: 0;
}
.stat-count {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
