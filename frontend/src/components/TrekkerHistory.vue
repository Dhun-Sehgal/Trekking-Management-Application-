<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Api from '../api.js'

const error = ref('')
const success = ref('')
const history = ref([])
const exportTaskId = ref(null)
const exportStatus = ref(null)
const exportFilename = ref(null)
let pollHandle = null

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadHistory = () => safeCall(async () => {
  const data = await Api.get('/user/history')
  history.value = data.history
})

const startExport = () => safeCall(async () => {
  const data = await Api.post('/user/export-history', {})
  exportTaskId.value = data.task_id
  exportStatus.value = 'PENDING'
  pollExport()
})

const pollExport = () => {
  if (pollHandle) clearInterval(pollHandle)
  pollHandle = setInterval(async () => {
    try {
      const data = await Api.get(`/user/export-status/${exportTaskId.value}`)
      exportStatus.value = data.state
      if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
        clearInterval(pollHandle)
        if (data.state === 'SUCCESS') {
          success.value = `Export ready: ${data.result.filename} (${data.result.record_count} records)`
          exportFilename.value = data.result.filename
        } else {
          error.value = 'Export failed: ' + (data.error || 'unknown error')
        }
      }
    } catch (e) {
      clearInterval(pollHandle)
      error.value = e.message
    }
  }, 2000)
}

const downloadExport = () => {
  if (!exportFilename.value) return
  const token = Api.getToken()
  fetch(`${Api.BASE}/user/download-export/${exportFilename.value}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => r.blob())
    .then((blob) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = exportFilename.value
      a.click()
    })
}

onMounted(loadHistory)
onUnmounted(() => { if (pollHandle) clearInterval(pollHandle) })
</script>

<template>
  <div class="container min-vh-90">
    <h4 class="mb-3">Trekking History</h4>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <button class="btn btn-outline-success mb-3" @click="startExport" :disabled="exportStatus==='PENDING' || exportStatus==='STARTED'">
      <i class="bi bi-download"></i> Export as CSV
    </button>
    <span v-if="exportStatus && exportStatus!=='SUCCESS'" class="ms-2 text-muted">Status: {{ exportStatus }}...</span>
    <button v-if="exportStatus==='SUCCESS'" class="btn btn-sm btn-link" @click="downloadExport">Download ready file</button>

    <table class="table table-hover bg-white mt-3">
      <thead><tr><th>Trek</th><th>Location</th><th>Status</th><th>Booking Date</th></tr></thead>
      <tbody>
        <tr v-for="b in history" :key="b.id">
          <td>{{ b.trek_name }}</td><td>{{ b.trek_location }}</td>
          <td>{{ b.status }}</td><td>{{ b.booking_date && b.booking_date.slice(0,10) }}</td>
        </tr>
        <tr v-if="history.length===0"><td colspan="4" class="text-muted">No history yet.</td></tr>
      </tbody>
    </table>
  </div>
</template>
