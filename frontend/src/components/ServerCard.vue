<template>
  <div class="server-card" :class="{ offline: server.status !== 'online' }">
    <div class="server-header">
      <div class="server-title">
        <h2>{{ server.name }}</h2>
        <span class="hostname">({{ server.hostname || server.host }})</span>
      </div>
      <span class="status-badge" :class="server.status">
        {{ server.status }}
      </span>
    </div>

    <template v-if="server.status === 'online'">
      <SystemMetrics :system="server.system" />

      <div class="gpu-section" v-if="server.gpus?.length">
        <h3 class="section-title">GPUs ({{ server.gpus.length }})</h3>
        <div class="gpu-list">
          <GPUCard
            v-for="gpu in server.gpus"
            :key="gpu.index"
            :gpu="gpu"
          />
        </div>
      </div>

      <div class="no-gpu" v-else>
        No GPU detected
      </div>
    </template>

    <div v-else class="error-message">
      {{ server.error_message || 'Connection failed' }}
    </div>
  </div>
</template>

<script setup>
import SystemMetrics from './SystemMetrics.vue'
import GPUCard from './GPUCard.vue'

defineProps({
  server: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped>
.server-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
}

.server-card.offline {
  opacity: 0.7;
}

.server-header {
  background: #21262d;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #30363d;
}

.server-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.server-title h2 {
  font-size: 16px;
  font-weight: 600;
  color: #f0f6fc;
}

.hostname {
  font-size: 13px;
  color: #8b949e;
}

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.status-badge.online {
  background: rgba(35, 134, 54, 0.2);
  color: #3fb950;
}

.status-badge.offline {
  background: rgba(248, 81, 73, 0.2);
  color: #f85149;
}

.gpu-section {
  padding: 12px 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #8b949e;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gpu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.no-gpu {
  padding: 24px 16px;
  text-align: center;
  color: #8b949e;
  font-size: 14px;
}

.error-message {
  padding: 24px 16px;
  color: #f85149;
  font-size: 14px;
}
</style>
