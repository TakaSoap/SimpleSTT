import { computed, reactive } from 'vue'

interface StoredCredentials {
  username: string
  token: string
}

const STORAGE_KEY = 'audio-app-basic-auth'

const state = reactive({
  username: '',
  token: ''
})

function getStorage(): Storage | null {
  if (typeof window === 'undefined') return null
  const storage = window.localStorage
  return storage && typeof storage.getItem === 'function' ? storage : null
}

const storage = getStorage()
const persisted = storage?.getItem(STORAGE_KEY)
if (persisted) {
  try {
    const parsed = JSON.parse(persisted) as StoredCredentials
    state.username = parsed.username
    state.token = parsed.token
  } catch (error) {
    storage?.removeItem(STORAGE_KEY)
  }
}

function persist(): void {
  const storage = getStorage()
  if (!storage) return

  if (state.token) {
    storage.setItem(
      STORAGE_KEY,
      JSON.stringify({ username: state.username, token: state.token })
    )
  } else {
    storage.removeItem(STORAGE_KEY)
  }
}

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(state.token))

  function setCredentials(username: string, password: string): void {
    const token = window.btoa(`${username}:${password}`)
    state.username = username
    state.token = token
    persist()
  }

  function clearCredentials(): void {
    state.username = ''
    state.token = ''
    persist()
  }

  function getAuthHeaders(): Record<string, string> {
    return state.token ? { Authorization: `Basic ${state.token}` } : {}
  }

  return {
    username: computed(() => state.username),
    token: computed(() => state.token),
    isAuthenticated,
    setCredentials,
    clearCredentials,
    getAuthHeaders
  }
}
