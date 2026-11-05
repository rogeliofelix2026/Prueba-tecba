export default function Nav() {
    return (
        <nav className="border-b-1 border-nav">
            <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between">
                <div>
                    <img className="h-16 w-auto" src="/logo2.webp" alt="Logo Ciudad de Buenos aires" />
                </div>

                <div>
                    <a href="#recorrido-tramite" className="text-xs font-bold text-[#035C80] hover:underline">Cómo funciona</a>
                </div>
            </div>
        </nav>
    );
}
