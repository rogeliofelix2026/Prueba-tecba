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
        <div className="absolute flex flex-col items-center bottom-3 left-1/2 z-10 -translate-x-1/2 rounded-lg bg-white/90 px-3 py-2 shadow-md backdrop-blur-sm">
            <span className="text-xs font-medium text-gray-700">Locales Parecidos</span>
            <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-700">Radio</span>
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
                    className="w-24 pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-moz-range-thumb]:pointer-events-auto" />
                <span className="text-xs text-gray-600">
                    {localRadius.toFixed(2)} km
                </span>
            </div>
        </div>
    )
}