const BASE = 'http://localhost:5000/api'

function getToken() {
  return localStorage.getItem('token')
}

function setToken(token) {
  if (token) localStorage.setItem('token', token)
}

function clearToken() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

function setUser(user) {
  localStorage.setItem('user', JSON.stringify(user))
}

function getUser() {
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
}

async function request(path, { method = 'GET', body = null, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const resp = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await resp.json()
  } catch (e) {
    data = null
  }

  if (!resp.ok) {
    const message = (data && (data.error || data.message)) || `Request failed (${resp.status})`
    const err = new Error(message)
    err.status = resp.status
    throw err
  }
  return data
}

export default {
  get: (path) => request(path, { method: 'GET' }),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  getToken,
  setToken,
  clearToken,
  setUser,
  getUser,
  BASE,
}
