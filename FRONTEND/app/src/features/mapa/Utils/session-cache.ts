const CACHE_PREFIX = "gastro-places-"
const CACHE_DURATION_MS = 10 * 60 * 1000

export function getCacheKey(lat: number, lon: number, radiusKm: number) {
  return `${CACHE_PREFIX}${lat.toFixed(4)}_${lon.toFixed(4)}_${radiusKm}`
}

export function getFromCache<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const { data, timestamp } = JSON.parse(raw)
    if (Date.now() - timestamp > CACHE_DURATION_MS) {
      sessionStorage.removeItem(key)
      return null
    }
    return data as T
  } catch {
    return null
  }
}

export function saveToCache(key: string, data: unknown) {
  try {
    sessionStorage.setItem(key, JSON.stringify({ data, timestamp: Date.now() }))
  } catch {
    // ignore
  }
}