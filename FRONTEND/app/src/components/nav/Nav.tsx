import { TadiaLogo } from "../logo/TadiaLogo"

export default function Nav() {
  return (
    <nav className="border-b border-nav">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center h-full">
          <TadiaLogo variant="dark" className="h-9 sm:h-10 w-auto" />
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
