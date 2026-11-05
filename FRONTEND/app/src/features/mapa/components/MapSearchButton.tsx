// components/MapSearchButton.tsx
type Props = {
  onClick: () => void
}

export function MapSearchButton({ onClick }: Props) {
  return (
    <div className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2">
      <button
        type="button"
        className="rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white shadow-lg transition-colors hover:bg-black/90 cursor-pointer"
        onClick={onClick}
      >
        Buscar locales parecidos
      </button>
    </div>
  )
}