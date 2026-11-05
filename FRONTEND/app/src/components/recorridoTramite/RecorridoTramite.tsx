"use client"

import { useState } from "react"
import { preguntarSobrePaso } from "../../features/main/actions"

type StepItem = {
  number: number
  title: string
  description: string
  summaryTag: string
  tags: { label: string; variant?: "default" | "success" }[]
  queNecesitasTitle: string
  queNecesitasItems: string[]
  queObtenesTitle: string
  queObtenesDesc: string
  fuenteTitulo: string
  fuenteDesc: string
  fuenteUrl: string
  evidenciaNormativa: { titulo: string; detalle: string; url?: string }[]
}

const STEPS: StepItem[] = [
  {
    number: 1,
    title: "Iniciá tu solicitud",
    description:
      'Ingresá a SSIT con miBA y seleccioná "Nueva Autorización de Actividad Económica".',
    summaryTag: "SSIT · miBA nivel 3",
    tags: [
      { label: "SSIT" },
      { label: "MIBA NIVEL 3" },
      { label: "ONLINE" },
      { label: "GRATUITO", variant: "success" },
    ],
    queNecesitasTitle: "Requisitos y datos previos",
    queNecesitasItems: [
      "Contar con usuario y clave miBA con validación de identidad nivel 3.",
      "Tener habilitado el servicio SSIT de la Agencia Gubernamental de Control (AGC).",
      "Conocer el rubro de la actividad y los datos preliminares del establecimiento.",
    ],
    queObtenesTitle: "Solicitud creada para continuar",
    queObtenesDesc:
      "Se abre el expediente digital en SSIT bajo la modalidad Nueva Autorización de Actividad Económica para cargar titular y ubicación.",
    fuenteTitulo: "Habilitación de actividad económica",
    fuenteDesc: "Página oficial del GCBA para iniciar y entender este trámite.",
    fuenteUrl: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    evidenciaNormativa: [
      {
        titulo: "Resolución 96/AGC/25 — Anexo II",
        detalle: "Usos de Actividad Económica y Tipos de Trámites (DGHP / AGC).",
        url: "https://www.boletinoficial.buenosaires.gob.ar/normativaba/norma/781370",
      },
      {
        titulo: "Portal SSIT — Agencia Gubernamental de Control",
        detalle: " Guía oficial de inicio del trámite online con usuario miBA nivel 3.",
        url: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
      },
    ],
  },
  {
    number: 2,
    title: "Agregá los datos de la persona titular o firmante",
    description: "Ingresá el CUIT. Puede ser una persona física o jurídica.",
    summaryTag: "CUIT · titular/firmante",
    tags: [
      { label: "CUIT" },
      { label: "PERSONA FÍSICA O JURÍDICA" },
      { label: "SSIT" },
    ],
    queNecesitasTitle: "Datos de identificación fiscal y representación",
    queNecesitasItems: [
      "CUIT de la persona física o jurídica titular de la actividad económica.",
      "Datos del firmante o apoderado en caso de corresponder a una persona jurídica.",
      "Domicilio constituido y correo electrónico de notificación.",
    ],
    queObtenesTitle: "Titularidad vinculada al trámite",
    queObtenesDesc:
      "La persona solicitante o firmante queda registrada como responsable de la solicitud en SSIT.",
    fuenteTitulo: "Identificación del titular en SSIT",
    fuenteDesc: "Requisitos oficiales sobre titularidad y representación del trámite.",
    fuenteUrl: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    evidenciaNormativa: [
      {
        titulo: "Procedimiento general DGHP — Paso 2",
        detalle: "Declaración de CUIT de persona física o jurídica solicitante.",
      },
    ],
  },
  {
    number: 3,
    title: "Declará la ubicación del establecimiento",
    description:
      "Ingresá partida o matriz, datos catastrales, ubicación especial y contacto.",
    summaryTag: "Genera Número de Trámite + Código de Seguridad",
    tags: [
      { label: "PARTIDA / MATRIZ" },
      { label: "DATOS CATASTRALES" },
      { label: "ANEXO TÉCNICO" },
    ],
    queNecesitasTitle: "Datos catastrales y del establecimiento",
    queNecesitasItems: [
      "Dirección oficial y tipo de ubicación en CABA.",
      "Número de partida o partida matriz y nomenclatura catastral (Sección-Manzana-Parcela).",
      "Ubicación especial (si aplica) y datos de contacto del local.",
    ],
    queObtenesTitle: "Número de Trámite + Código de Seguridad",
    queObtenesDesc:
      "Al guardar la solicitud se generan el Número de Trámite y el Código de Seguridad, indispensables para que el profesional confeccione el Anexo Técnico y lo certifique en su Consejo Profesional.",
    fuenteTitulo: "Declaración de ubicación y Anexo Técnico",
    fuenteDesc: "Instructivo oficial de carga parcelaria y generación de código para profesionales.",
    fuenteUrl: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    evidenciaNormativa: [
      {
        titulo: "Código Urbanístico CABA — Cuadro de Usos",
        detalle: "Verificación de mixtura de uso del suelo y compatibilidad parcelaria.",
      },
      {
        titulo: "Anexo Técnico Profesional",
        detalle: "Requiere Número de Trámite y Código de Seguridad emitidos al guardar la ubicación.",
      },
    ],
  },
  {
    number: 4,
    title: "Solicitá el Certificado de Aptitud Ambiental",
    description: "Continuá con Impacto Ambiental para obtener el CAA.",
    summaryTag: "CAA",
    tags: [
      { label: "IMPACTO AMBIENTAL" },
      { label: "CAA" },
      { label: "OBLIGATORIO" },
    ],
    queNecesitasTitle: "Formulario de categorización ambiental",
    queNecesitasItems: [
      "Datos de la unidad de uso, superficie y rubros declarados.",
      "Intervención profesional según la categorización ambiental de la actividad.",
    ],
    queObtenesTitle: "Certificado de Aptitud Ambiental (CAA)",
    queObtenesDesc:
      "Constancia ambiental emitida para incorporar a la presentación técnica de la habilitación.",
    fuenteTitulo: "Certificado de Aptitud Ambiental (CAA)",
    fuenteDesc: "Servicio oficial de Impacto Ambiental del GCBA vinculado al trámite.",
    fuenteUrl: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    evidenciaNormativa: [
      {
        titulo: "Normativa de Impacto Ambiental GCBA",
        detalle: "Requisito obligatorio para la autorización de actividades económicas.",
      },
    ],
  },
  {
    number: 5,
    title: "Esperá la evaluación y el resultado",
    description: "La Dirección General de Habilitaciones y Permisos evalúa el caso.",
    summaryTag: "Aprobar · observar · rechazar · librar al uso",
    tags: [
      { label: "DGHP" },
      { label: "EVALUACIÓN TÉCNICA" },
      { label: "QR / LIBRO DIGITAL" },
    ],
    queNecesitasTitle: "Documentación técnica presentada",
    queNecesitasItems: [
      "Formulario de conformación de la unidad de uso y Anexo Técnico firmado.",
      "Certificado de Aptitud Ambiental (CAA) y documentación adicional si corresponde.",
    ],
    queObtenesTitle: "Resolución de DGHP y oblea QR",
    queObtenesDesc:
      "La DGHP puede aprobar, observar, rechazar o librar al uso (enviando oblea con código QR y habilitando el Libro de Registro de Inspecciones Digital con miBA nivel 3).",
    fuenteTitulo: "Evaluación y librado al uso — DGHP",
    fuenteDesc: "Alcance del librado al uso, código QR y Libro de Inspecciones Digital.",
    fuenteUrl: "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica",
    evidenciaNormativa: [
      {
        titulo: "Criterio oficial de Librado al Uso",
        detalle: "Que el comercio esté librado al uso permite operar pero no equivale por sí mismo al acto final de habilitación.",
      },
    ],
  },
]

