"use client"

import { useState } from "react"
import { useConsulta } from "../../features/consulta/use-consulta"
import { MapLoader } from "../../features/mapa/components/MapLoader"
import ResumeCase from "../resumeCase/ResumeCase"
import UbicResume from "../resumeCase/UbicResume"
import BeforeStart from "../beforeStart/beforeStart"
import Nav from "../nav/Nav"
import {
  TimelineSteps,
  FichaYFuenteColumn,
  DudaStepCard,
} from "../recorridoTramite/RecorridoTramite"

export function MainStarted() {
  const { radius, setRadius, punto, consultaConfirmada, volverAConsulta } =
    useConsulta()

  const [visualRadius, setVisualRadius] = useState(radius)
  const [activeStep, setActiveStep] = useState(1)
  const [capas, setCapas] = useState({
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
      {/* Barra superior */}
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
        <div className="pointer-events-auto absolute left-6 top-6 z-10 w-[23rem] max-w-[calc(100vw-3rem)] rounded-xl border border-slate-200/90 bg-white/95 p-5 shadow-md backdrop-blur-xs lg:left-[20%]">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#035C80]">
            Tu consulta
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">
            {tituloConsulta}
          </h1>

          <div className="mt-2 flex items-center gap-2 text-xs font-medium text-slate-800">
            <span className="h-2 w-2 shrink-0 rounded-full bg-slate-900" />
            <span>
              {direccionMostrada.toUpperCase().includes("CABA")
                ? direccionMostrada
                : `${direccionMostrada}, CABA`}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span
              className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                esCompatible
                  ? "border border-emerald-600/80 bg-emerald-50/70 text-emerald-800"
                  : "border border-amber-600/80 bg-amber-50/70 text-amber-800"
              }`}
            >
              {esCompatible ? "Ubicación compatible" : "Ubicación a verificar"}
            </span>
            <span className="text-[11px] text-slate-600">
              Rubro {rubroCodigo} · {rubroNombre}
            </span>
          </div>

          <button
            type="button"
            onClick={volverAConsulta}
            className="mt-3 inline-flex cursor-pointer items-center gap-1 text-xs font-semibold text-[#035C80] hover:underline"
          >
            ← Volver a la consulta
          </button>
        </div>

        {/* Tarjeta flotante derecha: Capas del análisis */}
        <div className="pointer-events-auto absolute bottom-6 right-6 z-10 w-52 rounded-xl border border-slate-200/90 bg-white/95 p-3.5 shadow-md backdrop-blur-xs">
          <p className="text-[11px] font-bold text-slate-800">
            Capas del análisis
          </p>
          <div className="mt-2.5 flex flex-col gap-2 text-xs text-slate-700">
            <label className="flex cursor-pointer select-none items-center gap-2">
              <input
                type="checkbox"
                checked={capas.parcela}
                onChange={(e) =>
                  setCapas((c) => ({ ...c, parcela: e.target.checked }))
                }
                className="h-3.5 w-3.5 rounded accent-[#1D3343]"
              />
              <span className="h-2.5 w-2.5 shrink-0 rounded-xs border border-[#0f766e] bg-[#0d9488]/70" />
              <span>Parcela</span>
            </label>
            <label className="flex cursor-pointer select-none items-center gap-2">
              <input
                type="checkbox"
                checked={capas.codigoUrbanistico}
                onChange={(e) =>
                  setCapas((c) => ({
                    ...c,
                    codigoUrbanistico: e.target.checked,
                  }))
                }
                className="h-3.5 w-3.5 rounded accent-[#1D3343]"
              />
              <span className="h-2.5 w-2.5 shrink-0 rounded-xs border border-[#4338ca] bg-[#6366f1]/70" />
              <span>Código Urbanístico</span>
            </label>
            <label className="flex cursor-pointer select-none items-center gap-2">
              <input
                type="checkbox"
                checked={capas.usosSuelo}
                onChange={(e) =>
                  setCapas((c) => ({ ...c, usosSuelo: e.target.checked }))
                }
                className="h-3.5 w-3.5 rounded accent-[#1D3343]"
              />
              <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-[#1a1a1a]" />
              <span>Usos del suelo</span>
            </label>
          </div>
        </div>
      </section>

      {/* Contenido principal */}
      <section className="mt-10 flex w-full flex-1 flex-col px-4 lg:flex-row lg:items-start lg:justify-center lg:px-0">
        {/* Margen izquierdo (20%) */}
        <div className="hidden lg:block lg:w-[20%]" />

        {/* Columna central (60%) */}
        <div className="flex w-full flex-col gap-10 lg:w-[60%]">
          <ResumeCase />

          <UbicResume data={consultaConfirmada} />

          <BeforeStart data={consultaConfirmada} />

          {/* Sección Recorrido del trámite */}
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

            <div className="relative mt-1 grid grid-cols-1 items-start gap-5 lg:grid-cols-12">
              <div className="lg:col-span-8">
                <TimelineSteps
                  activeStep={activeStep}
                  onSelectStep={setActiveStep}
                />
              </div>

              <div className="lg:col-span-4">
                <FichaYFuenteColumn activeStep={activeStep} />
              </div>

              {/* Tarjeta "¿Tenés una duda?" alineada al tope derecho en desktop */}
              <div className="hidden lg:absolute lg:left-[calc(100%+1.25rem)] lg:top-0 lg:block lg:w-[14rem] xl:w-[16rem]">
                <DudaStepCard activeStep={activeStep} />
              </div>
            </div>

            {/* Tarjeta de dudas en pantallas chicas/medianas */}
            <div className="mt-2 block lg:hidden">
              <DudaStepCard activeStep={activeStep} />
            </div>
          </section>
        </div>

        {/* Margen derecho (20%) */}
        <div className="hidden lg:block lg:w-[20%]" />
      </section>
    </section>
  )
}
