import { useEffect, useRef } from "react"
import type { Map as MapLibreMap, Popup, GeoJSONSource, AddLayerObject } from "maplibre-gl"
import * as maplibregl from "maplibre-gl"
import type { AnalysisLayers } from "../types"
import { createOrientedBoxPolygon, getAnalysisCameraConfig } from "../Utils/map"

const PARCELA_LAYER_IDS = [
  "analysis-parcela-fill",
  "analysis-parcela-line",
  "analysis-parcela-label",
] as const

const CU_LAYER_IDS = [
  "analysis-cu-fill",
  "analysis-cu-line",
  "analysis-cu-label",
] as const

function upsertGeoJsonSource(
  map: MapLibreMap,
  id: string,
  data: GeoJSON.FeatureCollection
) {
  const existing = map.getSource(id) as GeoJSONSource | undefined
  if (existing) {
    existing.setData(data)
  } else {
    map.addSource(id, { type: "geojson", data })
  }
}

function upsertLayer(
  map: MapLibreMap,
  layer: AddLayerObject,
  visibility: "visible" | "none"
) {
  if (!map.getLayer(layer.id)) {
    map.addLayer(layer)
  } else {
    map.setLayoutProperty(layer.id, "visibility", visibility)
  }
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

  useEffect(() => {
    if (!enabled || !map || !analysisLayers) return

    let cancelled = false

    const setupLayers = () => {
      if (cancelled || !map.isStyleLoaded()) return

      const { padding, zoom } = getAnalysisCameraConfig()
      map.setPadding(padding)
      map.easeTo({ center: [lng, lat], zoom, duration: 280 })

      const currentLayers = layersStateRef.current ?? analysisLayers
      const cuVisibility = currentLayers.codigoUrbanistico ? "visible" : "none"
      const parcelaVisibility = currentLayers.parcela ? "visible" : "none"

      // 1. Código Urbanístico
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
              coordinates: [createOrientedBoxPolygon(lng, lat, 130, 130, -18)],
            },
          },
        ],
      }

      upsertGeoJsonSource(map, "analysis-cu-source", cuGeoJson)

      upsertLayer(
        map,
        {
          id: "analysis-cu-fill",
          type: "fill",
          source: "analysis-cu-source",
          layout: { visibility: cuVisibility },
          paint: { "fill-color": "#6366f1", "fill-opacity": 0.1 },
        },
        cuVisibility
      )
      map.setPaintProperty("analysis-cu-fill", "fill-opacity", 0.1)

      upsertLayer(
        map,
        {
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
        },
        cuVisibility
      )

      upsertLayer(
        map,
        {
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
        },
        cuVisibility
      )

      // 2. Parcela
      const customParcelGeometry = territory?.parcel?.geometry
      const parcelGeometry: GeoJSON.Geometry =
        customParcelGeometry &&
        (customParcelGeometry.type === "Polygon" ||
          customParcelGeometry.type === "MultiPolygon")
          ? customParcelGeometry
          : {
              type: "Polygon",
              coordinates: [createOrientedBoxPolygon(lng, lat, 12, 22, -18)],
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

      upsertGeoJsonSource(map, "analysis-parcela-source", parcelaGeoJson)

      upsertLayer(
        map,
        {
          id: "analysis-parcela-fill",
          type: "fill",
          source: "analysis-parcela-source",
          layout: { visibility: parcelaVisibility },
          paint: { "fill-color": "#0d9488", "fill-opacity": 0.22 },
        },
        parcelaVisibility
      )
      map.setPaintProperty("analysis-parcela-fill", "fill-opacity", 0.22)

      upsertLayer(
        map,
        {
          id: "analysis-parcela-line",
          type: "line",
          source: "analysis-parcela-source",
          layout: { visibility: parcelaVisibility },
          paint: { "line-color": "#0f766e", "line-width": 3 },
        },
        parcelaVisibility
      )

      upsertLayer(
        map,
        {
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
        },
        parcelaVisibility
      )

      // 3. Eventos de click
      if (!listenersAddedRef.current) {
        const showPopup = (lngLat: maplibregl.LngLat, html: string) => {
          popupRef.current?.remove()
          popupRef.current = new maplibregl.Popup({
            closeButton: true,
            maxWidth: "270px",
          })
            .setLngLat(lngLat)
            .setHTML(html)
            .addTo(map)
        }

        map.on("click", "analysis-parcela-fill", (e) => {
          if (!e.features?.length) return
          const props = e.features[0].properties as Record<string, string>
          showPopup(
            e.lngLat,
            `<div style="font-family: system-ui, sans-serif; font-size: 12.5px; line-height: 1.45; color: #0f172a;">
              <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #0d9488; margin-bottom: 2px;">Capa: Parcela</div>
              <strong style="font-size: 14px;">${props.direccion || "Parcela seleccionada"}</strong>
              <div style="margin-top: 4px;"><b>Plancheta / SMP:</b> ${props.plancheta || "-"}</div>
              <div><b>Estado:</b> ${props.estado || "Compatible"}</div>
            </div>`
          )
        })

        map.on("click", "analysis-cu-fill", (e) => {
          if (!e.features?.length) return
          if (
            map.getLayer("analysis-parcela-fill") &&
            map.queryRenderedFeatures(e.point, {
              layers: ["analysis-parcela-fill"],
            }).length > 0
          ) {
            return
          }
          const props = e.features[0].properties as Record<string, string>
          showPopup(
            e.lngLat,
            `<div style="font-family: system-ui, sans-serif; font-size: 12.5px; line-height: 1.45; color: #0f172a;">
              <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #4f46e5; margin-bottom: 2px;">Capa: Código Urbanístico</div>
              <strong style="font-size: 14px;">${props.mixtura || "Zonificación CABA"}</strong>
              <div style="margin-top: 4px;"><b>Rubro:</b> ${props.rubro || "-"}</div>
              <div><b>Condición:</b> ${props.compatible || "Compatible"}</div>
            </div>`
          )
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

  useEffect(() => {
    if (!enabled || !map || !analysisLayers || !map.isStyleLoaded()) return

    const parcelaVis = analysisLayers.parcela ? "visible" : "none"
    const cuVis = analysisLayers.codigoUrbanistico ? "visible" : "none"

    PARCELA_LAYER_IDS.forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", parcelaVis)
    })

    CU_LAYER_IDS.forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", cuVis)
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
