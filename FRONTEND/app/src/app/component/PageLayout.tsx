'use client';

import { useConsulta } from "../../features/consulta/use-consulta";
import { MainStarted } from "../../components/mainStarted/MainStarted";
import { Main } from "../../features/main/Main";



export default function PageLayout() {
    const { consultaIniciada } = useConsulta();

    return (
        <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans">

            {consultaIniciada ? ( 
                <main className="w-full">
                    <MainStarted /> 
                </main>
            ):(
                <main className="w-full">
                    <Main></Main>
                </main>
            )}   
                
        </div >
    );
}