<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Api from '../api.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  loading.value = true
  try {
    const data = await Api.post('/auth/login', { email: email.value, password: password.value })
    Api.setToken(data.access_token)
    Api.setUser(data.user)
    window.dispatchEvent(new Event('auth-changed'))

    if (data.user.role === 'admin') router.push('/admin')
    else if (data.user.role === 'staff') router.push('/staff')
    else router.push('/trekker')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container min-vh-90 d-flex align-items-center justify-content-center">
    <div class="card shadow-sm" style="max-width: 420px; width: 100%">
      <div class="card-body p-4">
        <h4 class="mb-3 text-center">Login</h4>
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input v-model="email" type="email" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="password" type="password" class="form-control" required />
          </div>
          <button class="btn btn-success w-100" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        <p class="text-center mt-3 mb-0 small">
          New trekker? <router-link to="/register">Create an account</router-link>
        </p>
        <p class="text-center text-muted small mt-2">
          Admin &amp; Staff accounts are pre-created &mdash; use your issued credentials.
        </p>
      </div>
    </div>
  </div>
</template>
