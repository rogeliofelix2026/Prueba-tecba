export interface DatosConsulta {
  actividadCompatible: boolean
  plancheta: string
  mixturaUso: string
  rubroCodigo: string
  rubroDescripcion?: string
}

export type ConsultaRespuesta = {
 query_id?: string
  answer?: string
  activity?: string
  address?: string
  location: {
    latitude: number
    longitude: number
    smp?: string | null
  }
  territory?: DatosConsulta
  procedures?: unknown[]
  evidence?: unknown[]
}