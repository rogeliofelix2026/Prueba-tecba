"use client"
type TramiteCardProps = {
  titulo?: string
  valor: string
}

export default function CardResume({titulo, valor}: TramiteCardProps) {

  return (
    <div className="flex flex-1 flex-col justify-center rounded-xl bg-[#EDF4FF] px-5 py-4 min-h-[5.5rem]">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#035C80]">
        {titulo}
      </p>
      <p className="mt-1 text-base font-bold text-zinc-900">
        {valor}
      </p>
    </div>
  )
}
