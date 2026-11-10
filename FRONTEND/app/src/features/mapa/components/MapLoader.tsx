"use client"

import { useEffect, useRef, useState, type ComponentType } from "react"
import type { MapProps, MapLoaderProps } from "../types.js"
import { useGastronomicPlaces } from "../hooks/UseGastronomicPlaces"
import type { Map as MapLibreMap } from "maplibre-gl"
import { useConsulta } from "../../consulta/use-consulta"
import { useGastronomicLayers } from "../hooks/UseGastronomicLayers"
import { useAnalysisLayers } from "../hooks/UseAnalysisLayers"
import { MapStatusBadge } from "./MapStatusBadge"
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
  onLocationClick,
  analysisLayers,
  territoryData,
}: MapLoaderProps) {
  const { radius: committedRadius } = useConsulta()
  const [Mapa, setMapa] = useState<ComponentType<MapProps & { onMapLoad?: (map: MapLibreMap) => void }> | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const mapRef = useRef<MapLibreMap | null>(null)

  const placesLayerEnabled = analysisLayers
    ? withPlaces && analysisLayers.usosSuelo
    : withPlaces

  const places = useGastronomicPlaces(lat, lng, committedRadius)
  const { data, loading, error } = placesLayerEnabled
    ? places
    : { data: null, loading: false, error: null }

  useEffect(() => {
    import("./Map").then((m) => setMapa(() => m.AddressMap))
  }, [])

  useAnalysisLayers(
    mapRef.current,
    lat,
    lng,
    analysisLayers,
    territoryData,
    Boolean(analysisLayers) && mapReady
  )

  useGastronomicLayers(
    mapRef.current,
    data,
    lat,
    lng,
    radius,
    placesLayerEnabled && mapReady
  )

  if (!Mapa) return <div style={{ width: "100%", height }} />

  return (
    <div className="relative w-full" style={{ height }}>
      <Mapa
        lat={lat}
        lng={lng}
        height={height}
        offsetCenterRight={Boolean(analysisLayers)}
        onLocationClick={onLocationClick}
        onMapLoad={(map) => {
          mapRef.current = map
          setMapReady(true)
        }}
      />

      {placesLayerEnabled && (
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
