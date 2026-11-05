"use client"

import { FormularioConsulta2 } from "../components/ForumularioV2"
import { useConsulta } from "../../consulta/use-consulta"
import { PopUpConfirmarConsulta } from "../components/PopUpConfirm"
import AuroraBackground from "../components/AuroraBackground"

export function Banner() {
    const { pendiente, editar, confirmarConsulta } = useConsulta()

    return (
        <AuroraBackground className="min-h-screen">
            <section className="flex min-h-screen flex-col items-center justify-evenly px-6 text-center text-white">

                <span className="inline-flex w-fit items-center rounded-full bg-white/10 px-3 py-1 text-[11px] font-medium tracking-wider text-white/70 backdrop-blur-sm">CONSULTAS SOBRE ACTIVIDADES ECONÓMICAS · CABA</span>

                <h1 className="text-8xl text-textColor md:text-6xl lg:text-7xl font-medium p-3 text-center">Todo empieza con<br />
                    lo que querés hacer.</h1>

                <span className="w-fitfont-medium tracking-wider backdrop-blur-sm p-3 text-[16px] text-textColor text-center">Contanos tu actividad y dónde pensás realizarla. Te orientaremos con información <br /> territorial y sobre trámites, respaldada por fuentes oficiales.</span>

                <FormularioConsulta2></FormularioConsulta2>

                <span className="text-textColor text-[12px] uppercase">DESLIZÁ PARA CONOCER EL PROCESO  ↓</span>

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
        </AuroraBackground>
    )
}