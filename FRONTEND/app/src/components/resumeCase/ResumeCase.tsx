import CardResume from "./components/CardResume";

export default function ResumeCase() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-semibold text-xl sm:text-2xl">
        Resumen de tu caso
      </h1>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <CardResume titulo="TRÁMITE" valor="1 principal" />
        <CardResume titulo="REQUISITOS" valor="4 datos base" />
        <CardResume titulo="DOCUMENTACIÓN" valor="2 base + adicionales" />
        <CardResume titulo="RECORRIDO" valor="5 pasos" />
      </div>
    </div>
  )
}