import type { Feature, Polygon } from "geojson"

export const amenityIcons: Record<string, string> = {
  cafe: "☕",
  restaurant: "🍽️",
  bar: "🍺",
  pub: "🍻",
  fast_food: "🍔",
  ice_cream: "🍦",
  biergarten: "🍻",
  food_court: "🥡",
}

export function getAmenityIcon(amenity?: string) {
  return amenityIcons[amenity || ""] || "📍"
}

export function createCirclePolygon(center: [number, number], radiusM: number, points = 64): Feature<Polygon> {
  const coords: [number, number][] = []
  const distanceX = radiusM / (111320 * Math.cos((center[1] * Math.PI) / 180))
  const distanceY = radiusM / 110540

  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI)
    const x = distanceX * Math.cos(theta)
    const y = distanceY * Math.sin(theta)
    coords.push([center[0] + x, center[1] + y])
  }
  coords.push(coords[0])

  return {
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [coords] },
    properties: {},
  }
}

export function createOrientedBoxPolygon(
  lng: number,
  lat: number,
  halfWidthMeters: number,
  halfDepthMeters: number,
  angleDeg = -18
): [number, number][] {
  const rad = (angleDeg * Math.PI) / 180
  const cosA = Math.cos(rad)
  const sinA = Math.sin(rad)
  const metersPerDegLat = 111320
  const metersPerDegLng = 111320 * Math.cos((lat * Math.PI) / 180)

  const corners: Array<[number, number]> = [
    [-halfWidthMeters, -halfDepthMeters],
    [halfWidthMeters, -halfDepthMeters],
    [halfWidthMeters, halfDepthMeters],
    [-halfWidthMeters, halfDepthMeters],
    [-halfWidthMeters, -halfDepthMeters],
  ]

  return corners.map(([dx, dy]) => [
    lng + (dx * cosA - dy * sinA) / metersPerDegLng,
    lat + (dx * sinA + dy * cosA) / metersPerDegLat,
  ])
}

export function getAnalysisCameraConfig() {
  const w = typeof window !== "undefined" ? window.innerWidth : 1024
  if (w < 640) {
    return {
      padding: { left: 0, top: 95, right: 0, bottom: 30 },
      zoom: 14.3,
    }
  }
  if (w < 768) {
    return {
      padding: { left: 60, top: 90, right: 20, bottom: 20 },
      zoom: 14.6,
    }
  }
  return {
    padding: { left: 240, top: 0, right: 40, bottom: 0 },
    zoom: 15,
  }
}
