import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios"

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "http://localhost:8000/api/v1" : "/api/v1")

const ACCESS_KEY = "bee_access"
const REFRESH_KEY = "bee_refresh"

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set({ access, refresh }: { access: string; refresh?: string }) {
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export const api: AxiosInstance = axios.create({ baseURL: BASE_URL })

// Inject access token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh saat 401 (sekali), lalu retry; gagal -> logout
let refreshing: Promise<string> | null = null

async function doRefresh(): Promise<string> {
  const refresh = tokenStore.refresh
  if (!refresh) throw new Error("no refresh token")
  const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
    refresh,
  })
  tokenStore.set({ access: data.access })
  return data.access
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const isAuthCall = original?.url?.includes("/auth/")

    if (status === 401 && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        refreshing = refreshing ?? doRefresh()
        const access = await refreshing
        refreshing = null
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch {
        refreshing = null
        tokenStore.clear()
        window.location.assign("/login")
      }
    }
    return Promise.reject(error)
  },
)
