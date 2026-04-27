import { computed, ref, watch } from 'vue'
import { usePreferredDark } from '@vueuse/core'

type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'audio-app-theme'
const preferredDark = usePreferredDark()
const envDefault = (import.meta.env.VITE_DEFAULT_THEME as string | undefined)?.toLowerCase() as ThemeMode | undefined

function getStorage(): Storage | null {
  if (typeof window === 'undefined') return null
  const storage = window.localStorage
  return storage && typeof storage.getItem === 'function' ? storage : null
}

function resolveInitialMode(): ThemeMode {
  const storage = getStorage()
  const stored = storage?.getItem(STORAGE_KEY) as ThemeMode | null
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored
  }
  if (envDefault && ['light', 'dark', 'system'].includes(envDefault)) {
    return envDefault
  }
  return 'system'
}

const mode = ref<ThemeMode>(resolveInitialMode())

watch(
  mode,
  (value) => {
    getStorage()?.setItem(STORAGE_KEY, value)
  },
  { immediate: true }
)

const isDark = computed(() => mode.value === 'dark' || (mode.value === 'system' && preferredDark.value))

function syncDocument(themeIsDark: boolean) {
  if (typeof document === 'undefined') return
  const body = document.body
  body.classList.toggle('theme-dark', themeIsDark)
  body.classList.toggle('theme-light', !themeIsDark)
}

watch(
  isDark,
  (value) => {
    syncDocument(value)
  },
  { immediate: true }
)

export function useTheme() {
  function setMode(value: ThemeMode) {
    mode.value = value
  }

  return {
    mode,
    isDark,
    setMode
  }
}
