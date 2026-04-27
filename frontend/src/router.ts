import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import TranscriptionView from './views/TranscriptionView.vue'
import { useAuth } from './composables/useAuth'

export const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView
  },
  {
    path: '/transcribe',
    name: 'transcribe',
    component: TranscriptionView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to) => {
  const auth = useAuth()
  if (to.meta.requiresAuth && !auth.isAuthenticated.value) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isAuthenticated.value) {
    return { name: 'transcribe' }
  }
  return true
})

export default router
