<template>
  <div class="debug-card">
    <h3>监考系统调试</h3>
    <button @click="connectWebSocket">连接监考WS</button>
    <div class="monitoring-feed">
      <div v-for="(event, index) in events" :key="index">{{ event }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMonitoring } from '@/composables/useMonitoring'

const { connect } = useMonitoring()
const events = ref([])

const connectWebSocket = () => {
  connect({
    onMessage: (msg) => events.value.push(msg)
  })
}
</script>