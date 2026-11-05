// components/AnimatedBackground.tsx
export function AnimatedBackground({ children }: { children: React.ReactNode }) {
    return (
        <div className="w-full ">
            {/* Fondo animado */}
            <div
                className="inset-0 animate-gradient bg-gradient-to-br from-teal-900 via-cyan-800 to-indigo-900"
                style={{
                    background: `
            linear-gradient(135deg, #0f766e 0%, #115e59 25%, #1e1b4b 70%, #312e81 100%),
            radial-gradient(ellipse at 20% 40%, rgba(20, 184, 166, 0.25) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 60%, rgba(99, 102, 241, 0.3) 0%, transparent 55%)
          `,
                    backgroundSize: "200% 200%, 100% 100%, 100% 100%",
                    backgroundPosition: "0% 50%, 0% 0%, 0% 0%",
                }}
            >

                {/* Capa extra suave para más profundidad */}
                    <div className="relative z-10">
                        {children}
                    </div>
            </div>
        </div>
    );
}