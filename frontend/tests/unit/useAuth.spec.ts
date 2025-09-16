import { describe, expect, it, beforeEach } from 'vitest'
import { useAuth } from '../../src/composables/useAuth'

const STORAGE_KEY = 'audio-app-basic-auth'

beforeEach(() => {
  window.localStorage.clear()
})

describe('useAuth composable', () => {
  it('stores credentials in localStorage', () => {
    const auth = useAuth()
    auth.clearCredentials()

    auth.setCredentials('tester', 'secret')
    expect(auth.isAuthenticated.value).toBe(true)
    expect(auth.token.value).toBe(window.btoa('tester:secret'))

    const persisted = window.localStorage.getItem(STORAGE_KEY)
    expect(persisted).toBeTruthy()
  })

  it('clears credentials properly', () => {
    const auth = useAuth()
    auth.setCredentials('tester', 'secret')

    auth.clearCredentials()
    expect(auth.isAuthenticated.value).toBe(false)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
