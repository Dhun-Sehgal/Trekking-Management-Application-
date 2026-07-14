<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Api from '../api.js'

const router = useRouter()
const name = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await Api.post('/auth/register', {
      name: name.value,
      email: email.value,
      phone: phone.value,
      password: password.value,
    })
    success.value = 'Registration successful! Redirecting to login...'
    setTimeout(() => router.push('/login'), 1200)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container min-vh-90 d-flex align-items-center justify-content-center">
    <div class="card shadow-sm" style="max-width: 460px; width: 100%">
      <div class="card-body p-4">
        <h4 class="mb-3 text-center">Trekker Registration</h4>
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>
        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Full Name</label>
            <input v-model="name" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input v-model="email" type="email" class="form-control" required />
          </div>
          <div class="mb-3">
            <label class="form-label">Phone</label>
            <input v-model="phone" class="form-control" />
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="password" type="password" class="form-control" required />
          </div>
          <button class="btn btn-success w-100" :disabled="loading">
            {{ loading ? 'Creating account...' : 'Register' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
