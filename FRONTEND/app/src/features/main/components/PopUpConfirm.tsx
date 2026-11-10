type ConfirmarConsultaProps = {
    actividad: string
    ubicacion: string
    cargando?: boolean
    onEditar: () => void
    onConfirmar: () => void
}

export function PopUpConfirmarConsulta({
    actividad,
    ubicacion,
    cargando = false,
    onEditar,
    onConfirmar,
}: ConfirmarConsultaProps) {
    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-zinc-900/40 p-4 text-left backdrop-blur-[2px]">
            <section className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-5 text-zinc-900 shadow-sm">
                <h2 className="text-lg font-semibold">Confirmá tu consulta</h2>

                <p className="mt-3 text-sm leading-relaxed text-zinc-600">
                    Antes de analizar el caso, revisá que hayamos entendido bien la actividad y la ubicación.
                </p>

                <dl className="mt-4 space-y-3 text-sm">
                    <div>
                        <dt className="text-zinc-500">Actividad</dt>
                        <dd className="mt-0.5 font-medium">{actividad}</dd>
                    </div>
                    <div>
                        <dt className="text-zinc-500">Ubicación</dt>
                        <dd className="mt-0.5 font-medium">{ubicacion}</dd>
                    </div>
                </dl>

                <div className="mt-5 flex gap-2">
                    <button
                        type="button"
                        disabled={cargando}
                        onClick={onEditar}
                        className="cursor-pointer rounded-md border-2 border-zinc-900 bg-white px-4 py-2 text-sm font-medium text-zinc-900 disabled:opacity-60"
                    >
                        Editar
                    </button>
                    <button
                        type="button"
                        disabled={cargando}
                        onClick={onConfirmar}
                        className="cursor-pointer rounded-md bg-button px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                    >
                        {cargando ? "Confirmando..." : "Confirmar"}
                    </button>
                </div>
            </section>
        </div>
    )
}