import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { NavBar } from "@/components/NavBar";

export const metadata: Metadata = {
  title: "ZIL Observatório — Soberania Industrial do Brasil",
  description:
    "Plataforma aberta que mostra como parlamentares brasileiros votaram nas votações que mais importam para a soberania industrial: fertilizantes, minerais, semicondutores, energia, defesa.",
  openGraph: {
    title: "ZIL Observatório",
    description:
      "94% do nióbio mundial é nosso. 87% dos fertilizantes são importados. Veja como seu deputado vota.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen">
        <NavBar />

        <main>{children}</main>

        {/* Footer */}
        <footer className="bg-zil-green-dark text-zil-bg mt-20">
          <div className="max-w-5xl mx-auto px-5 md:px-8 py-10 md:py-12">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-8">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <span className="font-display text-xl">ZIL</span>
                  <div className="w-6 h-1 bg-zil-gold" />
                </div>
                <p className="text-sm opacity-40 max-w-xs leading-relaxed">
                  Plataforma aberta e apartidária. Código e dados livres. O
                  Brasil é de todos — e a soberania também.
                </p>
              </div>
              <div className="sm:text-right">
                <p className="font-mono text-xs tracking-widest opacity-30">
                  2026 &middot; AGPL-3.0
                </p>
                <a
                  href="https://github.com/zil-observatorio/zil-observatorio"
                  className="font-mono text-xs opacity-40 hover:opacity-70 transition-opacity mt-1 block"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  github.com/zil-observatorio
                </a>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
