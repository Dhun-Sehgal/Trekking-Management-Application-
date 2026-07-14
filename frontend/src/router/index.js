import { createRouter, createWebHistory } from 'vue-router'
import Api from '../api.js'

import HomeView from '../components/HomeView.vue'
import LoginView from '../components/LoginView.vue'
import RegisterView from '../components/RegisterView.vue'

import AdminDashboard from '../components/AdminDashboard.vue'
import AdminTreks from '../components/AdminTreks.vue'
import AdminStaff from '../components/AdminStaff.vue'
import AdminUsers from '../components/AdminUsers.vue'

import StaffDashboard from '../components/StaffDashboard.vue'
import StaffTrekDetail from '../components/StaffTrekDetail.vue'

import TrekkerDashboard from '../components/TrekkerDashboard.vue'
import TrekkerHistory from '../components/TrekkerHistory.vue'

const routes = [
  {
    path: '/',
    component: HomeView,
  },

  {
    path: '/login',
    component: LoginView,
  },

  {
    path: '/register',
    component: RegisterView,
  },

  {
    path: '/admin',
    component: AdminDashboard,
    meta: { role: 'admin' },
  },

  {
    path: '/admin/treks',
    component: AdminTreks,
    meta: { role: 'admin' },
  },

  {
    path: '/admin/staff',
    component: AdminStaff,
    meta: { role: 'admin' },
  },

  {
    path: '/admin/users',
    component: AdminUsers,
    meta: { role: 'admin' },
  },

  {
    path: '/staff',
    component: StaffDashboard,
    meta: { role: 'staff' },
  },

  {
    path: '/staff/treks/:id',
    component: StaffTrekDetail,
    props: true,
    meta: { role: 'staff' },
  },

  {
    path: '/trekker',
    component: TrekkerDashboard,
    meta: { role: 'trekker' },
  },

  {
    path: '/trekker/history',
    component: TrekkerHistory,
    meta: { role: 'trekker' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const requiredRole = to.meta?.role

  if (!requiredRole) return true

  const user = Api.getUser()
  const token = Api.getToken()

  if (!user || !token) {
    return '/login'
  }

  if (user.role !== requiredRole) {
    return '/login'
  }

  return true
})

export default router