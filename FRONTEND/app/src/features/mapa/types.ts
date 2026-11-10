import { Map } from "maplibre-gl"

export type AnalysisLayers = {
  parcela: boolean
  codigoUrbanistico: boolean
  usosSuelo: boolean
}

export type MapProps = {
  lat: number
  lng: number
  height: string
  onMapLoad?: (map: Map) => void
  onLocationClick?: (lat: number, lng: number) => void
  withPlaces?: boolean
  radius?: number
  offsetCenterRight?: boolean
}

export type MapLoaderProps = MapProps & {
  onRadiusChange?: (radius: number) => void
  onRadiusCommit?: (radius: number) => void
  analysisLayers?: AnalysisLayers
  territoryData?: any
}

export type Coordenadas = {
  lat: number
  lng: number
}

export type PlaceFeature = {
  type: "Feature"
  geometry: {
    type: "Point"
    coordinates: [number, number]
  }
  properties: {
    name: string
    amenity: string
    cuisine: string
    opening_hours: string
    phone: string
    website: string
    address: string
    outdoor_seating: string
    takeaway: string
    delivery: string
  }
}

export type FeatureCollection = {
  type: "FeatureCollection"
  features: PlaceFeature[]
}