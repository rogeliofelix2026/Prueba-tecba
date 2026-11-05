"use client"

import { useState } from "react"

type BeforeStartProps = {
  data?: any
}

const REQUISITOS_BASE = [
  {
    code: "MIBA_N3",
    title: "Usuario miBA nivel 3",
    description: "Contar con usuario y contraseña de miBA con identidad validada en nivel 3 para ingresar a SSIT.",
  },
  {
    code: "CUIT_TITULAR",
    title: "CUIT de la persona titular o firmante",
    description: "Clave Única de Identificación Tributaria de la persona física o jurídica que solicita la habilitación.",
  },
  {
    code: "DATOS_CATASTRALES",
    title: "Identificación del establecimiento",
    description: "Dirección, número de partida o matriz, nomenclatura catastral (SMP), ubicación especial y datos de contacto.",
  },
  {
    code: "UNIDAD_USO",
    title: "Características del local y actividad",
    description: "Superficie total en m², dimensiones, ventilación, mixtura de uso y rubro de la actividad económica.",
  },
]

const DOCUMENTOS_BASE = [
  {
    code: "FORM_UNIDAD_USO",
    title: "Formulario de conformación de la unidad de uso",
    description: "Declaración jurada donde se informa qué actividad comercial se desarrollará en el establecimiento.",
    conditional: false,
  },
  {
    code: "ANEXO_TECNICO",
    title: "Anexo Técnico firmado por profesional responsable",
    description: "Incluye encomienda profesional, datos del profesional, unidad de uso, mixtura o área especial, croquis de ubicación y DDJJ de verificación.",
    conditional: false,
  },
]

const DOCUMENTOS_ADICIONALES = [
  {
    code: "CERT_SOBRECARGA",
    title: "Certificado de sobrecarga",
    description: "Se presenta únicamente cuando corresponda según las condiciones constructivas.",
    conditional: true,
  },
  {
    code: "PLANO_USO",
    title: "Plano de Uso de Actividad Económica",
    description: "Requerido en modalidades con plano o según exigencia normativa de la actividad.",
    conditional: true,
  },
  {
    code: "AUTORIZACION_EMPLAZAMIENTO",
    title: "Autorización de Emplazamiento",
    description: "Presentación condicional para ubicaciones o distritos con regulación especial.",
    conditional: true,
  },
  {
    code: "DOC_RUBRO_ESPECIFICO",
    title: "Documentación específica del rubro",
    description: "La normativa aplicable a la actividad puede requerir permisos o constancias adicionales.",
    conditional: true,
  },
]

export default function BeforeStart({ data }: BeforeStartProps) {
  const [openRequisitos, setOpenRequisitos] = useState(false)
  const [openDocumentos, setOpenDocumentos] = useState(false)

  const surfaceM2 = data?.query?.parameters?.surface_m2

  return (
    <section className="flex w-full flex-col gap-2" aria-label="Antes de iniciar">
      <div>
        <h2 className="text-2xl font-semibold text-zinc-900">Antes de iniciar</h2>
        <p className="mt-1 text-xs text-slate-600">
          Revisá primero qué dato puede cambiar el tipo de trámite y qué necesitás preparar.
        </p>
      </div>

      <div className="mt-2 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        {/* Condición de superficie */}
        <div className="flex flex-col gap-3 rounded-lg border border-[#F3DFB8] bg-[#FFF8EB] px-4 py-3.5 sm:flex-row sm:items-center">
          <span className="w-fit shrink-0 rounded-md border border-[#D49B35] bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-[#9A6700]">
            Condición
          </span>

          <div className="min-w-0 flex-1">
            <h3 className="text-xs font-semibold text-slate-900">
              La superficie puede cambiar el tipo de trámite
            </h3>
            <p className="mt-0.5 text-[11px] leading-relaxed text-slate-600">
              Si el local no supera los 200 m² y cumple otras condiciones, puede corresponder la vía exprés.
            </p>
          </div>

          <span className="w-fit shrink-0 rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-700">
            {surfaceM2 ? `${surfaceM2} m² informados` : "Dato no informado"}
          </span>
        </div>

        {/* Requisitos desplegable */}
        <div className="rounded-lg border border-slate-200 bg-white">
          <button
            type="button"
            onClick={() => setOpenRequisitos((v) => !v)}
            aria-expanded={openRequisitos}
            className="flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
          >
            <div className="flex items-center gap-3">
              <span className="shrink-0 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-700">
                Requisitos
              </span>
              <span className="text-xs font-medium text-slate-800">
                {REQUISITOS_BASE.length} datos base para empezar
              </span>
            </div>
            <span className="flex h-6 w-6 shrink-0 items-center justify-center text-lg font-medium text-slate-700">
              {openRequisitos ? "−" : "+"}
            </span>
          </button>

          {openRequisitos && (
            <div className="border-t border-slate-100 bg-slate-50/60 px-4 py-3.5">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {REQUISITOS_BASE.map((req, index) => (
                  <div
                    key={req.code}
                    className="flex items-start gap-2.5 rounded-lg border border-slate-200/80 bg-white p-3"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-[#EDF4FF] text-[11px] font-semibold text-[#035C80]">
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900">{req.title}</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-slate-600">
                        {req.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Documentos desplegable */}
        <div className="rounded-lg border border-slate-200 bg-white">
          <button
            type="button"
            onClick={() => setOpenDocumentos((v) => !v)}
            aria-expanded={openDocumentos}
            className="flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
          >
            <div className="flex items-center gap-3">
              <span className="shrink-0 rounded-md border border-sky-700/60 bg-sky-50/40 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-[#035C80]">
                Documentos
              </span>
              <span className="text-xs font-medium text-slate-800">
                {DOCUMENTOS_BASE.length} documentos base + adicionales
              </span>
            </div>
            <span className="flex h-6 w-6 shrink-0 items-center justify-center text-lg font-medium text-slate-700">
              {openDocumentos ? "−" : "+"}
            </span>
          </button>

          {openDocumentos && (
            <div className="space-y-3 border-t border-slate-100 bg-slate-50/60 px-4 py-3.5">
              <div>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Documentación base obligatoria
                </p>
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                  {DOCUMENTOS_BASE.map((doc) => (
                    <div
                      key={doc.code}
                      className="rounded-lg border border-slate-200 bg-white p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs font-semibold text-slate-900">{doc.title}</p>
                        <span className="shrink-0 rounded bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-[#035C80]">
                          Base
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
                        {doc.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Documentación adicional (cuando corresponda)
                </p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {DOCUMENTOS_ADICIONALES.map((doc) => (
                    <div
                      key={doc.code}
                      className="rounded-lg border border-dashed border-slate-200 bg-white/80 p-2.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs font-medium text-slate-800">{doc.title}</p>
                        <span className="shrink-0 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-800">
                          Condicional
                        </span>
                      </div>
                      <p className="mt-0.5 text-[11px] text-slate-500">{doc.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

