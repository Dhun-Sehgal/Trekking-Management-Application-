<script setup>
import { ref, onMounted } from 'vue'
import Api from '../api.js'

const tab = ref('overview')
const error = ref('')
const overview = ref(null)
const bookings = ref([])
const searchQuery = ref('')
const searchType = ref('all')
const searchResults = ref(null)
const reports = ref(null)

const safeCall = async (fn) => {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const loadOverview = () => safeCall(async () => { overview.value = await Api.get('/admin/dashboard') })

const switchTab = async (t) => {
  tab.value = t
  if (t === 'bookings') await loadBookings()
  if (t === 'reports') await loadReports()
}

const loadBookings = () => safeCall(async () => {
  const data = await Api.get('/admin/bookings')
  bookings.value = data.bookings
})

const runSearch = () => safeCall(async () => {
  const params = new URLSearchParams({ q: searchQuery.value, type: searchType.value })
  searchResults.value = await Api.get(`/admin/search?${params.toString()}`)
})

const loadReports = () => safeCall(async () => { reports.value = await Api.get('/admin/reports') })

onMounted(loadOverview)
</script>

<template>
  <div class="container min-vh-90">
    <ul class="nav nav-pills mb-4 gap-2 flex-wrap">
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='overview'}" href="#" @click.prevent="switchTab('overview')">Overview</a></li>
      <li class="nav-item"><router-link class="nav-link" to="/admin/treks">Treks</router-link></li>
      <li class="nav-item"><router-link class="nav-link" to="/admin/staff">Staff</router-link></li>
      <li class="nav-item"><router-link class="nav-link" to="/admin/users">Users</router-link></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='bookings'}" href="#" @click.prevent="switchTab('bookings')">Bookings</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='search'}" href="#" @click.prevent="switchTab('search')">Search</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active: tab==='reports'}" href="#" @click.prevent="switchTab('reports')">Reports</a></li>
    </ul>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="tab==='overview' && overview" class="row g-3">
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.total_treks }}</div><div class="text-muted small">Total Treks</div></div></div></div>
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.total_users }}</div><div class="text-muted small">Total Users</div></div></div></div>
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.total_staff }}</div><div class="text-muted small">Total Staff</div></div></div></div>
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.total_bookings }}</div><div class="text-muted small">Total Bookings</div></div></div></div>
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.open_treks }}</div><div class="text-muted small">Open Treks</div></div></div></div>
      <div class="col-md-3"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ overview.completed_treks }}</div><div class="text-muted small">Completed Treks</div></div></div></div>
    </div>

    <div v-if="tab==='bookings'">
      <table class="table table-hover bg-white">
        <thead><tr><th>User</th><th>Trek</th><th>Location</th><th>Status</th><th>Payment</th><th>Booking Date</th></tr></thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.id">
            <td>{{ b.user_name }}</td><td>{{ b.trek_name }}</td><td>{{ b.trek_location }}</td>
            <td>{{ b.status }}</td><td>{{ b.payment_status }}</td>
            <td>{{ b.booking_date && b.booking_date.slice(0,10) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="tab==='search'">
      <div class="row g-2 mb-4">
        <div class="col-md-6"><input v-model="searchQuery" @keyup.enter="runSearch" placeholder="Search users, staff, or treks..." class="form-control" /></div>
        <div class="col-md-3">
          <select v-model="searchType" class="form-select">
            <option value="all">All</option><option value="users">Users</option>
            <option value="staff">Staff</option><option value="treks">Treks</option>
          </select>
        </div>
        <div class="col-md-3"><button class="btn btn-success w-100" @click="runSearch">Search</button></div>
      </div>

      <div v-if="searchResults">
        <div v-if="searchResults.users" class="mb-4">
          <h6>Users</h6>
          <ul class="list-group">
            <li class="list-group-item" v-for="u in searchResults.users" :key="'u'+u.id">{{ u.name }} - {{ u.email }}</li>
            <li class="list-group-item text-muted" v-if="searchResults.users.length===0">No matches.</li>
          </ul>
        </div>
        <div v-if="searchResults.staff" class="mb-4">
          <h6>Staff</h6>
          <ul class="list-group">
            <li class="list-group-item" v-for="s in searchResults.staff" :key="'s'+s.id">{{ s.name }} - {{ s.email }}</li>
            <li class="list-group-item text-muted" v-if="searchResults.staff.length===0">No matches.</li>
          </ul>
        </div>
        <div v-if="searchResults.treks" class="mb-4">
          <h6>Treks</h6>
          <ul class="list-group">
            <li class="list-group-item" v-for="t in searchResults.treks" :key="'t'+t.id">{{ t.name }} - {{ t.location }}</li>
            <li class="list-group-item text-muted" v-if="searchResults.treks.length===0">No matches.</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="tab==='reports' && reports">
      <div class="row g-3 mb-4">
        <div class="col-md-4"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ reports.total_bookings }}</div><div class="text-muted small">Total Bookings</div></div></div></div>
        <div class="col-md-4"><div class="card stat-card h-100 border-0 shadow-sm"><div class="card-body"><div class="fs-4 fw-bold">{{ reports.total_completed_treks }}</div><div class="text-muted small">Completed Treks</div></div></div></div>
      </div>
      <div class="row g-4">
        <div class="col-md-6">
          <h6>Treks by Status</h6>
          <table class="table bg-white"><tbody>
            <tr v-for="(count, status) in reports.treks_by_status" :key="status"><td>{{ status }}</td><td>{{ count }}</td></tr>
          </tbody></table>
        </div>
        <div class="col-md-6">
          <h6>Treks by Difficulty</h6>
          <table class="table bg-white"><tbody>
            <tr v-for="(count, diff) in reports.treks_by_difficulty" :key="diff"><td>{{ diff }}</td><td>{{ count }}</td></tr>
          </tbody></table>
        </div>
        <div class="col-md-6">
          <h6>Most Popular Treks</h6>
          <table class="table bg-white">
            <thead><tr><th>Trek</th><th>Bookings</th></tr></thead>
            <tbody>
              <tr v-for="p in reports.most_popular_treks" :key="p.name"><td>{{ p.name }}</td><td>{{ p.bookings }}</td></tr>
              <tr v-if="reports.most_popular_treks.length===0"><td colspan="2" class="text-muted">No bookings yet.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
