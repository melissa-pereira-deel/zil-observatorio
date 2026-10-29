"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BotaoIcone, Button, Icone, type NomeIcone } from "@/components/ui";
import { rankingPublico } from "@/lib/flags";

/**
 * Navegação (ZIL Interface › Navegação): barra superior em vidro, sem borda
 * inferior, com links em pílula; no celular, tab bar flutuante em cápsula
 * com até cinco destinos. A separação vem do desfoque, não de linha.
 */

const LINKS: { href: string; rotulo: string; icone: NomeIcone }[] = [
  { href: "/", rotulo: "Manifesto", icone: "inicio" },
  // O placar só aparece quando a curadoria o sustenta (ver lib/flags.ts)
  ...(rankingPublico ? [{ href: "/ranking", rotulo: "Placar", icone: "placar" as const }] : []),
  { href: "/proposicoes", rotulo: "Proposições", icone: "documento" },
  { href: "/bussula", rotulo: "Bússola", icone: "bussola" },
  { href: "/metodologia", rotulo: "Metodologia", icone: "info" },
];

export function NavBar() {
  const pathname = usePathname();
  const [compacta, setCompacta] = useState(false);

  useEffect(() => {
    const aoRolar = () => setCompacta(window.scrollY > 24);
    aoRolar();
    window.addEventListener("scroll", aoRolar, { passive: true });
    return () => window.removeEventListener("scroll", aoRolar);
  }, []);

  const atual = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <>
      <nav
        aria-label="Principal"
        className={`zil-vidro sticky top-0 z-20 flex items-center gap-4 px-4 md:px-6 transition-[min-height] duration-padrao ease-padrao ${
          compacta ? "min-h-[52px]" : "min-h-16"
        }`}
      >
        <Link href="/" className="inline-flex items-center gap-2 text-[20px] font-bold leading-none tracking-[-0.02em] text-zil-texto no-underline">
          ZIL
          <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full bg-zil-brasil-amarelo" />
        </Link>

        <div className="hidden md:flex gap-0.5">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={atual(l.href) ? "page" : undefined}
              className={`inline-flex items-center h-9 px-3.5 rounded-pilula text-[15px] font-medium leading-none no-underline transition-colors duration-toque hover:bg-zil-vidro-hover hover:text-zil-texto ${
                atual(l.href) ? "bg-zil-vidro-ativo text-zil-texto" : "text-zil-texto-2"
              }`}
            >
              {l.rotulo}
            </Link>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <BotaoIcone icone="busca" rotulo="Buscar proposições" variante="fantasma" redondo href="/proposicoes" />
          <Button href="/#assinar" variante="primario" tamanho="s" className="hidden sm:inline-flex">
            Assinar
          </Button>
        </div>
      </nav>

      {/* Tab bar: cápsula flutuante no celular, 16px da base mais a área segura. */}
      <nav
        aria-label="Atalhos"
        className="zil-vidro md:hidden fixed left-1/2 -translate-x-1/2 z-20 flex gap-0.5 p-1.5 rounded-pilula shadow-elevada"
        // Distância da base soma a área segura do aparelho; não há classe para env().
        style={{ bottom: "calc(16px + env(safe-area-inset-bottom))" }}
      >
        {LINKS.slice(0, 5).map((l) => (
          <Link
            key={l.href}
            href={l.href}
            aria-current={atual(l.href) ? "page" : undefined}
            className={`grid justify-items-center gap-0.5 min-w-14 px-3 py-2 rounded-pilula text-[11px] leading-[14px] font-semibold no-underline transition-colors duration-padrao ease-padrao ${
              atual(l.href) ? "bg-zil-vidro-ativo text-zil-texto" : "text-zil-texto-2"
            }`}
          >
            <Icone nome={l.icone} className="!w-[22px] !h-[22px]" />
            {l.rotulo}
          </Link>
        ))}
      </nav>
    </>
  );
}
