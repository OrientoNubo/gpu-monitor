<template>
  <div id="app" class="app">
    <header class="header">
      <h1>GPU Monitor</h1>
      <div class="update-info">
        <span v-if="data">Last updated: {{ formatTime(data.timestamp) }}</span>
        <span v-else>Loading...</span>
        <span class="refresh-indicator" :class="{ active: isRefreshing }"></span>
      </div>
    </header>

    <main class="main">
      <div v-if="loading && !data" class="loading">
        Loading...
      </div>

      <div v-else-if="error" class="error">
        {{ error }}
      </div>

      <div v-else-if="data" class="server-grid">
        <ServerCard
          v-for="server in data.servers"
          :key="server.host"
          :server="server"
        />
      </div>
    </main>

    <footer class="footer">
      <p>Auto-refresh: {{ refreshInterval }}s | Version: {{ data?.collector_version || '-' }}</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ServerCard from './components/ServerCard.vue'

const data = ref(null)
const loading = ref(true)
const error = ref(null)
const isRefreshing = ref(false)
const refreshInterval = 60

let timer = null

const fetchData = async () => {
  isRefreshing.value = true
  try {
    const res = await fetch(`data/status.json?t=${Date.now()}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
    error.value = null
  } catch (e) {
    error.value = `Failed to load data: ${e.message}`
  } finally {
    loading.value = false
    isRefreshing.value = false
  }
}

const formatTime = (iso) => {
  if (!iso) return 'N/A'
  return new Date(iso).toLocaleString()
}

onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, refreshInterval * 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  background-color: #0d1117;
  color: #c9d1d9;
  line-height: 1.5;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #161b22;
  border-bottom: 1px solid #30363d;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #f0f6fc;
}

.update-info {
  font-size: 13px;
  color: #8b949e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #238636;
}

.refresh-indicator.active {
  background: #f0883e;
  animation: pulse 0.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.main {
  flex: 1;
  padding: 24px;
}

.loading, .error {
  text-align: center;
  padding: 48px;
  font-size: 16px;
}

.error {
  color: #f85149;
}

.server-grid {
  display: grid;
  gap: 24px;
}

.footer {
  background: #161b22;
  border-top: 1px solid #30363d;
  padding: 12px 24px;
  text-align: center;
  font-size: 12px;
  color: #8b949e;
}
</style>
