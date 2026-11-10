"use client"

import { Mapa } from "../../consulta/components/Mapa"
import { StepCard } from "../components/StepCard"

function formatPasos(inicio: number, fin: number) {
  const pasos = Array.from({ length: fin - inicio + 1 }, (_, i) => inicio + i)
  if (pasos.length === 1) return `Paso ${pasos[0]}`
  if (pasos.length === 2) return `Pasos ${pasos[0]} y ${pasos[1]}`
  return `Pasos ${pasos.slice(0, -1).join(", ")} y ${pasos[pasos.length - 1]}`
}

export function HowToWork() {
  const items = {
    requeriments: [
      { number: "01", title: "Superficie total de hasta 200 m²", description: "No puede superar ese límite." },
      { number: "02", title: "Productos restringidos", description: "No comercializar explosivos, inflamables ni productos medicinales sin envase." },
      { number: "03", title: "Tipo de ubicación", description: "No estar en galerías, centros comerciales, paseos de compras, mercados, patios gastronómicos, estaciones de subte o tren, aeropuertos u otros complejos comerciales." },
      { number: "04", title: "Áreas especiales y restricciones urbanísticas", description: "No estar en áreas históricas, culturales, ambientales, protegidas ni con usos o restricciones particulares del Código Urbanístico." },
      { number: "05", title: "Edificio catalogado", description: "No estar en edificios catalogados por valor histórico, arquitectónico o cultural, ni con restricciones de uso o modificación." },
      { number: "06", title: "Accesibilidad", description: "Cumplir las condiciones establecidas por la normativa vigente." },
      { number: "07", title: "Entrepisos", description: "No tener entrepisos en las plantas a habilitar." },
      { number: "08", title: "Normativa específica de la actividad", description: "No realizar actividades que requieran reglas específicas, como farmacia, agencia de lotería o estudio profesional, entre otras." },
    ],
  }

  const items2 = {
    requeriments: [
      { number: "", title: "1 - Declarar la ubicación", description: "Elegí una forma de identificar el local: dirección, número de partida, datos catastrales o ubicación especial." },
      { number: "", title: "2 - Datos del titular o firmante", description: "Ingresá el CUIT de la persona solicitante, física o jurídica." },
      { number: "", title: "3 - Formularios del local", description: "Completá datos del local, conformidad de uso, dimensiones, tipo de superficie, ventilación, destino de uso y otras características generales." },
    ],
  }

  const items3 = {
    requeriments: [
      { number: "", title: "4 - Rubros y actividades", description: "Elegí una forma de identificar el local: dirección, número de partida, datos catastrales o ubicación especial." },
      { number: "", title: "5 - Datos del titular o firmante", description: "Ingresá el CUIT de la persona solicitante, física o jurídica." },
    ],
    extra: [
      { title: "Certificado de Aptitud Ambiental", description: "Según el procedimiento relevado, una vez completados todos los formularios se genera automáticamente el Certificado de Aptitud Ambiental." },
    ],
  }

  const rango2Inicio = items2.requeriments.length + 1
  const rango2Fin = items2.requeriments.length + items3.requeriments.length

  return (
    <section className="flex flex-col w-full min-h-[screen] items-center pt-6 md:pt-10">
      <div className="mb-8 md:mb-12 text-center flex flex-col items-center gap-4 md:gap-5 px-4">
        <p className="text-xs font-medium uppercase tracking-widest text-[#035C80]">
          ANTES DE INICIAR · HABILITACIÓN EXPRÉS
        </p>
        <h2 className="text-3xl font-bold text-[#035C80] md:text-4xl lg:text-5xl px-2">
          Un camino más claro para empezar
        </h2>
        <p className="mx-auto max-w-2xl text-[#527084] text-base md:text-[17px] px-2">
          Explorá los requisitos y el proceso de habilitación, paso a paso y sin complicaciones.
        </p>
        <div
          className="h-[4px] w-24 md:w-32 rounded-full"
          style={{ background: "linear-gradient(90deg, #705AE0 0%, #12B9A6 100%)" }}
        />
      </div>

      <section className="flex flex-col lg:flex-row gap-6 lg:gap-8 w-full justify-center min-w-0 px-4 md:px-6">
        {/* Columna izquierda: pasos */}
        <div className="w-full lg:w-[48%] xl:w-[43%] min-w-0 flex flex-col gap-4">
          <StepCard
            number="01"
            label="CONDICIONES DE LA VÍA EXPRÉS"
            title="Verificá si tu local cumple"
            description="Hasta 200 m², accesibilidad y condiciones de ubicación, edificio y actividad."
            tag="Requisitos obligatorios"
            color="blue"
            requirementsTitle={`${items.requeriments.length} requisitos obligatorios para la vía exprés`}
            items={items}
            moreButtonOpen={`Mostrar los ${items.requeriments.length} requisitos`}
            moreButtonClose="Ocultar los requisitos"
            footerNote="Cumplir el límite de superficie, por sí solo, no alcanza: deben cumplirse todas las condiciones."
            footerLink="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica-expres"
          />

          <StepCard
            number="02"
            label={`PASOS 1-${items2.requeriments.length}`}
            title="Identificá el local y al titular"
            description="Indicá la ubicación, ingresá el CUIT y completá los formularios del local."
            tag="Ubicación / CUIT / local"
            color="teal"
            requirementsTitle={formatPasos(1, items2.requeriments.length)}
            items={items2}
            moreButtonOpen={`Mostrar los pasos 1-${items2.requeriments.length}`}
            moreButtonClose={`Ocultar los pasos 1-${items2.requeriments.length}`}
            footerNote="Cumplir el límite de superficie, por sí solo, no alcanza: deben cumplirse todas las condiciones."
            footerLink="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica-expres"
          />

          <StepCard
            number="03"
            label={`PASOS ${rango2Inicio}-${rango2Fin}`}
            title="Declará el rubro y confirmá"
            description="Informá la actividad y revisá los datos antes de enviar la solicitud."
            tag="Rubro / revisión / CAA"
            color="purple"
            requirementsTitle={formatPasos(rango2Inicio, rango2Fin)}
            items={items3}
            moreButtonOpen={`Mostrar los pasos ${rango2Inicio}-${rango2Fin}`}
            moreButtonClose={`Ocultar los pasos ${rango2Inicio}-${rango2Fin}`}
            footerNote="Cumplir el límite de superficie, por sí solo, no alcanza: deben cumplirse todas las condiciones."
            footerLink="https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica-expres"
          />
        </div>

        {/* Columna derecha: mapa */}
        <div className="w-full lg:w-[48%] xl:w-[43%] min-w-0 flex flex-col gap-4 md:gap-5 mt-2 lg:mt-0">
          <div className="flex flex-col gap-2">
            <p className="text-[#035C80] text-[12px] font-bold tracking-wide">
              INDICÁ LA UBICACIÓN DESEADA
            </p>
            <h2 className="text-[#143146] text-xl md:text-2xl lg:text-[27px] font-semibold">
              Elegí dónde querés realizar la actividad.
            </h2>
            <p className="text-[#527084] text-sm md:text-[15px]">
              Podés señalar el lugar en el mapa o escribir la dirección en el chat de arriba.
            </p>
          </div>
          <div className="w-full h-[22rem] sm:h-[26rem] md:h-[30rem] lg:h-[34rem]">
            <Mapa height="100%" className="h-full" />
          </div>
        </div>
      </section>
    </section>
  )
}