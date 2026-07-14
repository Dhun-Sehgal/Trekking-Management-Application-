<script setup>
import { ref, onMounted } from 'vue'
import Api from '../api.js'

const error = ref('')
const success = ref('')
const staffList = ref([])
const newStaff = ref({ name: '', email: '', password: '', phone: '' })

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadStaff = () => safeCall(async () => {
  const data = await Api.get('/admin/staff')
  staffList.value = data.staff
})

const createStaff = () => safeCall(async () => {
  await Api.post('/admin/staff', newStaff.value)
  success.value = 'Staff account created.'
  newStaff.value = { name: '', email: '', password: '', phone: '' }
  await loadStaff()
})
const toggleBlacklist = (staff) => safeCall(async () => {
  await Api.put(`/admin/users/${staff.id}/blacklist`, {
    is_blacklisted: !staff.is_blacklisted
  })

  await loadStaff()
})

onMounted(loadStaff)
</script>

<template>
  <div class="container min-vh-90">
    <h4 class="mb-3">Manage Trek Staff</h4>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5>Add Trek Staff</h5>
        <form @submit.prevent="createStaff" class="row g-2">
          <div class="col-md-3"><input v-model="newStaff.name" placeholder="Name" class="form-control" required /></div>
          <div class="col-md-3"><input v-model="newStaff.email" type="email" placeholder="Email" class="form-control" required /></div>
          <div class="col-md-3"><input v-model="newStaff.phone" placeholder="Phone" class="form-control" /></div>
          <div class="col-md-3"><input v-model="newStaff.password" type="password" placeholder="Password" class="form-control" required /></div>
          <div class="col-md-12"><button class="btn btn-success mt-2">Create Staff Account</button></div>
        </form>
      </div>
    </div>

    <table class="table table-hover bg-white">
  <thead>
    <tr>
      <th>Name</th>
      <th>Email</th>
      <th>Phone</th>
      <th>Status</th>
      <th>Action</th>
    </tr>
  </thead>

  <tbody>
    <tr v-for="s in staffList" :key="s.id">
      <td>{{ s.name }}</td>
      <td>{{ s.email }}</td>
      <td>{{ s.phone || '-' }}</td>

      <td>
        <span
          :class="s.is_blacklisted ? 'badge bg-danger' : 'badge bg-success'"
        >
          {{ s.is_blacklisted ? 'Blacklisted' : s.staff_status }}
        </span>
      </td>

      <td>
        <button
          class="btn btn-sm"
          :class="s.is_blacklisted ? 'btn-success' : 'btn-danger'"
          @click="toggleBlacklist(s)"
        >
          {{ s.is_blacklisted ? 'Unblacklist' : 'Blacklist' }}
        </button>
      </td>
    </tr>
  </tbody>
</table>
</div>
</template>
