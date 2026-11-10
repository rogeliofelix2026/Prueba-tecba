"use client"

import { FormularioConsulta2 } from "../components/ForumularioV2"
import AuroraBackground from "../components/AuroraBackground"

export function Banner() {
  return (
    <AuroraBackground className="min-h-screen">
      <section className="flex min-h-screen flex-col items-center justify-evenly px-4 sm:px-6 py-12 md:py-16 text-center text-white">

        <span className="inline-flex w-fit max-w-[90%] items-center rounded-full bg-white/10 px-3 py-1 text-[10px] sm:text-[11px] font-medium tracking-wider text-white/70 backdrop-blur-sm text-center mb-6 md:mb-8">
          CONSULTAS SOBRE ACTIVIDADES ECONÓMICAS · CABA
        </span>

        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-medium text-textColor leading-tight px-2 mb-4 md:mb-6">
          Todo empieza con<br className="hidden sm:block" />
          <span className="sm:hidden"> </span>lo que querés hacer.
        </h1>

        <p className="w-full max-w-2xl font-medium tracking-wide text-textColor text-sm sm:text-base md:text-[16px] leading-relaxed px-2 mb-8 md:mb-10">
          Contanos tu actividad y dónde pensás realizarla. Te orientaremos con información territorial y sobre trámites, respaldada por fuentes oficiales.
        </p>

        <div className="w-full max-w-lg md:max-w-xl lg:max-w-2xl px-2 mb-8 md:mb-12">
          <FormularioConsulta2 />
        </div>

        <span className="text-textColor text-[10px] sm:text-[12px] uppercase tracking-wider mt-2">
          DESLIZÁ PARA CONOCER EL PROCESO ↓
        </span>
      </section>
    </AuroraBackground>
  )
}