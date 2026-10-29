import type { Metadata } from "next";
import { Archivo } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";
import { indexacaoPublica } from "@/lib/flags";

export const metadata: Metadata = {
  // Segunda camada do noindex: o robots.txt pede para não rastrear, esta meta
  // tag impede indexar uma URL que o buscador chegou por link de fora.
  // Ver o comentário de `indexacaoPublica` em lib/flags.ts.
  ...(indexacaoPublica ? {} : { robots: { index: false, follow: false } }),
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

// A única família do site, servida pelo próprio Next (sem pedido ao Google
// em tempo de execução, sem troca de fonte ao carregar). Variável em peso.
const archivo = Archivo({
  subsets: ["latin", "latin-ext"],
  display: "swap",
  variable: "--font-sans",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // O escuro é o tema padrão do ZIL Interface; `data-theme="claro"` troca.
    <html lang="pt-BR" data-theme="escuro" className={archivo.variable}>
      <body className="min-h-screen">
        <NavBar />

        {/* Respiro inferior no celular para a tab bar flutuante. */}
        <main className="pb-24 md:pb-0">{children}</main>

        <footer className="zil-container mt-16 md:mt-24 mb-28 md:mb-12">
          <div className="grid gap-8 md:grid-cols-[1fr_auto] items-start px-6 py-8 md:px-10 md:py-10 rounded-xl bg-zil-superficie-1">
            <div className="grid gap-3">
              <span className="inline-flex items-center gap-2 text-[20px] font-bold leading-none tracking-[-0.02em]">
                ZIL
                <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full bg-zil-brasil-amarelo" />
              </span>
              <p className="text-texto-s text-zil-texto-2 max-w-[44ch]">
                Plataforma aberta e apartidária. Código e dados livres. O Brasil é de todos — e a soberania também.
              </p>
            </div>
            <div className="grid gap-1 md:text-right text-texto-s text-zil-texto-2 zil-num">
              <span>2026 · AGPL-3.0</span>
              <a
                href="https://github.com/zil-observatorio/zil-observatorio"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zil-texto-2 hover:text-zil-texto transition-colors duration-toque"
              >
                github.com/zil-observatorio ↗
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
