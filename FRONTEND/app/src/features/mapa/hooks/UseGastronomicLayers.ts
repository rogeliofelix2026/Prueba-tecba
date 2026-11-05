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

    useEffect(() => {
        if (!enabled || !map) return

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

            // --- Círculo ---
            const circleFeature = createCirclePolygon([lng, lat], radius * 1000)

            if (map.getSource("search-radius")) {
                // Animar si el radio cambió
                if (prevRadiusRef.current !== radius) {
                    animateCircle(prevRadiusRef.current, radius)
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
                    paint: {
                        "fill-color": "#3498db",
                        "fill-opacity": 0.12,
                    },
                })
                map.addLayer({
                    id: "search-radius-line",
                    type: "line",
                    source: "search-radius",
                    paint: {
                        "line-color": "#3498db",
                        "line-width": 2,
                        "line-opacity": 0.6,
                    },
                })
            }

            prevRadiusRef.current = radius

            // --- Puntos ---
            const sourceId = "gastronomic"
            const layerId = "gastronomic-labels"

            if (map.getLayer(layerId)) map.removeLayer(layerId)
            if (map.getSource(sourceId)) map.removeSource(sourceId)

            if (!data?.features?.length) return

            map.addSource(sourceId, {
                type: "geojson",
                data: data as any,
            })

            map.addLayer({
                id: layerId,
                type: "symbol",
                source: sourceId,
                layout: {
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
            if (popupRef.current) {
                popupRef.current.remove()
                popupRef.current = null
            }
        }
    }, [map, data, lat, lng, radius, enabled])
}