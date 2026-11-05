
import { PlaceFeature } from "../types"

export function buildGastronomicQuery(
  lat: number,
  lon: number,
  radius: number,
  refreshKey: number = 0
) {
  const timeout = 25 + (Date.now() % 10)

  return `
    [out:json][timeout:${timeout}];
    (
      node["amenity"~"^(restaurant|cafe|bar|pub|fast_food|food_court|ice_cream|biergarten)$"](around:${radius},${lat},${lon});
      way["amenity"~"^(restaurant|cafe|bar|pub|fast_food|food_court|ice_cream|biergarten)$"](around:${radius},${lat},${lon});
    );
    out center;
  `
}

export function mapOverpassElements(elements: any[]): PlaceFeature[] {
  return elements
    .filter((el) => el.lat && el.lon)
    .map((el) => {
      const tags = el.tags || {}
      const address = [
        tags["addr:street"],
        tags["addr:housenumber"],
        tags["addr:city"],
      ]
        .filter(Boolean)
        .join(", ")

      return {
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [el.lon, el.lat],
        },
        properties: {
          name: tags.name || "Sin nombre",
          amenity: tags.amenity || "",
          cuisine: tags.cuisine || "",
          opening_hours: tags.opening_hours || "",
          phone: tags.phone || tags["contact:phone"] || "",
          website: tags.website || tags["contact:website"] || "",
          address,
          outdoor_seating: tags.outdoor_seating || "",
          takeaway: tags.takeaway || "",
          delivery: tags.delivery || "",
        },
      }
    })
}