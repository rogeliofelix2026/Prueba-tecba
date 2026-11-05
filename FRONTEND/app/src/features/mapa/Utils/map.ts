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