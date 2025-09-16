import { computed, inject, provide, readonly, ref } from 'vue'

export type AppMode = 'advanced' | 'basic'

interface AppModeContext {
  mode: Readonly<{ value: AppMode }>
  isBasic: Readonly<{ value: boolean }>
  isAdvanced: Readonly<{ value: boolean }>
  setMode: (mode: AppMode) => void
  toggleMode: () => void
}

const APP_MODE_KEY = Symbol('app-mode')

export function provideAppMode(initialMode: AppMode = 'advanced') {
  const modeRef = ref<AppMode>(initialMode)
  const context: AppModeContext = {
    mode: readonly(modeRef),
    isBasic: computed(() => modeRef.value === 'basic'),
    isAdvanced: computed(() => modeRef.value === 'advanced'),
    setMode: (mode: AppMode) => {
      modeRef.value = mode
    },
    toggleMode: () => {
      modeRef.value = modeRef.value === 'basic' ? 'advanced' : 'basic'
    }
  }
  provide(APP_MODE_KEY, context)
  return context
}

export function useAppMode(): AppModeContext {
  const ctx = inject<AppModeContext>(APP_MODE_KEY)
  if (!ctx) {
    throw new Error('useAppMode must be used within provideAppMode')
  }
  return ctx
}
