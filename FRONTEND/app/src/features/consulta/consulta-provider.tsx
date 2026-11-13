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

function detectSurfaceM2(texto: string): number | null {
  const match = texto.match(/(\d+(?:[.,]\d+)?)\s*(?:m2|m²|metros\s*cuadrados|mts2|mts²)/i)
  if (!match) return null
  const val = parseFloat(match[1].replace(",", "."))
  return Number.isFinite(val) && val > 0 ? val : null
}

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
      setError("Por favor, ingresá qué actividad deseás realizar y en qué dirección de la Ciudad.");
      return;
    }

    setError(null);
    setCargando(true);
    setConsultaConfirmada(null);
    setPendiente(null);

    try {
      const parsed = await parseWithGroq(consultaLimpia);

      if (parsed.error) {
        throw new Error(parsed.error);
      }

      if (parsed.actividad && !parsed.direccion) {
        throw new Error(
          `Identificamos la actividad "${parsed.actividad}", pero falta la ubicación. Agregá la calle y altura en tu consulta (ej.: "${consultaLimpia} en Av. Corrientes 2500") o seleccioná el punto en el mapa de abajo.`
        );
      }

      if (!parsed.actividad && parsed.direccion) {
        throw new Error(
          `Identificamos la dirección "${parsed.direccion}", pero falta indicar qué actividad comercial querés realizar (ej.: "Quiero abrir una cafetería en ${parsed.direccion}").`
        );
      }

      if (!parsed.actividad || !parsed.direccion) {
        throw new Error(
          "Falta información para analizar el caso: indicá tanto la actividad comercial como la dirección (calle y altura en CABA)."
        );
      }

      setPendiente({
        query_id: "temp",
        answer: "",
        activity: parsed.actividad,
        address: parsed.direccion,
        surface_m2: parsed.superficie_m2 ?? detectSurfaceM2(consultaLimpia),
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
      const superficieM2 = pendiente.surface_m2 ?? detectSurfaceM2(texto);
      const latGuardada = pendiente.location?.latitude;
      const lngGuardada = pendiente.location?.longitude;

      try {
        const respuesta = await consultarTerritorioConDatos(
          actividad,
          direccion,
          superficieM2
        );
        const lat = respuesta?.location?.latitude || latGuardada;
        const lng = respuesta?.location?.longitude || lngGuardada;

        if (!lat || !lng) {
          throw new Error("No se encontraron coordenadas válidas");
        }

        if (superficieM2 && !respuesta.surface_m2) {
          respuesta.surface_m2 = superficieM2;
        }

        setConsultaConfirmada(respuesta);
        setResultado(respuesta.answer || "Consulta procesada con éxito.");
        setPunto({ lat, lng });
        setPendiente(null);
        setConsultaIniciada(true);
        setPlacesRefreshKey((k) => k + 1);
      } catch (backendErr) {
        if (latGuardada && lngGuardada) {
          setConsultaConfirmada({
            query_id: "mapa",
            activity: actividad,
            address: direccion,
            surface_m2: superficieM2,
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
      const surfaceM2 = detectSurfaceM2(actividadTexto);

      setTexto(`${actividadTexto.trim()} en ${direccion}`);
      setUbicacionMapaModal(null);

      setPendiente({
        query_id: "temp-mapa",
        answer: "",
        activity: actividad,
        address: direccion,
        surface_m2: surfaceM2,
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

    const latPrueba = -34.6037 + Math.random() * 0.01
    const lngPrueba = -58.3816 + Math.random() * 0.01

    setPunto({
      lat: latPrueba,
      lng: lngPrueba,
    })

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
