"use client"

import { FormularioConsulta2 } from "../components/ForumularioV2"
import AuroraBackground from "../components/AuroraBackground"
import { TadiaLogo } from "../../../components/logo/TadiaLogo"

export function Banner() {
  return (
    <AuroraBackground className="min-h-screen">
      <section className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col items-center justify-between px-4 py-8 sm:px-8 sm:py-10 md:py-12 text-center text-white">
        {/* Encabezado superior: Logo TADiA a la izquierda y etiqueta centrada */}
        <header className="relative flex w-full flex-col items-center gap-4 sm:gap-5 md:min-h-[4.5rem] md:flex-row md:justify-center">
          <div className="flex w-full items-center justify-start md:absolute md:left-0 md:top-1/2 md:w-auto md:-translate-y-1/2">
            <TadiaLogo
              variant="light"
              className="h-10 w-auto select-none drop-shadow-sm sm:h-12 md:h-14 lg:h-16"
            />
          </div>

          <span className="inline-flex w-fit max-w-[92%] items-center rounded-full border border-white/15 bg-white/10 px-3.5 py-1 text-[10px] font-medium tracking-wider text-white/80 backdrop-blur-sm sm:text-[11px]">
            CONSULTAS SOBRE ACTIVIDADES ECONÓMICAS · CABA
          </span>
        </header>

        {/* Bloque central: Título, subtítulo y formulario */}
        <div className="my-auto flex w-full flex-col items-center py-6 sm:py-8">
          <h1 className="mb-4 px-2 text-4xl font-normal leading-[1.12] tracking-tight text-textColor sm:text-5xl md:mb-5 md:text-6xl lg:text-[4.25rem]">
            Todo empieza con
            <br />
            lo que querés hacer.
          </h1>

          <p className="mb-7 w-full max-w-xl px-2 text-xs leading-relaxed tracking-wide text-white/85 sm:text-sm md:mb-9 md:text-[15px]">
            Contanos tu actividad y dónde pensás realizarla. Te orientaremos con
            información territorial y sobre trámites, respaldada por fuentes
            oficiales.
          </p>

          <div className="w-full max-w-lg px-1 sm:px-2 md:max-w-xl lg:max-w-2xl">
            <FormularioConsulta2 />
          </div>
        </div>

        {/* Pie del hero */}
        <span className="pb-1 text-[10px] uppercase tracking-widest text-white/75 sm:text-[11px]">
          DESLIZÁ PARA CONOCER EL PROCESO ↓
        </span>
      </section>
    </AuroraBackground>
  )
}
