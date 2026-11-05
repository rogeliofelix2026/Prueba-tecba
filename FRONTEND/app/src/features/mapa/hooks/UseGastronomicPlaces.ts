import { useEffect, useRef, useState } from "react"
import { buildGastronomicQuery, mapOverpassElements } from "../lib/overpass"
import { getCacheKey, getFromCache, saveToCache } from "../Utils/session-cache"
import { FeatureCollection } from "../types"
import { queryOverpassAction } from "../actionsMap"

export function useGastronomicPlaces(
  lat: number | null,
  lon: number | null,
  radiusKm: number = 1,
  refreshKey: number = 0
) {
  const [data, setData] = useState<FeatureCollection | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const lastQueryRef = useRef<string | null>(null)
  const abortRef = useRef(false)

  useEffect(() => {
    if (lat == null || lon == null) {
      setData(null)
      setLoading(false)
      return
    }

    abortRef.current = false
    setError(null)
    setLoading(true)

    const cacheKey = getCacheKey(lat, lon, radiusKm)

    if (refreshKey === 0) {
      const cached = getFromCache<FeatureCollection>(cacheKey)
      if (cached) {
        setData(cached)
        setLoading(false)
        return
      }
    }

    const query = buildGastronomicQuery(lat, lon, Math.round(radiusKm * 1000), refreshKey)

    // Evitar repetir la misma query
    if (lastQueryRef.current === query) {
      setLoading(false)
      return
    }

    lastQueryRef.current = query

    const fetchWithRetry = async (retries = 3): Promise<any> => {
      for (let i = 0; i < retries; i++) {
        if (abortRef.current) return null
        try {
          return await queryOverpassAction(query)
        } catch (err: any) {
          if (err.message === "duplicate_query" && i < retries - 1) {
            await new Promise(r => setTimeout(r, 1500 * (i + 1)))
            continue
          }
          throw err
        }
      }
      return null
    }

    const fetchData = async () => {
      try {
        const json = await fetchWithRetry()
        if (abortRef.current || !json) return

        const result: FeatureCollection = {
          type: "FeatureCollection",
          features: mapOverpassElements(json.elements || []),
        }

        setData(result)
        if (refreshKey === 0) saveToCache(cacheKey, result)
      } catch (err: any) {
        if (abortRef.current) return
        setError(err.message || "Error al cargar locales")
        setData(null)
      } finally {
        if (!abortRef.current) setLoading(false)
      }
    }

    fetchData()

    return () => {
      abortRef.current = true
      lastQueryRef.current = null
    }
  }, [lat, lon, radiusKm, refreshKey])

  return { data, loading, error }
}