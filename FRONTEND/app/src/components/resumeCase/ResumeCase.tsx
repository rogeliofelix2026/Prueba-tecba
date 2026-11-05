import CardResume from "./components/CardResume";

export default function ResumeCase() {
    return (
        <div className="flex gap-4 flex-col">
            <h1 className=" font-semibold text-2xl">Resumen de tu caso</h1>
            <div className="flex gap-5">
                <CardResume titulo="TRÁMITE" valor="1 principal" />
                <CardResume titulo="REQUISITOS" valor="4 datos base" />
                <CardResume titulo="DOCUMENTACIÓN" valor="2 base + adicionales" />
                <CardResume titulo="RECORRIDO" valor="5 pasos" />
            </div>
        </div>
    );
}
