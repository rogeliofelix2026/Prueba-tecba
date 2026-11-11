// components/MapStatusBadge.tsx
type Props = {
  loading?: boolean
  error?: string | null
  count?: number
}

export function MapStatusBadge({ loading, error, count }: Props) {
  if (!loading && !error && count == null) return null

  return (
    <div className="pointer-events-none absolute bottom-24 left-2.5 z-10 sm:bottom-auto sm:left-1/2 sm:top-3 sm:-translate-x-1/2">
      {loading && (
        <div className="rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-medium text-gray-700 shadow-md backdrop-blur-sm sm:px-4 sm:py-1.5 sm:text-sm">
          Cargando locales...
        </div>
      )}
      {error && (
        <div className="rounded-full bg-red-50/90 px-2.5 py-1 text-[11px] font-medium text-red-700 shadow-md backdrop-blur-sm sm:px-4 sm:py-1.5 sm:text-sm">
          Error: {error}
        </div>
      )}
      {!loading && count != null && (
        <div className="rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-medium text-gray-700 shadow-md backdrop-blur-sm sm:px-4 sm:py-1.5 sm:text-sm">
          {count} locales encontrados
        </div>
      )}
    </div>
  )
}
