"use client"

import { useState } from "react"

type AvisoOrientacionProps = {
  titulo: string
  detalle: string
}

export function AvisoOrientacion({ titulo, detalle }: AvisoOrientacionProps) {
  const [visible, setVisible] = useState(true)
  if (!visible) return null

  return (
    <div className="flex items-start gap-3 rounded-md border-2 border-[#0086AD] bg-[#E5F9FF] px-3 py-2.5 text-sm text-sky-950">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-sky-600 text-xs font-semibold text-white">
        i
      </span>

      <p className="min-w-0 flex-1 leading-snug">
        <span className="font-semibold">{titulo}</span> {detalle}
      </p>

      <button
        type="button"
        onClick={() => setVisible(false)}
        aria-label="Cerrar aviso"
        className="shrink-0 text-sky-800/70 hover:text-sky-950"
      >
        <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M5 5l10 10M15 5L5 15" />
        </svg>
      </button>
    </div>
  )
}