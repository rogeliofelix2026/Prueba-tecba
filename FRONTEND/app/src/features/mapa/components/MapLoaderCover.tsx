import { useEffect, useRef, useState } from "react"

// components/MapCoverLoader.tsx
export function MapCoverLoader({ loading }: { loading: boolean }) {
    const [visible, setVisible] = useState(false)
    const startRef = useRef<number>(0)

    useEffect(() => {
        if (loading) {
            startRef.current = Date.now()
            setVisible(true)
            return
        }

        const elapsed = Date.now() - startRef.current
        const remaining = Math.max(0, 3000 - elapsed)
        const t = setTimeout(() => setVisible(false), remaining)
        return () => clearTimeout(t)
    }, [loading])

    if (!visible) return null

    return (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
                {/* Logo titilando */}
                <div className="animate-pulse">
                    <svg
                        width="48"
                        height="48"
                        viewBox="0 0 24 24"
                        fill="none"
                        className="text-black"
                    >
                        <path
                            d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"
                            fill="currentColor"
                        />
                        <circle cx="12" cy="9" r="2.5" fill="white" />
                    </svg>
                </div>
                <span className="text-sm font-medium text-gray-700">
                    Cargando mapa...
                </span>
            </div>
        </div>
    )
}