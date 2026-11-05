"use client"

import { useEffect, useRef, useState, type ComponentType } from "react"
import type { MapProps, MapLoaderProps } from "../types.js"
import { useGastronomicPlaces } from "../hooks/UseGastronomicPlaces"
import type { Map as MapLibreMap } from "maplibre-gl"
import { useConsulta } from "../../consulta/use-consulta"
import { useGastronomicLayers } from "../hooks/UseGastronomicLayers"
import { MapStatusBadge } from "./MapStatusBadge"
import { MapSearchButton } from "./MapSearchButton"
import { MapRadiusControl } from "./MapRadiusControl"
import { MapCoverLoader } from "./MapLoaderCover"

export function MapLoader({
  lat,
  lng,
  height,
  withPlaces = false,
  radius = 1,
  onRadiusChange,
  onRadiusCommit,
}: MapLoaderProps) {
  const { updateMap, radius: committedRadius } = useConsulta()
  const [Mapa, setMapa] = useState<ComponentType<MapProps & { onMapLoad?: (map: MapLibreMap) => void }> | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const mapRef = useRef<MapLibreMap | null>(null)

  const places = useGastronomicPlaces(lat, lng, committedRadius)
  const { data, loading, error } = withPlaces
    ? places
    : { data: null, loading: false, error: null }

  useEffect(() => {
    import("./Map").then((m) => setMapa(() => m.AddressMap))
  }, [])

  useGastronomicLayers(
    mapRef.current,
    data,
    lat,
    lng,
    radius,
    withPlaces && mapReady
  )

  if (!Mapa) return <div style={{ width: "100%", height }} />

  return (
    <div className="relative w-full" style={{ height }}>
      <Mapa
        lat={lat}
        lng={lng}
        height={height}
        onMapLoad={(map) => {
          mapRef.current = map
          setMapReady(true)
        }}
      />

      {withPlaces && (
        <>
          <MapCoverLoader loading={loading} />
          <MapStatusBadge loading={loading} error={error} count={data?.features.length} />

          {onRadiusChange && onRadiusCommit && (
            <MapRadiusControl
              radius={radius}
              onChange={onRadiusChange}
              onCommit={onRadiusCommit}
            />
          )}
        </>
      )}
    </div>
  )
}