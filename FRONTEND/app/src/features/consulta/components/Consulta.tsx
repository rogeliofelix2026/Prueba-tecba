"use client"

import { useConsulta } from "../use-consulta"
import { FormularioConsulta } from "./Formulario"
import { Mapa } from "./Mapa"
import { PopUpConfirmarConsulta } from "./PopUpConfirm"

export function Consulta() {
  const { pendiente, editar, confirmarConsulta } = useConsulta()

  return (
    <section className=" flex w-full  flex-row gap-10 mt-12">
      <FormularioConsulta></FormularioConsulta>
      <Mapa></Mapa>
      {pendiente && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/40 p-4">
          <PopUpConfirmarConsulta
            actividad={pendiente.activity ?? ""}
            ubicacion={pendiente.address ?? ""}
            onEditar={editar}
            onConfirmar={confirmarConsulta}
          />
        </div>
      )}
    </section>
  )
}