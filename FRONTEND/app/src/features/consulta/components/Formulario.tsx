"use client"

import { useConsulta } from "../use-consulta"
import { AvisoOrientacion } from "./Aviso"


export function FormularioConsulta() {
    const { texto, cargando, error, resultado, setTexto, consultar } = useConsulta()

    return (
        <section className="flex flex-col w-[41%] min-w-0 gap-4">
            <h4 className="text-link text-sm">ORIENTACIÓN PARA ACTIVIDADES COMERCIALES</h4>
            <h1 className="font-semibold text-4xl">ARGENTINA EMPRENDE</h1>
            <p>Contanos qué actividad querés realizar. Si ya tenés
                una dirección, podés incluirla en la consulta o
                buscarla directamente en el mapa.
            </p>

            <h2>¿Qué querés hacer y dónde?</h2>
            <form onSubmit={consultar} className="flex flex-col gap-2">
                <div className="flex w-full flex-col gap-2">
                    <textarea
                        className={`w-[78%] h-30 rounded border px-3 py-2 text-zinc-900 transition-colors focus:outline-none focus:ring-2 ${error
                            ? "border-red-500 focus:ring-red-200"
                            : "border-zinc-300 focus:border-link focus:ring-link/30"
                            }`}
                        value={texto}
                        rows={3}
                        onChange={(event) => setTexto(event.target.value)}
                        disabled={cargando}
                        placeholder=" (ej. Habilitar verdulería en Cabildo 2000)"
                    />

                    <p className="text-sm">Podés escribirlo tus propias palabras,</p>

                    <AvisoOrientacion
                        titulo="La orientación se construye con información oficial."
                        detalle="Si falta algún dato, te lo vamos a indicar."
                    />

                    <section className="flex items-center gap-4">
                        <button
                            type="submit"
                            disabled={cargando || !texto.trim()}
                            className="flex items-center justify-center gap-2 min-w-[120px] rounded bg-blue-600 px-4 py-2 font-semibold text-white bg-button transition-colors hover:bg-button/95 disabled:opacity-80 disabled:cursor-default cursor-pointer"
                        >
                            {cargando ? (
                                <>
                                    <svg className="h-4 w-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                    </svg>
                                    <span>Buscando...</span>
                                </>
                            ) : (
                                "Consultar"
                            )}
                        </button>
                        <button
                            type="button"
                            onClick={() => setTexto("habilitar cafeteria en Av corrientes 2500")}
                            className="text-base font-semibold text-link cursor-pointer"
                        >
                            Ver un ejemplo
                        </button>
                    </section>
                </div>

                {error && (
                    <div className="rounded bg-red-50 border border-red-200 p-2.5 text-sm text-red-700 flex items-center gap-2">
                        <svg className="h-4 w-4 shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{error}</span>
                    </div>
                )}
            </form>

            
        </section>
    )
}