import { useEffect, useRef } from "react"
import type { Map as MapLibreMap, Popup, GeoJSONSource } from "maplibre-gl"
import * as maplibregl from "maplibre-gl"
import type { AnalysisLayers } from "../types"

function createOrientedBoxPolygon(
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

  return corners.map(([dx, dy]) => {
    const rx = dx * cosA - dy * sinA
    const ry = dx * sinA + dy * cosA
    return [lng + rx / metersPerDegLng, lat + ry / metersPerDegLat]
  })
}

export function useAnalysisLayers(
  map: MapLibreMap | null,
  lat: number,
  lng: number,
  analysisLayers: AnalysisLayers | undefined,
  territoryData: any,
  enabled: boolean
) {
  const popupRef = useRef<Popup | null>(null)
  const listenersAddedRef = useRef(false)
  const layersStateRef = useRef<AnalysisLayers | undefined>(analysisLayers)
  layersStateRef.current = analysisLayers

  const territory = territoryData?.territory ?? territoryData
  const plancheta =
    territory?.plancheta ??
    territory?.parcel?.smp ??
    territoryData?.location?.smp ??
    "12"

  const direccion =
    territoryData?.location?.address_input ??
    territoryData?.query?.address_input ??
    territoryData?.address ??
    "Ubicación seleccionada"

  const mixturasArr =
    territory?.urbanism?.mixturas ?? territoryData?.compatibility?.mixturas
  const mixturaUso =
    territory?.mixturaUso ??
    (Array.isArray(mixturasArr) && mixturasArr.length > 0
      ? `Área de Alta Mixtura de Usos del Suelo ${mixturasArr.join(", ")}`
      : "Área de Alta Mixtura de Usos del Suelo 4")

  const mixturaResumen =
    typeof mixturaUso === "string" ? mixturaUso.split(":")[0] : String(mixturaUso)

  const rubroCodigo =
    territory?.rubroCodigo ??
    territoryData?.activity?.code ??
    territoryData?.procedure_type_mapping?.activity_code ??
    "1.5"

  const rubroNombre =
    territoryData?.activity?.name ??
    territoryData?.procedure_type_mapping?.catalog_activity_name ??
    "Alimentación general y gastronomía"

  const esCompatible =
    territoryData?.compatibility?.status != null
      ? territoryData.compatibility.status === "compatible"
      : (territory?.actividadCompatible ?? true)

  // Crear / actualizar fuentes y capas cuando cambia la ubicación o los datos
  useEffect(() => {
    if (!enabled || !map || !analysisLayers) return

    let cancelled = false

    const setupLayers = () => {
      if (cancelled || !map.isStyleLoaded()) return

      const isDesktop = typeof window !== "undefined" && window.innerWidth >= 768
      map.setPadding(
        isDesktop
          ? { left: 240, top: 0, right: 40, bottom: 0 }
          : { left: 0, top: 180, right: 0, bottom: 0 }
      )
      map.easeTo({ center: [lng, lat], duration: 300 })

      // Limpiar raster antiguo si quedó por hot-reload
      if (map.getLayer("analysis-cu-raster-layer")) {
        map.removeLayer("analysis-cu-raster-layer")
      }
      if (map.getSource("analysis-cu-raster-source")) {
        map.removeSource("analysis-cu-raster-source")
      }

      const currentLayers = layersStateRef.current ?? analysisLayers
      const cuVisibility = currentLayers.codigoUrbanistico ? "visible" : "none"
      const parcelaVisibility = currentLayers.parcela ? "visible" : "none"

      // 1. Fuente y capas vectoriales de Código Urbanístico (Zonificación de entorno)
      const cuPolygonCoords = createOrientedBoxPolygon(lng, lat, 130, 130, -18)
      const cuGeoJson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {
              title: "Código Urbanístico",
              mixtura: mixturaResumen,
              rubro: `${rubroCodigo} · ${rubroNombre}`,
              compatible: esCompatible ? "Compatible" : "A verificar",
            },
            geometry: {
              type: "Polygon",
              coordinates: [cuPolygonCoords],
            },
          },
        ],
      }

      const existingCuSource = map.getSource("analysis-cu-source") as
        | GeoJSONSource
        | undefined
      if (existingCuSource) {
        existingCuSource.setData(cuGeoJson)
      } else {
        map.addSource("analysis-cu-source", {
          type: "geojson",
          data: cuGeoJson,
        })
      }

      if (!map.getLayer("analysis-cu-fill")) {
        map.addLayer({
          id: "analysis-cu-fill",
          type: "fill",
          source: "analysis-cu-source",
          layout: { visibility: cuVisibility },
          paint: {
            "fill-color": "#6366f1",
            "fill-opacity": 0.16,
          },
        })
      } else {
        map.setLayoutProperty("analysis-cu-fill", "visibility", cuVisibility)
      }

      if (!map.getLayer("analysis-cu-line")) {
        map.addLayer({
          id: "analysis-cu-line",
          type: "line",
          source: "analysis-cu-source",
          layout: { visibility: cuVisibility },
          paint: {
            "line-color": "#4338ca",
            "line-width": 2.5,
            "line-dasharray": [3, 2],
            "line-opacity": 0.85,
          },
        })
      } else {
        map.setLayoutProperty("analysis-cu-line", "visibility", cuVisibility)
      }

      if (!map.getLayer("analysis-cu-label")) {
        map.addLayer({
          id: "analysis-cu-label",
          type: "symbol",
          source: "analysis-cu-source",
          layout: {
            visibility: cuVisibility,
            "text-field": ["get", "mixtura"],
            "text-size": 12,
            "text-offset": [0, -3.2],
            "text-anchor": "center",
            "text-allow-overlap": false,
          },
          paint: {
            "text-color": "#312e81",
            "text-halo-color": "#ffffff",
            "text-halo-width": 2,
          },
        })
      } else {
        map.setLayoutProperty("analysis-cu-label", "visibility", cuVisibility)
      }

      // 2. Fuente y capas de Parcela (polígono de la parcela consultada)
      const customParcelGeometry = territory?.parcel?.geometry
      const parcelCoords = createOrientedBoxPolygon(lng, lat, 12, 22, -18)
      const parcelGeometry: GeoJSON.Geometry =
        customParcelGeometry &&
        (customParcelGeometry.type === "Polygon" ||
          customParcelGeometry.type === "MultiPolygon")
          ? customParcelGeometry
          : {
              type: "Polygon",
              coordinates: [parcelCoords],
            }

      const parcelaGeoJson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {
              label: `Parcela · Plancheta ${plancheta}`,
              direccion,
              plancheta: String(plancheta),
              estado: esCompatible
                ? "Ubicación compatible"
                : "Ubicación a verificar",
            },
            geometry: parcelGeometry,
          },
        ],
      }

      const existingParcelaSource = map.getSource("analysis-parcela-source") as
        | GeoJSONSource
        | undefined
      if (existingParcelaSource) {
        existingParcelaSource.setData(parcelaGeoJson)
      } else {
        map.addSource("analysis-parcela-source", {
          type: "geojson",
          data: parcelaGeoJson,
        })
      }

      if (!map.getLayer("analysis-parcela-fill")) {
        map.addLayer({
          id: "analysis-parcela-fill",
          type: "fill",
          source: "analysis-parcela-source",
          layout: { visibility: parcelaVisibility },
          paint: {
            "fill-color": "#0d9488",
            "fill-opacity": 0.45,
          },
        })
      } else {
        map.setLayoutProperty(
          "analysis-parcela-fill",
          "visibility",
          parcelaVisibility
        )
      }

      if (!map.getLayer("analysis-parcela-line")) {
        map.addLayer({
          id: "analysis-parcela-line",
          type: "line",
          source: "analysis-parcela-source",
          layout: { visibility: parcelaVisibility },
          paint: {
            "line-color": "#0f766e",
            "line-width": 3,
          },
        })
      } else {
        map.setLayoutProperty(
          "analysis-parcela-line",
          "visibility",
          parcelaVisibility
        )
      }

      if (!map.getLayer("analysis-parcela-label")) {
        map.addLayer({
          id: "analysis-parcela-label",
          type: "symbol",
          source: "analysis-parcela-source",
          layout: {
            visibility: parcelaVisibility,
            "text-field": ["get", "label"],
            "text-size": 12,
            "text-offset": [0, 1.8],
            "text-anchor": "top",
            "text-allow-overlap": true,
          },
          paint: {
            "text-color": "#115e59",
            "text-halo-color": "#ffffff",
            "text-halo-width": 2,
          },
        })
      } else {
        map.setLayoutProperty(
          "analysis-parcela-label",
          "visibility",
          parcelaVisibility
        )
      }

      // 3. Eventos de click para ver detalles de Parcela y Código Urbanístico
      if (!listenersAddedRef.current) {
        map.on("click", "analysis-parcela-fill", (e) => {
          if (!e.features?.length) return
          const props = e.features[0].properties as Record<string, string>
          const html = `
            <div style="font-family: system-ui, sans-serif; font-size: 12.5px; line-height: 1.45; max-width: 240px; color: #0f172a;">
              <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #0d9488; margin-bottom: 2px;">
                Capa: Parcela
              </div>
              <strong style="font-size: 14px;">${props.direccion || "Parcela seleccionada"}</strong>
              <div style="margin-top: 4px;"><b>Plancheta / SMP:</b> ${props.plancheta || "-"}</div>
              <div><b>Estado:</b> ${props.estado || "Compatible"}</div>
            </div>
          `
          if (popupRef.current) popupRef.current.remove()
          popupRef.current = new maplibregl.Popup({
            closeButton: true,
            maxWidth: "260px",
          })
            .setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map)
        })

        map.on("click", "analysis-cu-fill", (e) => {
          if (!e.features?.length) return
          if (map.getLayer("analysis-parcela-fill")) {
            const parcelHits = map.queryRenderedFeatures(e.point, {
              layers: ["analysis-parcela-fill"],
            })
            if (parcelHits.length > 0) return
          }
          const props = e.features[0].properties as Record<string, string>
          const html = `
            <div style="font-family: system-ui, sans-serif; font-size: 12.5px; line-height: 1.45; max-width: 260px; color: #0f172a;">
              <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #4f46e5; margin-bottom: 2px;">
                Capa: Código Urbanístico
              </div>
              <strong style="font-size: 14px;">${props.mixtura || "Zonificación CABA"}</strong>
              <div style="margin-top: 4px;"><b>Rubro:</b> ${props.rubro || "-"}</div>
              <div><b>Condición:</b> ${props.compatible || "Compatible"}</div>
            </div>
          `
          if (popupRef.current) popupRef.current.remove()
          popupRef.current = new maplibregl.Popup({
            closeButton: true,
            maxWidth: "280px",
          })
            .setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map)
        })

        listenersAddedRef.current = true
      }
    }

    if (map.isStyleLoaded()) {
      setupLayers()
    } else {
      map.once("load", setupLayers)
    }

    map.on("styledata", setupLayers)

    return () => {
      cancelled = true
      map.off("styledata", setupLayers)
    }
  }, [
    map,
    lat,
    lng,
    enabled,
    plancheta,
    direccion,
    mixturaResumen,
    rubroCodigo,
    rubroNombre,
    esCompatible,
  ])

  // Efecto dedicado para alternar visibilidad instantáneamente al marcar/desmarcar checkboxes
  useEffect(() => {
    if (!enabled || !map || !analysisLayers || !map.isStyleLoaded()) return

    const parcelaVis = analysisLayers.parcela ? "visible" : "none"
    const cuVis = analysisLayers.codigoUrbanistico ? "visible" : "none"

    ;[
      "analysis-parcela-fill",
      "analysis-parcela-line",
      "analysis-parcela-label",
    ].forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", parcelaVis)
      }
    })

    ;[
      "analysis-cu-fill",
      "analysis-cu-line",
      "analysis-cu-label",
    ].forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", cuVis)
      }
    })

    if (!analysisLayers.parcela && !analysisLayers.codigoUrbanistico && popupRef.current) {
      popupRef.current.remove()
      popupRef.current = null
    }
  }, [
    map,
    enabled,
    analysisLayers?.parcela,
    analysisLayers?.codigoUrbanistico,
  ])
}
