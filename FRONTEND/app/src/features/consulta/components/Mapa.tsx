"use client"

import { useEffect, useState } from "react"
import { MapLoader } from "../../mapa/components/MapLoader"
import { useConsulta } from "../use-consulta"

type MapaProps = {
  height?: string
}

export function Mapa({ height }: MapaProps) {
  const { radius, setRadius, punto } = useConsulta()
  const [visualRadius, setVisualRadius] = useState(radius)

  useEffect(() => {
    setVisualRadius(radius)
  }, [radius])

  return (
    <section className="flex flex-col min-w-0 flex-1 gap-4">
      <div className="w-full overflow-hidden rounded border border-zinc-200 dark:border-zinc-800">
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