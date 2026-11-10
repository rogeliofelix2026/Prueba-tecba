"use client"

import { useState } from "react"
import { ConsultaContext, type Punto, type UbicacionMapaModal } from "./consulta-context"
import { ConsultaRespuesta } from "./types"
import {
  consultarTerritorioConDatos,
  extraerActividadDesdeTexto,
  parseWithGroq,
  reverseGeocodeCoordenadas,
} from "../main/actions"

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
  const [ubicacionMapaModal, setUbicacionMapaModal] = useState<UbicacionMapaModal | null>(null)

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
      const latGuardada = pendiente.location?.latitude;
      const lngGuardada = pendiente.location?.longitude;

      try {
        // Ahora sí llamamos al backend
        const respuesta = await consultarTerritorioConDatos(actividad, direccion);
        const lat = respuesta?.location?.latitude || latGuardada;
        const lng = respuesta?.location?.longitude || lngGuardada;

        if (!lat || !lng) {
          throw new Error("No se encontraron coordenadas válidas");
        }

        setConsultaConfirmada(respuesta);
        setResultado(respuesta.answer || "Consulta procesada con éxito.");
        setPunto({ lat, lng });
        setPendiente(null);
        setConsultaIniciada(true);
        setPlacesRefreshKey((k) => k + 1);
      } catch (backendErr) {
        // Si la ubicación vino directamente de un clic en el mapa (tiene coordenadas válidas),
        // permitimos avanzar con esas coordenadas aunque la geocodificación textual falle
        if (latGuardada && lngGuardada) {
          setConsultaConfirmada({
            query_id: "mapa",
            activity: actividad,
            address: direccion,
            location: {
              latitude: latGuardada,
              longitude: lngGuardada,
              smp: null,
            },
          });
          setResultado("Consulta procesada con ubicación seleccionada en el mapa.");
          setPunto({ lat: latGuardada, lng: lngGuardada });
          setPendiente(null);
          setConsultaIniciada(true);
          setPlacesRefreshKey((k) => k + 1);
        } else {
          throw backendErr;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al confirmar");
    } finally {
      setCargando(false);
      setPendiente(null);
    }
  }

  async function seleccionarUbicacionEnMapa(lat: number, lng: number) {
    setPunto({ lat, lng });
    setError(null);
    setUbicacionMapaModal({
      lat,
      lng,
      direccion: null,
      cargandoDireccion: true,
    });

    const direccion = await reverseGeocodeCoordenadas(lat, lng);
    setUbicacionMapaModal((actual) => {
      if (!actual || actual.lat !== lat || actual.lng !== lng) return actual;
      return {
        ...actual,
        direccion,
        cargandoDireccion: false,
      };
    });
  }

  function cerrarUbicacionMapaModal() {
    setUbicacionMapaModal(null);
  }

  async function confirmarActividadEnMapa(actividadTexto: string) {
    if (!ubicacionMapaModal) return;

    setCargando(true);
    setError(null);

    try {
      const { lat, lng, direccion: dirYaCalculada } = ubicacionMapaModal;
      const [actividadExtraida, direccionFinal] = await Promise.all([
        extraerActividadDesdeTexto(actividadTexto),
        dirYaCalculada
          ? Promise.resolve(dirYaCalculada)
          : reverseGeocodeCoordenadas(lat, lng),
      ]);

      const actividad = actividadExtraida || actividadTexto.trim();
      const direccion = direccionFinal || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;

      setTexto(`${actividadTexto.trim()} en ${direccion}`);
      setUbicacionMapaModal(null);

      setPendiente({
        query_id: "temp-mapa",
        answer: "",
        activity: actividad,
        address: direccion,
        location: {
          latitude: lat,
          longitude: lng,
          smp: null,
        },
        territory: undefined,
        procedures: [],
        evidence: [],
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo procesar la ubicación seleccionada."
      );
    } finally {
      setCargando(false);
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
        ubicacionMapaModal,
        placesRefreshKey,
        radius,
        setRadius,
        setPendiente,
        setTexto: cambiarTexto,
        consultar: onConsultar,
        editar,
        confirmarConsulta,
        seleccionarUbicacionEnMapa,
        cerrarUbicacionMapaModal,
        confirmarActividadEnMapa,
        updateMap,
        volverAConsulta,
      }}
    >
      {children}
    </ConsultaContext.Provider>
  )
}