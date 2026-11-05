"use client"

import { createContext } from "react"
import { ConsultaRespuesta } from "./types";

export type Punto = { lat: number; lng: number }

export type ConsultaContextValue = {
  texto: string
  cargando: boolean
  error: string | null
  resultado: string | null
  punto: Punto
  pendiente: ConsultaRespuesta | null
  consultaConfirmada: ConsultaRespuesta | null
  placesRefreshKey: number
  radius: number
  setPendiente: (pendiente: ConsultaRespuesta | null) => void
  setRadius: (radius: number) => void
  setTexto: (texto: string) => void
  consultar: (e?: React.FormEvent) => void
  editar: (e?: React.FormEvent) => void
  confirmarConsulta: (e?: React.FormEvent) => void
  updateMap: () => void
  volverAConsulta: () => void
  consultaIniciada: boolean
}

export const ConsultaContext = createContext<ConsultaContextValue | null>(null)