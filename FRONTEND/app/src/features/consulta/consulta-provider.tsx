"use client"

import { useState } from "react"
import { ConsultaContext, type Punto } from "./consulta-context"
import { ConsultaRespuesta } from "./types"
import { consultarTerritorioConDatos, parseWithGroq } from "../main/actions"

export function ConsultaProvider({ children }: { children: React.ReactNode }) {
  const [texto, setTexto] = useState("")
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultado, setResultado] = useState<string | null>(null)
  const [radius, setRadius] = useState(0.3)

  const COORDS_DEFAULT: Punto = {
    lat: -34.603722,
    lng: -58.381592,
  }
  const [punto, setPunto] = useState<Punto>(COORDS_DEFAULT)

  const [pendiente, setPendiente] = useState<ConsultaRespuesta | null>(null)
  const [consultaConfirmada, setConsultaConfirmada] = useState<ConsultaRespuesta | null>(null)
  const [consultaIniciada, setConsultaIniciada] = useState<boolean>(false)

  const [placesRefreshKey, setPlacesRefreshKey] = useState(0)

  async function onConsultar(e?: React.FormEvent) {
    if (e) e.preventDefault();

    const consultaLimpia = texto.trim();
    if (!consultaLimpia) {
      setError("Por favor, ingresa qué trámite o actividad deseas realizar y la dirección.");
      return;
    }

    setError(null);
    setCargando(true);
    setConsultaConfirmada(null);
    setPendiente(null);

    try {
      // Solo parseamos con Groq (sin llamar al backend todavía)
      const parsed = await parseWithGroq(consultaLimpia);

      if (parsed.error || !parsed.actividad || !parsed.direccion) {
        throw new Error(parsed.error || "No se pudo extraer actividad y dirección");
      }

      // Armamos un pendiente temporal solo con lo extraído
      setPendiente({
        query_id: "temp",
        answer: "",
        activity: parsed.actividad,
        address: parsed.direccion,
        location: {
          latitude: 0,
          longitude: 0,
          smp: null,
        },
        territory: undefined,
        procedures: [],
        evidence: [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ocurrió un error inesperado al realizar la consulta.");
    } finally {
      setCargando(false);
    }
  }

  async function confirmarConsulta() {
    if (!pendiente) return;

    setCargando(true);
    setError(null);

    try {
      const actividad = pendiente.activity ?? "";
      const direccion = pendiente.address ?? "";

      // Ahora sí llamamos al backend
      const respuesta = await consultarTerritorioConDatos(actividad, direccion); // o adaptá consultarTerritorio
      const lat = respuesta?.location?.latitude;
      const lng = respuesta?.location?.longitude;

      if (!lat || !lng) {
        throw new Error("No se encontraron coordenadas válidas");
      }

      setConsultaConfirmada(respuesta);
      setResultado(respuesta.answer || "Consulta procesada con éxito.");
      setPunto({ lat, lng });
      setPendiente(null);
      setConsultaIniciada(true);
      setPlacesRefreshKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al confirmar");
    } finally {
      setCargando(false);
      setPendiente(null);
    }
  }

  async function updateMap() {
    if (!punto?.lat || !punto?.lng) return

    // 1. Cambia las coordenadas (para probar que el mapa se mueve)
    const latPrueba = -34.6037 + Math.random() * 0.01
    const lngPrueba = -58.3816 + Math.random() * 0.01

    setPunto({
      lat: latPrueba,
      lng: lngPrueba,
    })

    // 2. Refresca los locales
    setPlacesRefreshKey((k) => k + 1)

    if (texto.trim()) {
      await onConsultar()
    }

  }



  function editar() {
    setPendiente(null)
  }

  function volverAConsulta() {
    setConsultaIniciada(false)
    setPendiente(null)
  }

  function actualizarMapa() {
    if (!pendiente?.location) return
    setPunto({
      lat: pendiente.location.latitude,
      lng: pendiente.location.longitude,
    })
  }

  function cambiarTexto(value: string) {
    setTexto(value)
    if (error) setError(null)
  }

  return (
    <ConsultaContext.Provider
      value={{
        texto,
        cargando,
        error,
        resultado,
        punto,
        pendiente,
        consultaConfirmada,
        consultaIniciada,
        placesRefreshKey,
        radius,
        setRadius,
        setPendiente,
        setTexto: cambiarTexto,
        consultar: onConsultar,
        editar,
        confirmarConsulta,
        updateMap,
        volverAConsulta,
      }}
    >
      {children}
    </ConsultaContext.Provider>
  )
}