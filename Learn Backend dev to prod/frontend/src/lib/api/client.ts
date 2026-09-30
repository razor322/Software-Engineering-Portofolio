import axios from 'axios'

const CSRF_COOKIE = 'csrf_token'
const CSRF_HEADER = 'X-CSRF-Token'
const UNSAFE_METHODS = new Set(['post', 'put', 'patch', 'delete'])

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  // the session lives in an HttpOnly cookie, so every request must send it
  withCredentials: true,
})

function readCookie(name: string): string {
  return document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`))
    ?.split('=')[1] ?? ''
}

api.interceptors.request.use((config) => {
  // double-submit CSRF: the backend sets a readable cookie and requires the same
  // value in a header, which another origin cannot read
  if (UNSAFE_METHODS.has(config.method?.toLowerCase() ?? '')) {
    const token = readCookie(CSRF_COOKIE)
    if (token) config.headers.set(CSRF_HEADER, decodeURIComponent(token))
  }
  return config
})
