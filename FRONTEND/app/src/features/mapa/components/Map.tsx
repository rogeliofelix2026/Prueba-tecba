"use client"

import { useEffect, useRef } from "react"
import { FullscreenControl, Map, Marker, NavigationControl, ScaleControl, setWorkerUrl } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import type { MapProps } from "../types.js"
import { getAnalysisCameraConfig } from "../Utils/map"

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs")

const DEFAULT_PADDING = { left: 0, top: 0, right: 0, bottom: 0 }

export function AddressMap({ lat, lng, height, onMapLoad, onLocationClick, offsetCenterRight }: MapProps) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markerRef = useRef<Marker | null>(null)
  const onLocationClickRef = useRef(onLocationClick)
  const coordsRef = useRef({ lat, lng })
  coordsRef.current = { lat, lng }

  useEffect(() => {
    onLocationClickRef.current = onLocationClick
  }, [onLocationClick])

  useEffect(() => {
    if (!container.current || mapRef.current) return

    const initial = offsetCenterRight
      ? getAnalysisCameraConfig()
      : { padding: DEFAULT_PADDING, zoom: 15 }

    const map = new Map({
      container: container.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [lng, lat],
      zoom: initial.zoom,
    })

    if (offsetCenterRight) {
      map.setPadding(initial.padding)
      map.jumpTo({ center: [lng, lat], zoom: initial.zoom })
    }

    map.addControl(new NavigationControl(), "top-right")
    map.addControl(new FullscreenControl(), "top-right")
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-left")

    map.on("click", (e) => {
      const { lng: clickLng, lat: clickLat } = e.lngLat
      if (markerRef.current) {
        markerRef.current.setLngLat([clickLng, clickLat])
      } else {
        markerRef.current = new Marker().setLngLat([clickLng, clickLat]).addTo(map)
      }
      onLocationClickRef.current?.(clickLat, clickLng)
    })

    markerRef.current = new Marker().setLngLat([lng, lat]).addTo(map)
    mapRef.current = map
    onMapLoad?.(map)

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!mapRef.current) return

    const syncCamera = () => {
      const map = mapRef.current
      if (!map) return
      const { lat: curLat, lng: curLng } = coordsRef.current

      if (offsetCenterRight) {
        const { padding, zoom } = getAnalysisCameraConfig()
        map.setPadding(padding)
        map.easeTo({ center: [curLng, curLat], zoom, duration: 280 })
      } else {
        map.setPadding(DEFAULT_PADDING)
        map.flyTo({ center: [curLng, curLat], zoom: 15 })
      }
    }

    syncCamera()
    markerRef.current?.setLngLat([lng, lat])

    window.addEventListener("resize", syncCamera)
    return () => window.removeEventListener("resize", syncCamera)
  }, [lat, lng, offsetCenterRight])

  return <div ref={container} style={{ width: "100%", height }} />
}
