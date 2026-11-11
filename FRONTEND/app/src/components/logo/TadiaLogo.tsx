type TadiaLogoProps = {
  variant?: "light" | "dark"
  className?: string
}

const LETTER_A_PATH =
  "M68.5 11.2C69.7 8.6 72.3 7 75.2 7H76.8C79.7 7 82.3 8.6 83.5 11.2L101.8 51C103.3 54.3 100.9 58 97.2 58H90.8C88.5 58 86.5 56.6 85.7 54.4L83.5 48.5H68.5L66.3 54.4C65.5 56.6 63.5 58 61.2 58H54.8C51.1 58 48.7 54.3 50.2 51L68.5 11.2ZM76 23.5L71.8 35.5H80.2L76 23.5Z"

export function TadiaLogo({
  variant = "light",
  className = "h-10 sm:h-12 w-auto",
}: TadiaLogoProps) {
  const textColor = variant === "light" ? "#FFFFFF" : "#0F2942"
  const starColor = variant === "light" ? "#38BDF8" : "#0891B2"

  return (
    <svg
      viewBox="0 0 242 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="TADiA"
    >
      {/* T */}
      <path
        d="M4 13C4 10.2 6.2 8 9 8H45C47.8 8 50 10.2 50 13V18.5C50 21.3 47.8 23.5 45 23.5H35V53C35 55.8 32.8 58 30 58H24C21.2 58 19 55.8 19 53V23.5H9C6.2 23.5 4 21.3 4 18.5V13Z"
        fill={textColor}
      />
      {/* A */}
      <path fillRule="evenodd" clipRule="evenodd" d={LETTER_A_PATH} fill={textColor} />
      {/* D */}
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M108 13C108 10.2 110.2 8 113 8H131.5C147.8 8 159 18.2 159 33C159 47.8 147.8 58 131.5 58H113C110.2 58 108 55.8 108 53V13ZM124 22V44H131C138.8 44 143.5 39.8 143.5 33C143.5 26.2 138.8 22 131 22H124Z"
        fill={textColor}
      />
      {/* i */}
      <rect x="166" y="23" width="16" height="35" rx="6.5" fill={textColor} />
      <path
        d="M174 0.5C175.5 7.2 178.5 10.2 185.2 11.7C178.5 13.2 175.5 16.2 174 22.9C172.5 16.2 169.5 13.2 162.8 11.7C169.5 10.2 172.5 7.2 174 0.5Z"
        fill={starColor}
      />
      {/* A */}
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d={LETTER_A_PATH}
        transform="translate(137 0)"
        fill={textColor}
      />
    </svg>
  )
}
