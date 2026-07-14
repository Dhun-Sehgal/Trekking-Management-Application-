<script setup>
import { ref, onMounted } from 'vue'
import Api from '../api.js'
import TrekCard from './TrekCard.vue'

const tab = ref('overview')
const error = ref('')
const success = ref('')

const overview = ref(null)
const treks = ref([])
const filters = ref({ difficulty: '', location: '', max_duration: '' })
const bookings = ref([])
const profile = ref({ name: '', phone: '', password: '' })

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadOverview = () => safeCall(async () => { overview.value = await Api.get('/user/dashboard') })

const switchTab = async (t) => {
  tab.value = t
  error.value = ''
  success.value = ''
  if (t === 'browse') await loadTreks()
  if (t === 'bookings') await loadBookings()
  if (t === 'profile') await loadProfile()
}

const loadTreks = () => safeCall(async () => {
  const params = new URLSearchParams()
  if (filters.value.difficulty) params.set('difficulty', filters.value.difficulty)
  if (filters.value.location) params.set('location', filters.value.location)
  if (filters.value.max_duration) params.set('max_duration', filters.value.max_duration)
  const data = await Api.get(`/treks?${params.toString()}`)
  treks.value = data.treks
})

const bookTrek = (trekId) => safeCall(async () => {
  await Api.post('/user/bookings', { trek_id: trekId })
  success.value = 'Trek booked successfully!'
  await loadTreks()
})

const loadBookings = () => safeCall(async () => {
  const data = await Api.get('/user/bookings')
  bookings.value = data.bookings
})

const cancelBooking = (id) => safeCall(async () => {
  await Api.put(`/user/bookings/${id}/cancel`, {})
  success.value = 'Booking cancelled.'
  await loadBookings()
})

const loadProfile = () => safeCall(async () => {
  const data = await Api.get('/user/profile')
  profile.value = { name: data.user.name, phone: data.user.phone || '', password: '' }
})

const saveProfile = () => safeCall(async () => {
  const payload = { name: profile.value.name, phone: profile.value.phone }
  if (profile.value.password) payload.password = profile.value.password
  const data = await Api.put('/user/profile', payload)
  Api.setUser(data.user)
  window.dispatchEvent(new Event('auth-changed'))
  success.value = 'Profile updated.'
})

onMounted(loadOverview)
</script>

<template>
  <div class="container min-vh-90">
    <ul class="nav nav-pills mb-4 gap-2">
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='overview'}" href="#" @click.prevent="switchTab('overview')">Overview</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='browse'}" href="#" @click.prevent="switchTab('browse')">Browse Treks</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='bookings'}" href="#" @click.prevent="switchTab('bookings')">My Bookings</a></li>
      <li class="nav-item"><router-link class="nav-link" to="/trekker/history">Trekking History</router-link></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='profile'}" href="#" @click.prevent="switchTab('profile')">Profile</a></li>
    </ul>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div v-if="tab==='overview' && overview" class="row g-3">
      <div class="col-md-4">
        <div class="card stat-card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="fs-4 fw-bold">{{ overview.available_treks }}</div>
            <div class="text-muted small">Available Treks</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card stat-card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="fs-4 fw-bold">{{ overview.booked_treks.length }}</div>
            <div class="text-muted small">Active Bookings</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card stat-card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="fs-4 fw-bold">{{ overview.total_bookings }}</div>
            <div class="text-muted small">Total Bookings Ever</div>
          </div>
        </div>
      </div>

      <div class="col-12 mt-4">
        <h5>Your Upcoming Treks</h5>
        <table class="table table-hover bg-white">
          <thead><tr><th>Trek</th><th>Location</th><th>Start Date</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="b in overview.booked_treks" :key="b.id">
              <td>{{ b.trek_name }}</td><td>{{ b.trek_location }}</td>
              <td>{{ b.trek_start_date || '-' }}</td><td>{{ b.status }}</td>
            </tr>
            <tr v-if="overview.booked_treks.length===0"><td colspan="4" class="text-muted">No active bookings yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="tab==='browse'">
      <div class="row g-2 mb-3">
        <div class="col-md-3">
          <select v-model="filters.difficulty" class="form-select" @change="loadTreks">
            <option value="">All Difficulties</option>
            <option>Easy</option><option>Moderate</option><option>Hard</option>
          </select>
        </div>
        <div class="col-md-3">
          <input v-model="filters.location" @keyup.enter="loadTreks" placeholder="Location" class="form-control" />
        </div>
        <div class="col-md-3">
          <input v-model="filters.max_duration" @keyup.enter="loadTreks" placeholder="Max duration (days)" type="number" class="form-control" />
        </div>
        <div class="col-md-3">
          <button class="btn btn-success w-100" @click="loadTreks">Search</button>
        </div>
      </div>
      <div class="row g-3">
        <div class="col-md-4" v-for="t in treks" :key="t.id">
          <TrekCard :trek="t" @book="bookTrek" />
        </div>
        <div v-if="treks.length===0" class="text-muted">No treks match your filters.</div>
      </div>
    </div>

    <div v-if="tab==='bookings'">
      <table class="table table-hover bg-white">
        <thead><tr><th>Trek</th><th>Location</th><th>Booking Date</th><th>Status</th><th>Payment</th><th></th></tr></thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>{{ b.trek_name }}</td><td>{{ b.trek_location }}</td>
            <td>{{ b.booking_date && b.booking_date.slice(0,10) }}</td>
            <td>{{ b.status }}</td><td>{{ b.payment_status }}</td>
            <td>
              <button v-if="b.status==='Booked'" class="btn btn-sm btn-outline-danger" @click="cancelBooking(b.id)">Cancel</button>
            </td>
          </tr>
          <tr v-if="bookings.length===0"><td colspan="6" class="text-muted">No bookings yet.</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="tab==='profile'" class="row">
      <div class="col-md-6">
        <div class="card shadow-sm">
          <div class="card-body">
            <h5 class="mb-3">Edit Profile</h5>
            <form @submit.prevent="saveProfile">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input v-model="profile.name" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">Phone</label>
                <input v-model="profile.phone" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">New Password (optional)</label>
                <input v-model="profile.password" type="password" class="form-control" />
              </div>
              <button class="btn btn-success">Save Changes</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
