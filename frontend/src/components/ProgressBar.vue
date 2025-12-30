<template>
  <div class="progress-bar">
    <div
      class="progress-fill"
      :style="{
        width: `${Math.min(100, Math.max(0, percent))}%`,
        backgroundColor: color,
      }"
    ></div>
  </div>
</template>

<script setup>
defineProps({
  percent: {
    type: Number,
    default: 0,
  },
  color: {
    type: String,
    default: '#58a6ff',
  },
})
</script>

<style scoped>
.progress-bar {
  height: 4px;
  background: #30363d;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}
</style>
