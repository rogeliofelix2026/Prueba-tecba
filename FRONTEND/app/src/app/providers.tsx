'use client';

import { ConsultaProvider } from "../features/consulta/consulta-provider";


export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ConsultaProvider>
      {children}
    </ConsultaProvider>
  );
}