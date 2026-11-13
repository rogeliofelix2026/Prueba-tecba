"use client"

import { useState } from "react"
import { useConsulta } from "../../features/consulta/use-consulta"
import { MapLoader } from "../../features/mapa/components/MapLoader"
import type { AnalysisLayers } from "../../features/mapa/types"
import ResumeCase from "../resumeCase/ResumeCase"
import UbicResume from "../resumeCase/UbicResume"
import BeforeStart from "../beforeStart/beforeStart"
import Nav from "../nav/Nav"
import {
  TimelineSteps,
  FichaYFuenteColumn,
  DudaStepCard,
} from "../recorridoTramite/RecorridoTramite"

const CAPAS_OPCIONES: Array<{ key: keyof AnalysisLayers; label: string }> = [
  { key: "parcela", label: "Parcela" },
  { key: "codigoUrbanistico", label: "Código Urbanístico" },
  { key: "usosSuelo", label: "Usos del suelo" },
]

export function MainStarted() {
  const { radius, setRadius, punto, consultaConfirmada, volverAConsulta } =
    useConsulta()

  const [visualRadius, setVisualRadius] = useState(radius)
  const [activeStep, setActiveStep] = useState(1)
  const [capas, setCapas] = useState<AnalysisLayers>({
    parcela: true,
    codigoUrbanistico: true,
    usosSuelo: false,
  })

  const rawConfirmada = consultaConfirmada as any

  const actividadInput =
    rawConfirmada?.query?.activity_input ??
    rawConfirmada?.activity?.name ??
    rawConfirmada?.activity ??
    "cafetería"

  const tituloConsulta =
    typeof actividadInput === "string" &&
    actividadInput.toLowerCase().startsWith("abrir")
      ? actividadInput
      : `Abrir una ${String(actividadInput).toLowerCase()}`

  const direccionMostrada =
    rawConfirmada?.location?.address_input ??
    rawConfirmada?.query?.address_input ??
    rawConfirmada?.address ??
    "Av. Corrientes 2500, CABA"

  const rubroCodigo =
    rawConfirmada?.territory?.rubroCodigo ??
    rawConfirmada?.activity?.code ??
    rawConfirmada?.procedure_type_mapping?.activity_code ??
    "1.5"

  const rubroNombre =
    rawConfirmada?.activity?.name ??
    rawConfirmada?.procedure_type_mapping?.catalog_activity_name ??
    "Alimentación general y gastronomía"

  const esCompatible =
    rawConfirmada?.compatibility?.status != null
      ? rawConfirmada.compatibility.status === "compatible"
      : (rawConfirmada?.territory?.actividadCompatible ?? true)

  return (
    <section className="flex min-h-screen w-full flex-col bg-[#FAFAFA] pb-20 text-slate-900">
      <header className="w-full bg-white">
        <Nav />
      </header>

      {/* Mapa con tarjetas flotantes */}
      <section className="relative w-full">
        <MapLoader
          lat={punto.lat}
          lng={punto.lng}
          height="24rem"
          withPlaces
          radius={visualRadius}
          onRadiusChange={setVisualRadius}
          onRadiusCommit={setRadius}
          analysisLayers={capas}
          territoryData={consultaConfirmada}
        />

        {/* Tarjeta flotante izquierda: Tu consulta */}
        <div className="pointer-events-auto absolute left-2.5 top-2.5 z-10 w-[calc(100vw-4.25rem)] max-w-[16.5rem] rounded-lg border border-slate-200/90 bg-white/95 p-2.5 shadow-md backdrop-blur-xs sm:left-4 sm:top-4 sm:max-w-[19.5rem] sm:rounded-xl sm:p-3.5 md:left-6 md:top-6 md:w-[23rem] md:max-w-[calc(100vw-3rem)] md:p-5 lg:left-[8%] xl:left-[12%]">
          <p className="text-[9px] font-semibold uppercase tracking-wider text-[#035C80] md:text-[10px]">
            Tu consulta
          </p>
          <h1 className="mt-0.5 text-sm font-bold leading-snug text-slate-900 sm:text-base md:mt-1 md:text-2xl">
            {tituloConsulta}
          </h1>

          <div className="mt-1 flex items-center gap-1.5 text-[11px] font-medium text-slate-800 md:mt-2 md:gap-2 md:text-xs">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-slate-900 md:h-2 md:w-2" />
            <span className="truncate">
              {direccionMostrada.toUpperCase().includes("CABA")
                ? direccionMostrada
                : `${direccionMostrada}, CABA`}
            </span>
          </div>

          <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 md:mt-3">
            <span
              className={`text-[10px] font-semibold uppercase tracking-wide md:text-[11px] ${
                esCompatible ? "text-emerald-700" : "text-amber-700"
              }`}
            >
              {esCompatible ? "Ubicación compatible" : "Ubicación a verificar"}
            </span>
            <span className="text-[10px] text-slate-400 md:text-[11px]" aria-hidden="true">
              ·
            </span>
            <span className="text-[10px] text-slate-600 md:text-[11px]">
              Rubro {rubroCodigo} · {rubroNombre}
            </span>
          </div>

          <button
            type="button"
            onClick={volverAConsulta}
            className="mt-1.5 inline-flex cursor-pointer items-center gap-1 text-[11px] font-semibold text-[#035C80] hover:underline md:mt-3 md:text-xs"
          >
            ← Volver a la consulta
          </button>
        </div>

        {/* Tarjeta flotante derecha: Capas del análisis */}
        <div className="pointer-events-auto absolute bottom-2.5 right-2.5 z-10 w-38 rounded-lg border border-slate-200/90 bg-white/95 p-2.5 shadow-md backdrop-blur-xs sm:bottom-4 sm:right-4 sm:w-44 sm:p-3 md:bottom-6 md:right-6 md:w-52 md:rounded-xl md:p-3.5">
          <p className="text-[10px] font-bold text-slate-800 md:text-[11px]">
            Capas del análisis
          </p>
          <div className="mt-1.5 flex flex-col gap-1.5 text-[10px] text-slate-700 sm:text-[11px] md:mt-2.5 md:gap-2 md:text-xs">
            {CAPAS_OPCIONES.map(({ key, label }) => (
              <label
                key={key}
                className="flex cursor-pointer select-none items-center gap-1.5 md:gap-2"
              >
                <input
                  type="checkbox"
                  checked={capas[key]}
                  onChange={(e) =>
                    setCapas((prev) => ({ ...prev, [key]: e.target.checked }))
                  }
                  className="h-3 w-3 rounded accent-[#1D3343] md:h-3.5 md:w-3.5"
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </div>
      </section>

      {/* Contenido principal con panel "¿Tenés una duda?" siempre a mano */}
      <section className="mx-auto mt-8 flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 sm:px-6 lg:mt-10 lg:flex-row lg:items-start">
        {/* Columna principal de resultados */}
        <div className="flex min-w-0 flex-1 flex-col gap-8">
          <ResumeCase />
          <UbicResume data={consultaConfirmada} />

          {/* En mobile/tablet: "¿Tenés una duda?" visible arriba a mano antes de los acordeones largos */}
          <div className="block lg:hidden">
            <DudaStepCard
              activeStep={activeStep}
              data={consultaConfirmada}
            />
          </div>

          <BeforeStart data={consultaConfirmada} />

          <section
            id="recorrido-tramite"
            className="flex w-full flex-col gap-4"
            aria-label="Recorrido del trámite"
          >
            <div>
              <h2 className="text-2xl font-semibold text-zinc-900">
                Recorrido del trámite
              </h2>
              <p className="mt-1 text-xs text-slate-600">
                Te mostramos solo lo necesario para el paso actual; el resto se
                abre cuando lo necesites.
              </p>
            </div>

            <div className="mt-1 grid grid-cols-1 items-start gap-5 lg:grid-cols-12">
              <div className="lg:col-span-7">
                <TimelineSteps
                  activeStep={activeStep}
                  onSelectStep={setActiveStep}
                />
              </div>

              <div className="lg:col-span-5">
                <FichaYFuenteColumn
                  activeStep={activeStep}
                  data={consultaConfirmada}
                />
              </div>
            </div>
          </section>
        </div>

        {/* Columna derecha fija (sticky) en desktop: "¿Tenés una duda?" visible desde el inicio y durante todo el scroll */}
        <aside className="hidden lg:sticky lg:top-6 lg:block lg:w-64 xl:w-72 shrink-0">
          <DudaStepCard
            activeStep={activeStep}
            data={consultaConfirmada}
          />
        </aside>
      </section>
    </section>
  )
}
