// components/MapStatusBadge.tsx
type Props = {
  loading?: boolean
  error?: string | null
  count?: number
}

export function MapStatusBadge({ loading, error, count }: Props) {
  if (!loading && !error && count == null) return null

  return (
    <div className="pointer-events-none absolute left-1/2 top-3 z-10 -translate-x-1/2">
      {loading && (
        <div className="rounded-full bg-white/90 px-4 py-1.5 text-sm font-medium text-gray-700 shadow-md backdrop-blur-sm">
          Cargando locales...
        </div>
      )}
      {error && (
        <div className="rounded-full bg-red-50/90 px-4 py-1.5 text-sm font-medium text-red-700 shadow-md backdrop-blur-sm">
          Error: {error}
        </div>
      )}
      {!loading && count != null && (
        <div className="rounded-full bg-white/90 px-4 py-1.5 text-sm font-medium text-gray-700 shadow-md backdrop-blur-sm">
          {count} locales encontrados
        </div>
      )}
    </div>
  )
}