export function TimelineSteps({
  activeStep,
  onSelectStep,
}: {
  activeStep: number
  onSelectStep: (step: number) => void
}) {
  const [openNecesitas, setOpenNecesitas] = useState<Record<number, boolean>>({})
  const [openObtenes, setOpenObtenes] = useState<Record<number, boolean>>({})

  return (
    <div className="relative flex flex-col gap-3.5">
      {/* Línea vertical conectora */}
      <div
        className="pointer-events-none absolute bottom-8 left-[13px] top-6 w-px bg-slate-200"
        aria-hidden="true"
      />

      {STEPS.map((step) => {
        const isActive = activeStep === step.number
        const isNecesitasOpen = !!openNecesitas[step.number]
        const isObtenesOpen = !!openObtenes[step.number]

        return (
          <div key={step.number} className="relative flex items-start gap-3.5">
            {/* Círculo numerado */}
            <button
              type="button"
              onClick={() => onSelectStep(step.number)}
              className={`relative z-10 mt-3.5 flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-full text-xs font-bold transition-colors ${
                isActive
                  ? "bg-[#E08A00] text-white shadow-xs"
                  : "border border-slate-200 bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
              aria-label={`Paso ${step.number}`}
            >
              {step.number}
            </button>

            {/* Tarjeta del paso */}
            <div
              className={`min-w-0 flex-1 rounded-xl bg-white transition-all ${
                isActive
                  ? "border border-[#E5A93C] p-4 shadow-xs"
                  : "border border-slate-200 px-4 py-3.5 hover:border-slate-300"
              }`}
            >
              {/* Encabezado del paso */}
              <button
                type="button"
                onClick={() => onSelectStep(step.number)}
                className="flex w-full cursor-pointer items-start justify-between gap-3 text-left"
              >
                <div className="flex flex-wrap items-center gap-2.5">
                  <span
                    className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                      isActive
                        ? "border border-[#E5A93C] bg-[#FFF8EB] text-[#9A6700]"
                        : "border border-slate-200 bg-slate-50 text-slate-500"
                    }`}
                  >
                    {isActive ? "Ahora" : "Después"}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {step.title}
                  </h3>
                </div>

                <span className="flex h-5 w-5 shrink-0 items-center justify-center text-base font-medium text-slate-700">
                  +
                </span>
              </button>

              {/* Descripción */}
              <p className="mt-2 text-xs leading-relaxed text-slate-600">
                {step.description}
              </p>

              {!isActive ? (
                <p className="mt-1.5 text-[11px] font-medium text-[#035C80]">
                  {step.summaryTag}
                </p>
              ) : (
                <div className="mt-3.5 space-y-3">
                  {/* Etiquetas */}
                  <div className="flex flex-wrap gap-2">
                    {step.tags.map((tag) => (
                      <span
                        key={tag.label}
                        className={`rounded-md px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                          tag.variant === "success"
                            ? "border border-emerald-600/70 bg-emerald-50/50 text-emerald-800"
                            : "border border-slate-200 bg-white text-slate-700"
                        }`}
                      >
                        {tag.label}
                      </span>
                    ))}
                  </div>

                  {/* Sub-acordeón: QUÉ NECESITÁS */}
                  <div className="rounded-lg border border-slate-200 bg-slate-50/50">
                    <button
                      type="button"
                      onClick={() =>
                        setOpenNecesitas((prev) => ({
                          ...prev,
                          [step.number]: !prev[step.number],
                        }))
                      }
                      className="flex w-full cursor-pointer items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-slate-100/70"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="rounded border border-slate-300 bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-700">
                          Qué necesitás
                        </span>
                        <span className="text-xs font-semibold text-slate-800">
                          {step.queNecesitasTitle}
                        </span>
                      </div>
                      <span className="text-base font-medium text-slate-700">
                        {isNecesitasOpen ? "−" : "+"}
                      </span>
                    </button>

                    {isNecesitasOpen && (
                      <ul className="space-y-1.5 border-t border-slate-200/80 bg-white px-4 py-3 text-xs text-slate-600">
                        {step.queNecesitasItems.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#035C80]" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Sub-acordeón: QUÉ OBTENÉS */}
                  <div className="rounded-lg border border-slate-200 bg-slate-50/50">
                    <button
                      type="button"
                      onClick={() =>
                        setOpenObtenes((prev) => ({
                          ...prev,
                          [step.number]: !prev[step.number],
                        }))
                      }
                      className="flex w-full cursor-pointer items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-slate-100/70"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="rounded border border-sky-700/60 bg-sky-50/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#035C80]">
                          Qué obtenés
                        </span>
                        <span className="text-xs font-semibold text-slate-800">
                          {step.queObtenesTitle}
                        </span>
                      </div>
                      <span className="text-base font-medium text-slate-700">
                        {isObtenesOpen ? "−" : "+"}
                      </span>
                    </button>

                    {isObtenesOpen && (
                      <div className="border-t border-slate-200/80 bg-white px-4 py-3 text-xs leading-relaxed text-slate-600">
                        {step.queObtenesDesc}
                      </div>
                    )}
                  </div>

                  {/* Botones de acción */}
                  <div className="flex flex-wrap items-center gap-4 pt-1">
                    <a
                      href="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center rounded-lg bg-[#1D3343] px-4 py-2.5 text-xs font-semibold text-white transition-colors hover:bg-[#142430]"
                    >
                      Iniciar trámite
                    </a>
                    <a
                      href={step.fuenteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-semibold text-[#035C80] hover:underline"
                    >
                      Ver fuente oficial
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function FichaYFuenteColumn({ activeStep }: { activeStep: number }) {
  const [evidenciaOpen, setEvidenciaOpen] = useState(false)
  const step = STEPS.find((s) => s.number === activeStep) ?? STEPS[0]

  return (
    <div className="flex flex-col gap-4">
      {/* Ficha del trámite */}
      <div className="rounded-xl bg-[#EDF4FF] p-4">
        <h3 className="text-sm font-bold text-slate-900">Ficha del trámite</h3>
        <p className="mt-1 text-xs font-semibold text-slate-800">
          Habilitación de Actividad Económica
        </p>
        <div className="mt-2 space-y-0.5 text-[11px] leading-relaxed text-slate-600">
          <p>Agencia Gubernamental de Control</p>
          <p>Dirección General de Habilitaciones y Permisos</p>
          <p>Online · SSIT · miBA nivel 3</p>
          <p>Gratuito · tiempo no informado</p>
        </div>
      </div>

      {/* Fuente del paso activo */}
      <div className="rounded-xl border border-[#E5A93C] bg-white p-4 shadow-xs">
        <span className="inline-block rounded-md border border-[#E5A93C] bg-[#FFF8EB] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-[#9A6700]">
          Fuente del paso {step.number}
        </span>

        <h4 className="mt-2.5 text-xs font-bold text-slate-900">
          {step.fuenteTitulo}
        </h4>
        <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
          {step.fuenteDesc}
        </p>

        <a
          href={step.fuenteUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2.5 inline-block text-xs font-semibold text-[#035C80] hover:underline"
        >
          Abrir fuente oficial
        </a>

        {/* Bloque Evidencia */}
        <div className="mt-3.5 rounded-lg bg-[#F1F5F9] p-3">
          <p className="text-[10px] font-medium text-slate-500">Qué respalda</p>
          <button
            type="button"
            onClick={() => setEvidenciaOpen((v) => !v)}
            className="mt-1 flex w-full cursor-pointer items-center justify-between gap-2 text-left"
          >
            <div className="flex items-center gap-2">
              <svg
                className="h-4 w-4 shrink-0 text-slate-800"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M4 4a2 2 0 012-2h5.586A2 2 0 0113 2.586L15.414 5A2 2 0 0116 6.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
              </svg>
              <span className="text-xs font-bold text-slate-900">Evidencia</span>
            </div>
            <span className="text-base font-medium text-slate-700">
              {evidenciaOpen ? "−" : "+"}
            </span>
          </button>
          <p className="mt-0.5 text-[11px] text-slate-600">Normativa relacionada</p>

          {evidenciaOpen && (
            <div className="mt-2.5 space-y-2 border-t border-slate-200 pt-2.5">
              {step.evidenciaNormativa.map((ev, i) => (
                <div key={i} className="rounded bg-white p-2 text-[11px]">
                  <p className="font-semibold text-slate-800">{ev.titulo}</p>
                  <p className="mt-0.5 text-slate-600">{ev.detalle}</p>
                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-block font-semibold text-[#035C80] hover:underline"
                    >
                      Ver documento
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function DudaStepCard({ activeStep }: { activeStep: number }) {
  const [collapsed, setCollapsed] = useState(false)
  const [pregunta, setPregunta] = useState("")
  const [respuesta, setRespuesta] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const step = STEPS.find((s) => s.number === activeStep) ?? STEPS[0]

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault()
    if (!pregunta.trim()) return

    setLoading(true)
    setError(null)
    setRespuesta(null)

    const res = await preguntarSobrePaso(pregunta, step.title, step.description)
    if (res.error) {
      setError(res.error)
    } else {
      setRespuesta(res.respuesta)
    }
    setLoading(false)
  }

  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-bold text-slate-900">¿Tenés una duda?</h3>
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          className="flex h-5 w-5 cursor-pointer items-center justify-center text-slate-500 hover:text-slate-800"
          aria-label={collapsed ? "Expandir tarjeta de dudas" : "Minimizar tarjeta de dudas"}
        >
          {collapsed ? "+" : "−"}
        </button>
      </div>

      {!collapsed && (
        <>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
            Preguntá sobre el paso activo usando información oficial.
          </p>

          <form onSubmit={handleAsk} className="mt-3">
            <input
              type="text"
              value={pregunta}
              onChange={(e) => setPregunta(e.target.value)}
              placeholder="Ej.: ¿qué lleva el Anexo Técnico?"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#035C80] focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading}
              className="mt-2.5 cursor-pointer rounded-lg bg-[#1D3343] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#142430] disabled:opacity-60"
            >
              {loading ? "Consultando..." : "Preguntar"}
            </button>
          </form>

          {error && (
            <p className="mt-2.5 rounded-lg bg-red-50 p-2 text-[11px] text-red-700">
              {error}
            </p>
          )}

          {respuesta && (
            <div className="mt-3 rounded-lg border border-sky-100 bg-[#EDF4FF]/60 p-2.5 text-[11px] leading-relaxed text-slate-800">
              {respuesta}
            </div>
          )}
        </>
      )}
    </div>
  )
}

