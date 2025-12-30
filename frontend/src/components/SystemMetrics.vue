<template>
  <div class="system-metrics">
    <div class="metric-row">
      <div class="metric">
        <span class="metric-label">CPU</span>
        <div class="metric-value-row">
          <span class="metric-value" :class="cpuClass">{{ system.cpu?.usage_percent ?? 0 }}%</span>
          <span class="metric-detail">{{ system.cpu?.cores ?? 0 }} cores</span>
        </div>
        <ProgressBar :percent="system.cpu?.usage_percent ?? 0" :color="cpuColor" />
      </div>

      <div class="metric">
        <span class="metric-label">Memory</span>
        <div class="metric-value-row">
          <span class="metric-value" :class="memClass">{{ formatBytes(system.memory?.used_bytes) }}</span>
          <span class="metric-detail">/ {{ formatBytes(system.memory?.total_bytes) }}</span>
        </div>
        <ProgressBar :percent="system.memory?.usage_percent ?? 0" :color="memColor" />
      </div>
    </div>

    <div class="disk-row" v-if="system.disks?.length">
      <div class="metric disk" v-for="disk in mainDisks" :key="disk.mount_point">
        <span class="metric-label">{{ disk.mount_point }}</span>
        <div class="metric-value-row">
          <span class="metric-value small">{{ formatBytes(disk.used_bytes) }}</span>
          <span class="metric-detail">/ {{ formatBytes(disk.total_bytes) }} ({{ disk.usage_percent }}%)</span>
        </div>
        <ProgressBar :percent="disk.usage_percent" color="#8b949e" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProgressBar from './ProgressBar.vue'

const props = defineProps({
  system: {
    type: Object,
    required: true,
  },
})

const cpuClass = computed(() => {
  const usage = props.system.cpu?.usage_percent ?? 0
  if (usage >= 80) return 'high'
  if (usage >= 50) return 'medium'
  return 'low'
})

const cpuColor = computed(() => {
  const usage = props.system.cpu?.usage_percent ?? 0
  if (usage >= 80) return '#f85149'
  if (usage >= 50) return '#f0883e'
  return '#3fb950'
})

const memClass = computed(() => {
  const usage = props.system.memory?.usage_percent ?? 0
  if (usage >= 80) return 'high'
  if (usage >= 50) return 'medium'
  return 'low'
})

const memColor = computed(() => {
  const usage = props.system.memory?.usage_percent ?? 0
  if (usage >= 80) return '#f85149'
  if (usage >= 50) return '#f0883e'
  return '#58a6ff'
})

const mainDisks = computed(() => {
  // Show only important mount points
  const important = ['/', '/home', '/data', '/workspace']
  const disks = props.system.disks || []
  return disks.filter(d => important.some(p => d.mount_point === p || d.mount_point.startsWith(p + '/')))
    .slice(0, 3)
})

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let value = bytes
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024
    i++
  }
  return `${value.toFixed(i > 1 ? 1 : 0)} ${units[i]}`
}
</script>

<style scoped>
.system-metrics {
  padding: 12px 16px;
  border-bottom: 1px solid #30363d;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.disk-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #30363d;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 11px;
  font-weight: 600;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #f0f6fc;
}

.metric-value.small {
  font-size: 14px;
}

.metric-value.low {
  color: #3fb950;
}

.metric-value.medium {
  color: #f0883e;
}

.metric-value.high {
  color: #f85149;
}

.metric-detail {
  font-size: 12px;
  color: #8b949e;
}
</style>
