<script setup>
import { ref, onMounted } from 'vue'
import Api from '../api.js'

const error = ref('')
const users = ref([])

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadUsers = () => safeCall(async () => {
  const data = await Api.get('/admin/users')
  users.value = data.users
})

const toggleActive = (u) => safeCall(async () => {
  await Api.put(`/admin/users/${u.id}/deactivate`, { is_active: !u.is_active })
  await loadUsers()
})

const toggleBlacklist = (u) => safeCall(async () => {
  await Api.put(`/admin/users/${u.id}/blacklist`, { is_blacklisted: !u.is_blacklisted })
  await loadUsers()
})

onMounted(loadUsers)
</script>

<template>
  <div class="container min-vh-90">
    <h4 class="mb-3">Manage Trekkers</h4>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <table class="table table-hover bg-white">
      <thead><tr><th>Name</th><th>Email</th><th>Active</th><th>Blacklisted</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.name }}</td><td>{{ u.email }}</td>
          <td>{{ u.is_active ? 'Yes' : 'No' }}</td>
          <td>{{ u.is_blacklisted ? 'Yes' : 'No' }}</td>
          <td class="d-flex gap-1">
            <button class="btn btn-sm" :class="u.is_active ? 'btn-outline-secondary' : 'btn-outline-success'" @click="toggleActive(u)">
              {{ u.is_active ? 'Deactivate' : 'Activate' }}
            </button>
            <button class="btn btn-sm" :class="u.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'" @click="toggleBlacklist(u)">
              {{ u.is_blacklisted ? 'Remove Blacklist' : 'Blacklist' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
