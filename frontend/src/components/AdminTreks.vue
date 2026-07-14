<script setup>
import { ref, onMounted } from 'vue'
import Api from '../api.js'

const error = ref('')
const success = ref('')
const treks = ref([])
const staffList = ref([])
const assignStaffId = ref({})
const editingTrekId = ref(null)

const emptyTrek = () => ({
  name: '', location: '', difficulty: 'Easy', duration_days: 1,
  total_slots: 10, start_date: '', end_date: '', description: '',
})
const newTrek = ref(emptyTrek())

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadTreks = () => safeCall(async () => {
  const data = await Api.get('/admin/treks')
  treks.value = data.treks
})

const loadStaff = () => safeCall(async () => {
  const data = await Api.get('/admin/staff')
  staffList.value = data.staff
})

const createOrUpdateTrek = () => safeCall(async () => {
  if (editingTrekId.value) {
    await Api.put(`/admin/treks/${editingTrekId.value}`, newTrek.value)
    success.value = 'Trek updated.'
  } else {
    await Api.post('/admin/treks', newTrek.value)
    success.value = 'Trek created.'
  }
  newTrek.value = emptyTrek()
  editingTrekId.value = null
  await loadTreks()
})

const editTrek = (t) => {
  editingTrekId.value = t.id
  newTrek.value = {
    name: t.name, location: t.location, difficulty: t.difficulty,
    duration_days: t.duration_days, total_slots: t.total_slots,
    start_date: t.start_date || '', end_date: t.end_date || '', description: t.description || '',
  }
}

const cancelEdit = () => {
  editingTrekId.value = null
  newTrek.value = emptyTrek()
}

const deleteTrek = (id) => {
  if (!confirm('Delete this trek permanently?')) return
  safeCall(async () => {
    await Api.del(`/admin/treks/${id}`)
    success.value = 'Trek deleted.'
    await loadTreks()
  })
}

const assignStaff = (trek) => safeCall(async () => {
  const staffId = assignStaffId.value[trek.id]
  if (!staffId) { error.value = 'Select a staff member first.'; return }
  await Api.put(`/admin/treks/${trek.id}/assign-staff`, { staff_id: Number(staffId) })
  success.value = `Staff assigned to ${trek.name}.`
  await loadTreks()
})

onMounted(async () => {
  await loadTreks()
  await loadStaff()
})
</script>

<template>
  <div class="container min-vh-90">
    <h4 class="mb-3">Manage Treks</h4>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5>{{ editingTrekId ? 'Edit Trek' : 'Create New Trek' }}</h5>
        <form @submit.prevent="createOrUpdateTrek" class="row g-2">
          <div class="col-md-4"><input v-model="newTrek.name" placeholder="Trek Name" class="form-control" required /></div>
          <div class="col-md-4"><input v-model="newTrek.location" placeholder="Location" class="form-control" required /></div>
          <div class="col-md-2">
            <select v-model="newTrek.difficulty" class="form-select">
              <option>Easy</option><option>Moderate</option><option>Hard</option>
            </select>
          </div>
          <div class="col-md-2"><input v-model="newTrek.duration_days" type="number" min="1" placeholder="Duration (days)" class="form-control" required /></div>
          <div class="col-md-2"><input v-model="newTrek.total_slots" type="number" min="1" placeholder="Total Slots" class="form-control" required /></div>
          <div class="col-md-3"><input v-model="newTrek.start_date" type="date" class="form-control" /></div>
          <div class="col-md-3"><input v-model="newTrek.end_date" type="date" class="form-control" /></div>
          <div class="col-md-4"><input v-model="newTrek.description" placeholder="Description" class="form-control" /></div>
          <div class="col-md-12 d-flex gap-2 mt-2">
            <button class="btn btn-success">{{ editingTrekId ? 'Save Changes' : 'Create Trek' }}</button>
            <button v-if="editingTrekId" type="button" class="btn btn-outline-secondary" @click="cancelEdit">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table table-hover bg-white align-middle">
        <thead><tr><th>Name</th><th>Location</th><th>Difficulty</th><th>Slots</th><th>Status</th><th>Assigned Staff</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="t in treks" :key="t.id">
            <td>{{ t.name }}</td><td>{{ t.location }}</td>
            <td><span class="badge" :class="'badge-difficulty-'+t.difficulty">{{ t.difficulty }}</span></td>
            <td>{{ t.registered_count }}/{{ t.total_slots }}</td>
            <td><span :class="'status-'+t.status">{{ t.status }}</span></td>
            <td>
              <div v-if="t.assigned_staff_name">{{ t.assigned_staff_name }}</div>
              <div v-else class="input-group input-group-sm" style="max-width:220px;">
                <select v-model="assignStaffId[t.id]" class="form-select">
                  <option disabled value="">Select staff</option>
                  <option v-for="s in staffList" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
                <button class="btn btn-outline-primary" @click="assignStaff(t)">Assign</button>
              </div>
            </td>
            <td class="d-flex gap-1">
              <button class="btn btn-sm btn-outline-primary" @click="editTrek(t)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteTrek(t.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
