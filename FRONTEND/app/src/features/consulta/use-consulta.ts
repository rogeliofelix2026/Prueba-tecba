"use client"

import { useContext } from "react"
import { ConsultaContext } from "./consulta-context"

export function useConsulta() {
  const value = useContext(ConsultaContext)
  if (!value) throw new Error("useConsulta tiene que estar dentro de ConsultaProvider")
  return value
}