<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Api from '../api.js'

const router = useRouter()
const tab = ref('overview')
const error = ref('')
const success = ref('')
const overview = ref(null)
const treks = ref([])
const editSlots = ref({})

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadOverview = () => safeCall(async () => { overview.value = await Api.get('/staff/dashboard') })

const switchTab = async (t) => {
  tab.value = t
  success.value = ''
  if (t === 'treks') await loadTreks()
}

const loadTreks = () => safeCall(async () => {
  const data = await Api.get('/staff/treks')
  treks.value = data.treks
  editSlots.value = {}
  data.treks.forEach((t) => { editSlots.value[t.id] = t.available_slots })
})

const updateSlots = (trek) => safeCall(async () => {
  await Api.put(`/staff/treks/${trek.id}`, { available_slots: Number(editSlots.value[trek.id]) })
  success.value = `Updated slots for ${trek.name}`
  await loadTreks()
})

const updateStatus = (trek, status) => safeCall(async () => {
  await Api.put(`/staff/treks/${trek.id}`, { status })
  success.value = `${trek.name} marked as ${status}`
  await loadTreks()
})

const markCompleted = (trek) => safeCall(async () => {
  await Api.put(`/staff/treks/${trek.id}/complete`, {})
  success.value = `${trek.name} marked as Completed`
  await loadTreks()
})

const viewParticipants = (trek) => router.push(`/staff/treks/${trek.id}`)

onMounted(loadOverview)
</script>

<template>
  <div class="container min-vh-90">
    <ul class="nav nav-pills mb-4 gap-2">
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='overview'}" href="#" @click.prevent="switchTab('overview')">Overview</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='treks'}" href="#" @click.prevent="switchTab('treks')">My Treks</a></li>
    </ul>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div v-if="tab==='overview' && overview" class="row g-3">
      <div class="col-md-6">
        <div class="card stat-card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="fs-4 fw-bold">{{ overview.assigned_trek_count }}</div>
            <div class="text-muted small">Assigned Treks</div>
          </div>
        </div>
      </div>
      <div class="col-12 mt-3">
        <h5>Registrations per Trek</h5>
        <table class="table bg-white">
          <thead><tr><th>Trek</th><th>Registered Users</th></tr></thead>
          <tbody>
            <tr v-for="r in overview.registrations_per_trek" :key="r.trek_id">
              <td>{{ r.trek_name }}</td><td>{{ r.registered_count }}</td>
            </tr>
            <tr v-if="overview.registrations_per_trek.length===0"><td colspan="2" class="text-muted">No treks assigned yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="tab==='treks'">
      <div class="row g-3">
        <div class="col-md-6" v-for="t in treks" :key="t.id">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <h5>{{ t.name }} <span class="badge bg-light" :class="'status-'+t.status">{{ t.status }}</span></h5>
              <p class="text-muted mb-1"><i class="bi bi-geo-alt"></i> {{ t.location }} &middot; {{ t.duration_days }} day(s)</p>
              <p class="mb-2">Registered: {{ t.registered_count }} / {{ t.total_slots }}</p>

              <div class="input-group input-group-sm mb-2" style="max-width: 220px;">
                <input type="number" class="form-control" v-model="editSlots[t.id]" min="0" :max="t.total_slots" />
                <button class="btn btn-outline-success" @click="updateSlots(t)">Update Slots</button>
              </div>

              <div class="d-flex gap-2 flex-wrap">
                <button class="btn btn-sm btn-outline-primary" @click="updateStatus(t, 'Open')" :disabled="t.status==='Open'">Set Open</button>
                <button class="btn btn-sm btn-outline-secondary" @click="updateStatus(t, 'Closed')" :disabled="t.status==='Closed'">Set Closed</button>
                <button class="btn btn-sm btn-outline-success" @click="markCompleted(t)" :disabled="t.status==='Completed'">Mark Completed</button>
                <button class="btn btn-sm btn-link" @click="viewParticipants(t)">View Participants</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="treks.length===0" class="text-muted">No treks assigned to you yet.</div>
      </div>
    </div>
  </div>
</template>
