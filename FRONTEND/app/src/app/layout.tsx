import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Nav from "../components/nav/Nav";
import { Providers } from "./providers";
import { Archivo, Open_Sans } from 'next/font/google'

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const archivo = Archivo({
  subsets: ['latin'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800', '900'],
  variable: '--font-archivo',
})

const openSans = Open_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800'],
  variable: '--font-opensans',
})

export const metadata = {
  title: "TADiA",
  description: "Orientación inteligente para trámites y actividades económicas en CABA",
  icons: {
    icon: "/tadia-icon.svg",
  },
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>
          {/* Esperando un nav nuevo 
          <header> 
            <Nav></Nav>
          </header> */}
          <main>
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
