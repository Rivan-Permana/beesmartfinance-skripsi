import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios"

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "http://localhost:8000/api/v1" : "/api/v1")

const ACCESS_KEY = "bee_access"
const REFRESH_KEY = "bee_refresh"
let sessionVersion = 0
if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === ACCESS_KEY || event.key === REFRESH_KEY || event.key === null) sessionVersion += 1
  })
}

export const tokenStore = {
  get version() {
    return sessionVersion
  },
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set({ access, refresh }: { access: string; refresh?: string }) {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) {
      sessionVersion += 1
      localStorage.setItem(REFRESH_KEY, refresh)
    }
  },
  clear() {
    sessionVersion += 1
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export const api: AxiosInstance = axios.create({ baseURL: BASE_URL })

// Inject access token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  (config as InternalAxiosRequestConfig & { _sessionVersion?: number })._sessionVersion ??= tokenStore.version
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh saat 401 (sekali), lalu retry; gagal -> logout
let refreshing: Promise<string> | null = null
let refreshingFor: string | null = null

async function doRefresh(expectedAccess: string, expectedVersion: number): Promise<string> {
  const refresh = tokenStore.refresh
  if (!refresh) throw new Error("no refresh token")
  const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
    refresh,
  })
  if (tokenStore.version !== expectedVersion || tokenStore.access !== expectedAccess || tokenStore.refresh !== refresh) {
    throw new Error("session changed during refresh")
  }
  tokenStore.set({ access: data.access })
  return data.access
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const isLoginCall = original?.url === "/auth/token/"

    if (status === 401 && original && !original._retry && !isLoginCall) {
      const sentAccess = String(original.headers?.Authorization ?? "").replace(/^Bearer /, "")
      if (!sentAccess || original._sessionVersion !== tokenStore.version) return Promise.reject(error)
      original._retry = true
      if (tokenStore.access !== sentAccess) {
        if (!tokenStore.access) return Promise.reject(error)
        original.headers.Authorization = `Bearer ${tokenStore.access}`
        return api(original)
      }
      if (!refreshing || refreshingFor !== sentAccess) {
        refreshingFor = sentAccess
        refreshing = doRefresh(sentAccess, original._sessionVersion)
      }
      const pendingRefresh = refreshing
      try {
        const access = await pendingRefresh
        if (tokenStore.access !== access) return Promise.reject(error)
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch {
        if (tokenStore.version === original._sessionVersion && tokenStore.access === sentAccess) {
          tokenStore.clear()
          window.location.assign("/login")
        }
      } finally {
        if (refreshing === pendingRefresh) {
          refreshing = null
          refreshingFor = null
        }
      }
    }
    return Promise.reject(error)
  },
)
