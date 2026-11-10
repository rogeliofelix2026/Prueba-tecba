"use client"

import { useEffect, useRef } from "react"
import { FullscreenControl, Map, Marker, NavigationControl, ScaleControl, setWorkerUrl } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import type { MapProps } from "../types.js"

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs")

export function AddressMap({ lat, lng, height, onMapLoad, onLocationClick, offsetCenterRight }: MapProps) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markerRef = useRef<Marker | null>(null)
  const onLocationClickRef = useRef(onLocationClick)

  useEffect(() => {
    onLocationClickRef.current = onLocationClick
  }, [onLocationClick])

  // Crear el mapa solo una vez
  useEffect(() => {
    if (!container.current || mapRef.current) return
    const map = new Map({
      container: container.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [lng, lat],
      zoom: 15,
    })

    if (offsetCenterRight) {
      const isDesktop = typeof window !== "undefined" && window.innerWidth >= 768
      map.setPadding(
        isDesktop
          ? { left: 240, top: 0, right: 40, bottom: 0 }
          : { left: 0, top: 180, right: 0, bottom: 0 }
      )
      map.jumpTo({ center: [lng, lat] })
    }

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

      onLocationClickRef.current?.(clickLat, clickLng)
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
    if (offsetCenterRight) {
      const isDesktop = typeof window !== "undefined" && window.innerWidth >= 768
      mapRef.current.setPadding(
        isDesktop
          ? { left: 240, top: 0, right: 40, bottom: 0 }
          : { left: 0, top: 180, right: 0, bottom: 0 }
      )
    }
    mapRef.current.flyTo({ center: [lng, lat], zoom: 15 })
    markerRef.current?.setLngLat([lng, lat])
  }, [lat, lng, offsetCenterRight])

  return <div ref={container} style={{ width: "100%", height }} />
}