import { ConsultaCard } from "./components/ConsultaCard"

type UbicResumeProps = {
  data: any
}

export default function UbicResume({ data }: UbicResumeProps) {
  return (
    <section className="w-full" aria-label="Resumen de ubicación">
      <ConsultaCard data={data} />
    </section>
  )
}
