"use client"

import { useEffect, useRef } from "react"
import { FullscreenControl, Map, Marker, NavigationControl, ScaleControl, setWorkerUrl } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import type { MapProps } from "../types.js"

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs")

export function AddressMap({ lat, lng, height, onMapLoad }: MapProps) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markerRef = useRef<Marker | null>(null)

  // Crear el mapa solo una vez
  useEffect(() => {
    if (!container.current || mapRef.current) return
    const map = new Map({
      container: container.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [lng, lat],
      zoom: 15,
    })

    map.addControl(new NavigationControl(), "top-right")
    map.addControl(new FullscreenControl(), "top-right")
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-left")

    map.on("click", (e) => {
      const { lng: clickLng, lat: clickLat } = e.lngLat

      // Mover el marcador existente o crear uno nuevo
      if (markerRef.current) {
        markerRef.current.setLngLat([clickLng, clickLat])
      } else {
        markerRef.current = new Marker().setLngLat([clickLng, clickLat]).addTo(map)
      }
    })

    // Marcador inicial
    markerRef.current = new Marker().setLngLat([lng, lat]).addTo(map)

    mapRef.current = map
    onMapLoad?.(map)

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Actualizar centro y marcador cuando cambian lat/lng
  useEffect(() => {
    if (!mapRef.current) return
    mapRef.current.flyTo({ center: [lng, lat], zoom: 15 })
    markerRef.current?.setLngLat([lng, lat])
  }, [lat, lng])

  return <div ref={container} style={{ width: "100%", height }} />
}