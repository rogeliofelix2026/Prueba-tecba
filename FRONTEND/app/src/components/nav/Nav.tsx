export default function Nav() {
  return (
    <nav className="border-b border-nav">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center h-full">
          <img
            className="h-10 sm:h-12 w-auto object-contain"
            src="/logo2.webp"
            alt="Logo Ciudad de Buenos Aires"
          />
        </div>

        <div>
          <a
            href="#recorrido-tramite"
            className="text-xs sm:text-sm font-bold text-[#035C80] hover:underline"
          >
            Cómo funciona
          </a>
        </div>
      </div>
    </nav>
  )
}