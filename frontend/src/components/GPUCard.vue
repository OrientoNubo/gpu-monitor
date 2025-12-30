<template>
  <div class="gpu-card">
    <div class="gpu-header">
      <span class="gpu-index">[{{ gpu.index }}]</span>
      <span class="gpu-name">{{ gpu.name }}</span>
      <span class="driver-version">{{ gpu.driver_version }}</span>
    </div>

    <div class="gpu-metrics">
      <div class="metric">
        <span class="metric-label">Temp</span>
        <span class="metric-value" :class="tempClass">{{ gpu.temperature_celsius }}'C</span>
      </div>

      <div class="metric">
        <span class="metric-label">GPU</span>
        <span class="metric-value" :class="utilClass">{{ gpu.utilization_percent }}%</span>
      </div>

      <div class="metric memory">
        <span class="metric-label">VRAM</span>
        <div class="memory-info">
          <span class="metric-value">{{ formatMemory(gpu.memory.used_mb) }}</span>
          <span class="metric-detail">/ {{ formatMemory(gpu.memory.total_mb) }}</span>
        </div>
        <ProgressBar :percent="gpu.memory.usage_percent" color="#a371f7" />
      </div>
    </div>

    <div class="processes" v-if="gpu.processes?.length">
      <div
        class="process"
        v-for="proc in gpu.processes"
        :key="proc.pid"
      >
        <span class="process-user">{{ proc.user }}</span>
        <span class="process-cmd">{{ proc.command }}</span>
        <span class="process-pid">/{{ proc.pid }}</span>
        <span class="process-mem">({{ proc.gpu_memory_mb }}M)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProgressBar from './ProgressBar.vue'

const props = defineProps({
  gpu: {
    type: Object,
    required: true,
  },
})

const tempClass = computed(() => {
  const temp = props.gpu.temperature_celsius
  if (temp >= 80) return 'critical'
  if (temp >= 70) return 'high'
  if (temp >= 50) return 'medium'
  return 'low'
})

const utilClass = computed(() => {
  const util = props.gpu.utilization_percent
  if (util > 80) return 'high'
  if (util > 10) return 'active'
  return 'idle'
})

const formatMemory = (mb) => {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)}G`
  return `${mb}M`
}
</script>

<style scoped>
.gpu-card {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 10px 12px;
}

.gpu-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.gpu-index {
  color: #58a6ff;
  font-weight: 600;
}

.gpu-name {
  color: #a371f7;
  font-weight: 500;
  flex: 1;
}

.driver-version {
  font-size: 11px;
  color: #8b949e;
}

.gpu-metrics {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric.memory {
  flex: 1;
  min-width: 120px;
}

.metric-label {
  font-size: 10px;
  color: #8b949e;
  text-transform: uppercase;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
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

.metric-value.critical {
  color: #ff7b72;
  animation: blink 1s ease-in-out infinite;
}

.metric-value.idle {
  color: #8b949e;
}

.metric-value.active {
  color: #3fb950;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.memory-info {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-detail {
  font-size: 12px;
  color: #8b949e;
}

.processes {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #30363d;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.process {
  font-size: 12px;
  display: flex;
  gap: 0;
}

.process-user {
  color: #8b949e;
}

.process-user::after {
  content: ':';
}

.process-cmd {
  color: #58a6ff;
}

.process-pid {
  color: #8b949e;
}

.process-mem {
  color: #f0883e;
}
</style>
