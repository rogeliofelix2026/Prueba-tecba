"use client"

import { useEffect, useState } from "react"
import { MapLoader } from "../../mapa/components/MapLoader"
import { useConsulta } from "../use-consulta"

type MapaProps = {
  height?: string
  className?: string
}

export function Mapa({ height = "34rem", className }: MapaProps) {
  const { radius, setRadius, punto } = useConsulta()
  const [visualRadius, setVisualRadius] = useState(radius)

  useEffect(() => {
    setVisualRadius(radius)
  }, [radius])

  return (
    <section className={`flex flex-col min-w-0 flex-1 gap-4 h-full ${className ?? ""}`}>
      <div className="w-full h-full overflow-hidden rounded border border-zinc-200">
        <MapLoader
          lat={punto.lat}
          lng={punto.lng}
          height={height}
          withPlaces
          radius={visualRadius}
          onRadiusChange={setVisualRadius}
          onRadiusCommit={setRadius}
        />
      </div>
    </section>
  )
}