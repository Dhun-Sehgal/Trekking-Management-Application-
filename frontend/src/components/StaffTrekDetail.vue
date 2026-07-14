<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Api from '../api.js'

const route = useRoute()
const router = useRouter()
const error = ref('')
const trek = ref(null)
const participants = ref([])

const load = async () => {
  error.value = ''
  try {
    const data = await Api.get(`/staff/treks/${route.params.id}/participants`)
    trek.value = data.trek
    participants.value = data.participants
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <div class="container min-vh-90">
    <button class="btn btn-sm btn-outline-secondary mb-3" @click="router.push('/staff')">&larr; Back to My Treks</button>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="trek">
      <h4>Participants for {{ trek.name }}</h4>
      <p class="text-muted">{{ trek.location }} &middot; {{ trek.registered_count }} / {{ trek.total_slots }} registered</p>
      <table class="table bg-white table-hover">
        <thead><tr><th>User</th><th>Status</th><th>Payment</th><th>Booking Date</th></tr></thead>
        <tbody>
          <tr v-for="p in participants" :key="p.id">
            <td>{{ p.user_name }}</td><td>{{ p.status }}</td><td>{{ p.payment_status }}</td>
            <td>{{ p.booking_date && p.booking_date.slice(0,10) }}</td>
          </tr>
          <tr v-if="participants.length===0"><td colspan="4" class="text-muted">No registrations yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
