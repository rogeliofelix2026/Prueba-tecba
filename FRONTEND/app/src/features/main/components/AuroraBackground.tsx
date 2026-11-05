'use client';

import { useEffect, useState } from 'react';

export default function AuroraBackground({
    children,
    className = ''
}: {
    children?: React.ReactNode;
    className?: string;
}) {
    const [dots, setDots] = useState<{ x: number; y: number; delay: number }[]>([]);

    useEffect(() => {
        const positions = [
            { x: 12, y: 22 }, { x: 28, y: 18 }, { x: 45, y: 28 },
            { x: 68, y: 20 }, { x: 82, y: 35 }, { x: 18, y: 48 },
            { x: 35, y: 55 }, { x: 58, y: 42 }, { x: 75, y: 58 },
            { x: 22, y: 72 }, { x: 48, y: 68 }, { x: 65, y: 75 },
            { x: 88, y: 62 }, { x: 15, y: 85 }, { x: 40, y: 82 },
            { x: 72, y: 88 }, { x: 55, y: 15 }, { x: 90, y: 25 },
        ];

        const withDelay = positions.map((pos, i) => ({
            ...pos,
            delay: (i * 0.7) % 8,
        }));

        setDots(withDelay);
    }, []);

    return (
        <div className={`relative isolate overflow-hidden ${className}`}>
            {/* Fondo del bloque */}
            <div className="absolute inset-0 -z-10">
                {/* Gradiente principal */}
                <div
                    className="absolute inset-0"
                    style={{
                        background: 'linear-gradient(69.9deg, #0B1930 18.75%, #162C66 61.61%, #101C3E 108.04%)',
                    }}
                />

                {/* Grilla */}
                <div
                    className="absolute inset-0"
                    style={{
                        backgroundImage: `
              linear-gradient(to right, #D9F4FF11 1px, transparent 1px),
              linear-gradient(to bottom, #D9F4FF11 1px, transparent 1px)
            `,
                        backgroundSize: '48px 48px',
                        maskImage: 'radial-gradient(ellipse 80% 70% at 50% 50%, black 30%, transparent 75%)',
                        WebkitMaskImage: 'radial-gradient(ellipse 80% 70% at 50% 50%, black 30%, transparent 75%)',
                    }}
                />

                {/* Auroras animadas */}
                <div
                    className="absolute -left-[15%] -bottom-[20%] h-[70%] w-[60%] rounded-full blur-[80px] animate-aurora-1"
                    style={{ background: '#00BFB56B' }}
                />
                <div
                    className="absolute -right-[10%] top-[10%] h-[50%] w-[50%] rounded-full blur-[80px] animate-aurora-2"
                    style={{ background: '#2668EA80' }}
                />
                <div
                    className="absolute -right-[5%] -top-[15%] h-[55%] w-[45%] rounded-full blur-[80px] animate-aurora-3"
                    style={{ background: '#7655EFA6' }}
                />

                {/* Lightwash centro */}
                <div
                    className="absolute left-1/2 top-[45%] h-[50%] w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[100px] animate-pulse-slow"
                    style={{ background: '#5378FF3B' }}
                />

                {/* Órbitas */}
                <div
                    className="absolute left-3/4 top-1/4 -translate-x-1/2 -translate-y-1/2 rounded-full"
                    style={{
                        width: 380,
                        height: 380,
                        border: '1px solid #BCE5FF1F',
                        opacity: 0.6,
                    }}
                />
                <div
                    className="absolute left-4/6 -top-5 rounded-full"
                    style={{
                        width: 580,
                        height: 580,
                        border: '1px solid #BCE5FF1F',
                        opacity: 0.6,
                    }}
                />

                {/* Puntos animados */}
                {dots.map((dot, i) => (
                    <div
                        key={i}
                        className="absolute h-1 w-1 rounded-full animate-dot"
                        style={{
                            left: `${dot.x}%`,
                            top: `${dot.y}%`,
                            background: '#D7F7FFA6',
                            boxShadow: '0 0 6px #D7F7FFA6',
                            animationDelay: `${dot.delay}s`,
                        }}
                    />
                ))}
            </div>

            {/* Contenido */}
            {children}

            {/* Animaciones */}
            <style jsx global>{`
        @keyframes aurora-1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(8%, -6%) scale(1.08); }
        }
        @keyframes aurora-2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-6%, 8%) scale(1.05); }
        }
        @keyframes aurora-3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(5%, 4%) scale(1.1); }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 0.85; transform: translate(-50%, -50%) scale(1.05); }
        }
        @keyframes dot-float {
          0%, 100% { 
            transform: translate(0, 0); 
            opacity: 0.5;
          }
          50% { 
            transform: translate(26px, -18px); 
            opacity: 1;
          }
        }
        .animate-aurora-1 {
          animation: aurora-1 18s ease-in-out infinite;
        }
        .animate-aurora-2 {
          animation: aurora-2 22s ease-in-out infinite;
        }
        .animate-aurora-3 {
          animation: aurora-3 20s ease-in-out infinite;
        }
        .animate-pulse-slow {
          animation: pulse-slow 12s ease-in-out infinite;
        }
        .animate-dot {
          animation: dot-float 7s ease-in-out infinite;
        }
      `}</style>
        </div>
    );
}
