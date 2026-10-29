"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Revelar — o que está abaixo da dobra sobe 18px e aparece quando entra na
 * tela, em sequência (ZIL Interface › Revelar). O que já está visível ao
 * carregar nunca pisca: a classe só é aplicada no cliente, a elementos
 * fora da janela. Com movimento reduzido, corte seco (globals.css).
 */

export function Revelar({
  ordem = 0,
  as: Tag = "div",
  className = "",
  children,
}: {
  /** Posição na sequência: 70ms entre cada. */
  ordem?: number;
  as?: "div" | "section" | "li" | "article";
  className?: string;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const [estado, setEstado] = useState<"inicial" | "escondido" | "visivel">("inicial");

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const r = el.getBoundingClientRect();
    if (r.top < window.innerHeight) return; // já na tela: fica como está
    setEstado("escondido");
    const io = new IntersectionObserver(
      (entradas) => {
        if (entradas.some((e) => e.isIntersecting)) {
          setEstado("visivel");
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const cls = estado === "inicial" ? "" : `zil-revela ${estado === "visivel" ? "is-visivel" : ""}`;
  // A tag é dinâmica; o ref é tipado como o elemento genérico que todas compartilham.
  const Elemento = Tag as unknown as React.ComponentType<React.HTMLAttributes<HTMLElement> & { ref: React.Ref<HTMLElement> }>;
  return (
    <Elemento
      ref={ref}
      className={`${cls} ${className}`}
      // Atraso da sequência, lido pela transição em globals.css.
      style={{ "--atraso": `${ordem * 70}ms` } as React.CSSProperties}
    >
      {children}
    </Elemento>
  );
}

/** Número que conta até o valor quando entra na tela. Até quatro por tela. */
export function Contador({ ate, sufixo = "", prefixo = "", duracao = 1100, className = "" }: { ate: number; sufixo?: string; prefixo?: string; duracao?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [valor, setValor] = useState(ate);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const io = new IntersectionObserver((entradas) => {
      if (!entradas.some((e) => e.isIntersecting)) return;
      io.disconnect();
      const inicio = performance.now();
      const passo = (agora: number) => {
        const t = Math.min(1, (agora - inicio) / duracao);
        const suave = 1 - Math.pow(1 - t, 3);
        setValor(Math.round(ate * suave));
        if (t < 1) requestAnimationFrame(passo);
      };
      setValor(0);
      requestAnimationFrame(passo);
    });
    io.observe(el);
    return () => io.disconnect();
  }, [ate, duracao]);

  return (
    <span ref={ref} className={`zil-num ${className}`}>
      {prefixo}
      {valor.toLocaleString("pt-BR")}
      {sufixo}
    </span>
  );
}
