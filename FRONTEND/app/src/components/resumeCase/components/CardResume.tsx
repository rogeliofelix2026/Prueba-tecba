"use client"

type TramiteCardProps = {
  titulo?: string
  valor: string
}

export default function CardResume({ titulo, valor }: TramiteCardProps) {
  return (
    <div className="flex flex-1 flex-col justify-center rounded-xl bg-[#EDF4FF] px-4 py-3 sm:px-5 sm:py-4 min-h-[4.75rem] sm:min-h-[5.5rem]">
      <p className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wide text-[#035C80]">
        {titulo}
      </p>
      <p className="mt-1 text-sm sm:text-base font-bold text-zinc-900 leading-snug break-words">
        {valor}
      </p>
    </div>
  )
}