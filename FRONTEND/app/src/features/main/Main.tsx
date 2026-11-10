"use client"

import { Banner } from "./Pages/Banner"
import { HowToWork } from "./Pages/HowToWork"
import { useConsulta } from "../consulta/use-consulta"
import { PopUpConfirmarConsulta } from "./components/PopUpConfirm"

export function Main() {
  const { pendiente, cargando, editar, confirmarConsulta } = useConsulta()

  return (
    <section className="h-[95%] pb-10">
      <Banner />
      <HowToWork />

      {pendiente && (
        <PopUpConfirmarConsulta
          actividad={pendiente.activity ?? ""}
          ubicacion={pendiente.address ?? ""}
          cargando={cargando}
          onEditar={editar}
          onConfirmar={confirmarConsulta}
        />
      )}
    </section>
  )
}