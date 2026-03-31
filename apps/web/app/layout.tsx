import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ZIL Observatório — Soberania Industrial do Brasil",
  description:
    "Plataforma aberta que monitora como cada parlamentar brasileiro vota nas pautas de soberania industrial: fertilizantes, minerais, semicondutores, energia, defesa.",
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
        {/* Navigation */}
        <nav className="border-b border-zil-divider">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <span className="font-display text-2xl tracking-wider">ZIL</span>
              <div className="flex gap-0.5">
                <div className="w-5 h-1 bg-zil-gold skew-x-[-12deg]" />
                <div className="w-2 h-1 bg-zil-green skew-x-[-12deg]" />
              </div>
            </Link>

            <div className="flex items-center gap-6 text-sm font-medium text-zil-soft">
              <Link
                href="/ranking"
                className="hover:text-zil-green transition-colors"
              >
                Ranking
              </Link>
              <Link
                href="/proposicoes"
                className="hover:text-zil-green transition-colors"
              >
                Proposições
              </Link>
              <Link
                href="/manifesto"
                className="hover:text-zil-green transition-colors"
              >
                Manifesto
              </Link>
              <Link
                href="/sobre"
                className="hover:text-zil-green transition-colors"
              >
                Sobre
              </Link>
            </div>
          </div>
        </nav>

        <main>{children}</main>

        {/* Footer */}
        <footer className="bg-zil-green-dark text-zil-bg mt-20">
          <div className="max-w-5xl mx-auto px-6 py-12">
            <div className="flex justify-between items-start flex-wrap gap-8">
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
              <div className="text-right">
                <p className="font-mono text-xs tracking-widest opacity-30">
                  2026 · AGPL-3.0
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
