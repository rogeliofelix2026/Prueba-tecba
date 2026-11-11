import { useState, useEffect } from "react"

type Props = {
    radius: number
    onChange: (radius: number) => void
    onCommit: (radius: number) => void
}

export function MapRadiusControl({ radius, onChange, onCommit }: Props) {
    const [localRadius, setLocalRadius] = useState(radius)

    // Sincronizar si el radio cambia desde afuera
    useEffect(() => {
        setLocalRadius(radius)
    }, [radius])

    return (
        <div className="absolute bottom-9 left-2.5 z-10 flex flex-col items-center rounded-lg bg-white/90 px-2 py-1.5 shadow-md backdrop-blur-sm sm:bottom-3 sm:left-1/2 sm:-translate-x-1/2 sm:px-3 sm:py-2">
            <span className="text-[10px] font-medium text-gray-700 sm:text-xs">Locales Parecidos</span>
            <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="text-[10px] font-medium text-gray-700 sm:text-xs">Radio</span>
                <input
                    type="range"
                    min={0.1}
                    max={1}
                    step={0.05}
                    value={localRadius}
                    onChange={(e) => {
                        const value = Number(e.target.value)
                        setLocalRadius(value)
                        onChange(value) // actualiza el círculo en tiempo real
                    }}
                    onMouseUp={(e) => onCommit?.(Number(e.currentTarget.value))}
                    onTouchEnd={(e) => onCommit?.(Number(e.currentTarget.value))}
                    className="w-16 sm:w-24 pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-moz-range-thumb]:pointer-events-auto" />
                <span className="text-[10px] text-gray-600 sm:text-xs">
                    {localRadius.toFixed(2)} km
                </span>
            </div>
        </div>
    )
}
