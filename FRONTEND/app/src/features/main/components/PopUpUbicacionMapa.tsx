"use client"

import { useState } from "react"

type PopUpUbicacionMapaProps = {
  direccionDetectada?: string | null
  cargandoDireccion?: boolean
  procesando?: boolean
  onCerrar: () => void
  onConfirmarActividad: (actividadTexto: string) => void
}

export function PopUpUbicacionMapa({
  direccionDetectada,
  cargandoDireccion = false,
  procesando = false,
  onCerrar,
  onConfirmarActividad,
}: PopUpUbicacionMapaProps) {
  const [actividadTexto, setActividadTexto] = useState("")

  const tieneTexto = actividadTexto.trim().length > 0

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!tieneTexto) {
      onCerrar()
      return
    }
    onConfirmarActividad(actividadTexto.trim())
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-[2px]">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-xl sm:p-8">
        {/* Encabezado */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#035C80]">
              Ubicación en el mapa
            </span>
            {cargandoDireccion ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] text-slate-500">
                Obteniendo dirección...
              </span>
            ) : direccionDetectada ? (
              <span className="rounded-full bg-[#EDF4FF] px-2.5 py-0.5 text-[11px] font-medium text-[#035C80]">
                {direccionDetectada}
              </span>
            ) : null}
          </div>

          <button
            type="button"
            onClick={onCerrar}
            disabled={procesando}
            aria-label="Cerrar"
            className="flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-lg bg-[#EFF4F9] text-[#143146] transition-colors hover:bg-[#E1EBF4] disabled:opacity-60"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Título y subtítulo */}
        <h2 className="mt-3 text-2xl font-bold text-[#143146] sm:text-[26px]">
          ¿Qué querés hacer en este lugar?
        </h2>
        <p className="mt-2 text-sm text-[#647887]">
          Indicá la actividad que querés realizar en esta ubicación.
        </p>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="mt-5">
          <input
            type="text"
            autoFocus
            value={actividadTexto}
            onChange={(e) => setActividadTexto(e.target.value)}
            disabled={procesando}
            placeholder="Ej.: abrir una cafetería"
            className="w-full rounded-xl border border-[#DCE5EE] bg-[#F7FAFC] px-4 py-3.5 text-base text-[#143146] placeholder:text-[#8A9BA8] transition-colors focus:border-[#035C80] focus:bg-white focus:outline-none"
          />

          <div className="mt-6 flex items-center justify-end gap-3">
            {tieneTexto && (
              <button
                type="button"
                onClick={onCerrar}
                disabled={procesando}
                className="cursor-pointer rounded-xl px-4 py-3 text-sm font-medium text-[#527084] transition-colors hover:bg-slate-100 disabled:opacity-60"
              >
                Volver al mapa
              </button>
            )}

            <button
              type="submit"
              disabled={procesando || cargandoDireccion}
              className="cursor-pointer rounded-xl bg-[#143146] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1D3E58] disabled:opacity-60"
            >
              {procesando
                ? "Procesando..."
                : tieneTexto
                  ? "Continuar"
                  : "Volver al mapa"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
