<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Api from '../api.js'

const router = useRouter()
const user = ref(Api.getUser())

window.addEventListener('auth-changed', () => {
  user.value = Api.getUser()
})

const logout = () => {
  Api.clearToken()
  window.dispatchEvent(new Event('auth-changed'))
  router.push('/login')
}
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm mb-4">
    <div class="container">
      <router-link class="navbar-brand fw-bold" to="/">
        <i class="bi bi-flag-fill me-1"></i> TrekPlatform
      </router-link>
      <div class="d-flex align-items-center gap-3 ms-auto">
        <template v-if="!user">
          <router-link class="btn btn-outline-success btn-sm" to="/login">Login</router-link>
          <router-link class="btn btn-success btn-sm" to="/register">Register</router-link>
        </template>
        <template v-else>
          <span class="text-muted small d-none d-md-inline">
            {{ user.name }} &middot; <span class="text-capitalize">{{ user.role }}</span>
          </span>
          <router-link v-if="user.role === 'admin'" class="btn btn-link btn-sm" to="/admin">Dashboard</router-link>
          <router-link v-if="user.role === 'staff'" class="btn btn-link btn-sm" to="/staff">Dashboard</router-link>
          <router-link v-if="user.role === 'trekker'" class="btn btn-link btn-sm" to="/trekker">Dashboard</router-link>
          <button class="btn btn-outline-danger btn-sm" @click="logout">Logout</button>
        </template>
      </div>
    </div>
  </nav>
</template>
