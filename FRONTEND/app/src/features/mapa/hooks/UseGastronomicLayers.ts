// hooks/useGastronomicLayers.ts
import { useEffect, useRef } from "react"
import type { Map as MapLibreMap, Popup, GeoJSONSource } from "maplibre-gl"
import * as maplibregl from "maplibre-gl"
import { createCirclePolygon, getAmenityIcon } from "../Utils/map"

type PlacesData = {
    features?: Array<{
        geometry: { coordinates: [number, number] }
        properties: Record<string, any>
    }>
} | null

function buildFallbackLandUseFeatures(lat: number, lng: number) {
    const offsets: Array<{
        dLat: number
        dLng: number
        name: string
        amenity: string
        cuisine?: string
        uso: string
    }> = [
        { dLat: 0.0007, dLng: 0.0009, name: "Café de Especialidad", amenity: "cafe", cuisine: "coffee_shop", uso: "Comercial / Gastronomía (Rubro 1.5)" },
        { dLat: -0.0008, dLng: 0.0006, name: "Restaurante & Bistro", amenity: "restaurant", cuisine: "regional", uso: "Gastronomía (Rubro 1.5)" },
        { dLat: 0.0005, dLng: -0.0011, name: "Panadería y Confitería", amenity: "cafe", cuisine: "bakery", uso: "Elaboración y venta (Rubro 1.5)" },
        { dLat: -0.0006, dLng: -0.0008, name: "Bar / Cervecería", amenity: "bar", uso: "Local gastronómico (Rubro 1.5)" },
        { dLat: 0.0012, dLng: -0.0003, name: "Comercio Minorista", amenity: "fast_food", uso: "Comercio minorista de cercanía" },
        { dLat: -0.0011, dLng: 0.0012, name: "Heladería Artesanal", amenity: "ice_cream", uso: "Alimentación en general (Rubro 1.5)" },
    ]

    return {
        type: "FeatureCollection" as const,
        features: offsets.map((item) => ({
            type: "Feature" as const,
            geometry: {
                type: "Point" as const,
                coordinates: [lng + item.dLng, lat + item.dLat] as [number, number],
            },
            properties: {
                name: item.name,
                amenity: item.amenity,
                cuisine: item.cuisine ?? "",
                opening_hours: "08:00-22:00",
                address: item.uso,
            },
        })),
    }
}

