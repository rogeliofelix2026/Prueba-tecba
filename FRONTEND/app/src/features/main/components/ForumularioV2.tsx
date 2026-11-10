"use client";

import { useConsulta } from "../../consulta/use-consulta";

export function FormularioConsulta2() {
    const {
        texto,
        cargando,
        error,
        setTexto,
        consultar,
    } = useConsulta();

    return (
        <div className="group relative w-full max-w-2xl mx-auto">
            {/* Halo */}
            <div
                className="pointer-events-none absolute -inset-3 md:-inset-4 rounded-3xl opacity-50 md:opacity-60 blur-xl md:blur-2xl"
                style={{
                    background: 'linear-gradient(90deg, #20CAB9 0%, #7992FF 55%, #D3A3FF 100%)',
                }}
            />

            <section className="relative z-10 flex flex-col min-w-0 gap-4 p-4 sm:p-5 md:p-6 bg-white rounded-2xl shadow-[0_0_20px_10px_rgba(255,255,255,0.4)]">
                <form onSubmit={consultar} className="flex flex-col gap-3">
                    <div className="flex w-full flex-col gap-2">
                        <header className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-0">
                            <span className="font-semibold text-base sm:text-[17px] md:text-[18px] text-[#102A3A]">
                                ¿Qué querés hacer?
                            </span>
                            <span className="font-normal text-xs sm:text-[13px] text-[#5B7284]">
                                Podés escribirlo con tus palabras
                            </span>
                        </header>

                        <main>
                            <textarea
                                className={`w-full text-base sm:text-lg md:text-xl lg:text-[22px] min-h-[110px] md:min-h-[120px] rounded-lg border bg-white px-3 py-2.5 text-zinc-900 transition-colors focus:outline-none focus:ring-2 resize-y ${
                                    error
                                        ? "border-red-500 focus:ring-red-200"
                                        : "border-zinc-300 focus:border-link focus:ring-link/30"
                                }`}
                                value={texto}
                                rows={3}
                                onChange={(event) => setTexto(event.target.value)}
                                disabled={cargando}
                                placeholder="Ej.: Quiero abrir una cafetería en Av. Corrientes 2500"
                            />
                        </main>

                        <footer className="flex flex-col-reverse sm:flex-row sm:justify-between sm:items-center gap-3 sm:gap-4">
                            <span className="text-[#586C7B] text-xs sm:text-[13px] text-center sm:text-left leading-snug">
                                La orientación muestra sus fuentes y señala cuando falta información.
                            </span>

                            <button
                                type="submit"
                                disabled={cargando || !texto.trim()}
                                className="flex items-center justify-center gap-2 w-full sm:w-auto min-w-[120px] rounded-lg px-4 py-2.5 font-semibold text-white bg-button transition-colors hover:bg-button/95 disabled:opacity-80 disabled:cursor-default cursor-pointer"
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
                        </footer>
                    </div>

                    {error && (
                        <div className="rounded-lg bg-red-50 border border-red-200 p-2.5 text-sm text-red-700 flex items-start gap-2 text-left">
                            <svg className="h-4 w-4 shrink-0 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{error}</span>
                        </div>
                    )}
                </form>
            </section>
        </div>
    );
}