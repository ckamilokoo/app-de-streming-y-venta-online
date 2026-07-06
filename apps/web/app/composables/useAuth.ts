// Auth mock de desarrollo: usuario en localStorage, token "dev." + base64url(JSON).
// Al integrar Clerk: reemplazar token por el session JWT manteniendo la interfaz.

export interface DevUser {
  id: string
  name: string
  role: 'buyer' | 'streamer'
}

const STORAGE_KEY = 'lc.devUser'

function b64url(json: string): string {
  return btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

export function useAuth() {
  const user = useState<DevUser | null>('auth.user', () => {
    if (import.meta.client) {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) try { return JSON.parse(raw) } catch {}
    }
    return null
  })

  const token = computed(() =>
    user.value ? `dev.${b64url(JSON.stringify(user.value))}` : null,
  )

  function login(name: string, role: DevUser['role']) {
    // id estable derivado del nombre: re-login con mismo nombre = mismo usuario
    const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-')
    user.value = { id: `u_${slug}`, name: name.trim(), role }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user.value))
  }

  function logout() {
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  const isStreamer = computed(() => user.value?.role === 'streamer')

  return { user, token, login, logout, isStreamer }
}