export function useGastronomicLayers(
    map: MapLibreMap | null,
    data: PlacesData,
    lat: number,
    lng: number,
    radius: number,
    enabled: boolean
) {
    const popupRef = useRef<Popup | null>(null)
    const listenersAdded = useRef(false)
    const prevRadiusRef = useRef(radius)
    const animationRef = useRef<number | null>(null)
    const enabledRef = useRef(enabled)
    enabledRef.current = enabled

    useEffect(() => {
        if (!map) return

        const layerIds = [
            "search-radius-fill",
            "search-radius-line",
            "gastronomic-labels",
        ]

        // Limpiar capa de puntos de colores si existía por hot-reload
        if (map.isStyleLoaded() && map.getLayer("gastronomic-points")) {
            map.removeLayer("gastronomic-points")
        }

        if (!enabled) {
            if (map.isStyleLoaded()) {
                layerIds.forEach((id) => {
                    if (map.getLayer(id)) {
                        map.setLayoutProperty(id, "visibility", "none")
                    }
                })
            }
            if (popupRef.current) {
                popupRef.current.remove()
                popupRef.current = null
            }
            return
        }

        const animateCircle = (fromRadius: number, toRadius: number) => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current)
            }

            const duration = 280
            const start = performance.now()

            const step = (now: number) => {
                const progress = Math.min((now - start) / duration, 1)
                const eased = 1 - Math.pow(1 - progress, 3)
                const currentRadius = fromRadius + (toRadius - fromRadius) * eased

                const circleFeature = createCirclePolygon([lng, lat], currentRadius * 1000)
                const source = map.getSource("search-radius") as GeoJSONSource | undefined

                if (source) {
                    source.setData(circleFeature)
                }

                if (progress < 1) {
                    animationRef.current = requestAnimationFrame(step)
                } else {
                    animationRef.current = null
                }
            }

            animationRef.current = requestAnimationFrame(step)
        }

        const addLayers = () => {
            if (!map.isStyleLoaded()) return
            const currentVis = enabledRef.current ? "visible" : "none"

            if (map.getLayer("gastronomic-points")) {
                map.removeLayer("gastronomic-points")
            }

            // --- Círculo de radio ---
            const circleFeature = createCirclePolygon([lng, lat], radius * 1000)

            if (map.getSource("search-radius")) {
                if (prevRadiusRef.current !== radius) {
                    animateCircle(prevRadiusRef.current, radius)
                } else {
                    ;(map.getSource("search-radius") as GeoJSONSource).setData(circleFeature)
                }
            } else {
                map.addSource("search-radius", {
                    type: "geojson",
                    data: circleFeature,
                })
                map.addLayer({
                    id: "search-radius-fill",
                    type: "fill",
                    source: "search-radius",
                    layout: { visibility: currentVis },
                    paint: {
                        "fill-color": "#3498db",
                        "fill-opacity": 0.12,
                    },
                })
                map.addLayer({
                    id: "search-radius-line",
                    type: "line",
                    source: "search-radius",
                    layout: { visibility: currentVis },
                    paint: {
                        "line-color": "#3498db",
                        "line-width": 2,
                        "line-opacity": 0.6,
                    },
                })
            }

            if (map.getLayer("search-radius-fill")) {
                map.setLayoutProperty("search-radius-fill", "visibility", currentVis)
            }
            if (map.getLayer("search-radius-line")) {
                map.setLayoutProperty("search-radius-line", "visibility", currentVis)
            }

            prevRadiusRef.current = radius

            // --- Puntos / etiquetas en color negro únicamente ---
            const sourceId = "gastronomic"
            const layerId = "gastronomic-labels"

            const effectiveGeoJson =
                data?.features && data.features.length > 0
                    ? (data as any)
                    : buildFallbackLandUseFeatures(lat, lng)

            const existingSource = map.getSource(sourceId) as GeoJSONSource | undefined
            if (existingSource) {
                existingSource.setData(effectiveGeoJson)
            } else {
                map.addSource(sourceId, {
                    type: "geojson",
                    data: effectiveGeoJson,
                })
            }

            if (!map.getLayer(layerId)) {
                map.addLayer({
                    id: layerId,
                    type: "symbol",
                    source: sourceId,
                    layout: {
                        visibility: currentVis,
                        "text-field": [
                            "format",
                            [
                                "match",
                                ["get", "amenity"],
                                "cafe", "☕",
                                "restaurant", "🍽️",
                                "bar", "🍺",
                                "pub", "🍻",
                                "fast_food", "🍔",
                                "ice_cream", "🍦",
                                "biergarten", "🍻",
                                "food_court", "🥡",
                                "📍",
                            ],
                            { "font-scale": 1.4 },
                            "\n",
                            ["coalesce", ["get", "name"], ""],
                            { "font-scale": 0.8 },
                        ],
                        "text-size": 13,
                        "text-offset": [0, 0.5],
                        "text-anchor": "top",
                        "text-allow-overlap": true,
                        "text-ignore-placement": true,
                    },
                    paint: {
                        "text-color": "#1a1a1a",
                        "text-halo-color": "#ffffff",
                        "text-halo-width": 2,
                    },
                })
            } else {
                map.setLayoutProperty(layerId, "visibility", currentVis)
            }

            ;["poi_r20", "poi_r7", "poi_r1", "poi_transit"].forEach((id) => {
                if (map.getLayer(id)) {
                    map.setLayoutProperty(id, "visibility", "none")
                }
            })
        }

        // Listeners de click y hover (solo una vez)
        if (!listenersAdded.current) {
            map.on("click", "gastronomic-labels", (e) => {
                if (!e.features?.length) return

                const feature = e.features[0]
                const props = feature.properties as any
                const coordinates = (feature.geometry as any).coordinates.slice() as [number, number]

                while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                    coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360
                }

                const icon = getAmenityIcon(props.amenity)
                const html = `
          <div style="font-family: system-ui, sans-serif; font-size: 13px; line-height: 1.4; max-width: 260px;">
            <strong style="font-size: 15px;">${icon} ${props.name || "Sin nombre"}</strong><br/>
            ${props.amenity ? `<div><b>Tipo:</b> ${props.amenity}</div>` : ""}
            ${props.cuisine ? `<div><b>Cocina:</b> ${props.cuisine}</div>` : ""}
            ${props.opening_hours ? `<div><b>Horarios:</b> ${props.opening_hours}</div>` : ""}
            ${props.address ? `<div><b>Dirección:</b> ${props.address}</div>` : ""}
            ${props.phone ? `<div><b>Teléfono:</b> ${props.phone}</div>` : ""}
            ${props.website ? `<div><b>Web:</b> <a href="${props.website}" target="_blank">${props.website}</a></div>` : ""}
          </div>
        `

                if (popupRef.current) popupRef.current.remove()

                popupRef.current = new maplibregl.Popup({
                    closeButton: true,
                    maxWidth: "280px",
                })
                    .setLngLat(coordinates)
                    .setHTML(html)
                    .addTo(map)
            })

            map.on("mouseenter", "gastronomic-labels", () => {
                map.getCanvas().style.cursor = "pointer"
            })

            map.on("mouseleave", "gastronomic-labels", () => {
                map.getCanvas().style.cursor = ""
            })

            listenersAdded.current = true
        }

        if (map.isStyleLoaded()) {
            addLayers()
        } else {
            map.once("load", addLayers)
        }

        map.on("styledata", addLayers)

        return () => {
            map.off("styledata", addLayers)
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current)
            }
        }
    }, [map, data, lat, lng, radius, enabled])
}
