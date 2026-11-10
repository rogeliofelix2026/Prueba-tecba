"use client"

import { useId, useState } from "react"

type ConsultaCardProps = {
  data: any
}

export function ConsultaCard({ data }: ConsultaCardProps) {
  const territory = data?.territory ?? data
  const compatibilityStatus = data?.compatibility?.status
  const actividadCompatible =
    compatibilityStatus != null
      ? compatibilityStatus === "compatible"
      : (territory?.actividadCompatible ?? true)

  const plancheta =
    territory?.plancheta ??
    territory?.parcel?.smp ??
    data?.location?.smp ??
    "12"

  const mixturasArr = territory?.urbanism?.mixturas ?? data?.compatibility?.mixturas
  const mixturaUso =
    territory?.mixturaUso ??
    (Array.isArray(mixturasArr) && mixturasArr.length > 0
      ? `Área de Alta Mixtura de Usos del Suelo ${mixturasArr.join(", ")}`
      : "Área de Alta Mixtura de Usos del Suelo 4")

  const rubroCodigo =
    territory?.rubroCodigo ??
    data?.activity?.code ??
    data?.procedure_type_mapping?.activity_code ??
    "1.5"

  const mixturaResumen = typeof mixturaUso === "string"
    ? mixturaUso.split(":")[0]
    : mixturaUso

  const [detailsOpen, setDetailsOpen] = useState(false)
  const detailsId = useId()

  return (
    <article className="w-full rounded-lg border border-slate-200 bg-white p-3 sm:p-4 font-sans shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
        <span className="w-fit shrink-0 rounded-lg border border-sky-700 px-3 py-1.5 text-[10px] sm:text-[11px] font-semibold uppercase tracking-wide text-sky-800">
          Ubicación
        </span>

        <div className="min-w-0 flex-1">
          <h2 className="text-sm sm:text-base font-semibold text-slate-900 leading-snug">
            {actividadCompatible
              ? "La actividad es compatible con esta ubicación"
              : "La actividad no es compatible con esta ubicación"}
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-slate-700 break-words">
            Plancheta {plancheta} · {mixturaResumen} · Rubro {rubroCodigo}
          </p>
        </div>

        <div className="relative shrink-0 self-start sm:self-center sm:ml-auto">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 sm:gap-2 whitespace-nowrap text-left text-xs sm:text-sm font-semibold text-sky-800 hover:text-sky-950"
            aria-expanded={detailsOpen}
            aria-controls={detailsId}
            onClick={() => setDetailsOpen((open) => !open)}
          >
            Ver detalle territorial
            <svg
              className={`h-3.5 w-3.5 sm:h-4 sm:w-4 transition-transform ${detailsOpen ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m6 9 6 6 6-6" />
            </svg>
          </button>

          {detailsOpen && (
            <div
              id={detailsId}
              className="absolute left-0 right-0 sm:left-auto sm:right-0 top-full z-20 mt-2 w-full sm:w-80 max-w-[calc(100vw-2rem)] rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-lg"
            >
              <div className="space-y-3">
                <div>
                  <p className="text-xs font-medium text-slate-500">Plancheta / SMP</p>
                  <p className="mt-1 break-words font-semibold text-slate-900">{plancheta}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500">Mixtura del suelo</p>
                  <p className="mt-1 break-words text-slate-800">{mixturaUso}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500">Rubro</p>
                  <p className="mt-1 break-words font-mono font-semibold text-sky-800">{rubroCodigo}</p>
                </div>
                <a
                  href="https://ciudad3d.buenosaires.gob.ar/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-800 transition-colors hover:bg-sky-100"
                >
                  Consultar en Ciudad 3D
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5h5v5m-1-4-8 8" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" />
                  </svg>
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </article>
  )
}