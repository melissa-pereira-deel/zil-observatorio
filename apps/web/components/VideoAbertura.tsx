"use client";

import { useEffect, useRef, useState } from "react";

import { BotaoIcone } from "@/components/ui";
import type { MidiaAbertura } from "@/lib/midia";

/**
 * Abertura da home com vídeo de fundo, de borda a borda, passando por baixo
 * da barra de navegação para o vidro desfocá-lo.
 *
 * Camadas, de trás para a frente: poster (ou fundo provisório) → vídeo →
 * véu → conteúdo. O HTML inicial carrega só o poster; o `src` do vídeo é
 * atribuído no cliente, já escolhendo o arquivo de celular abaixo de
 * 768px, para o celular nunca baixar o de desktop. Com movimento reduzido
 * o vídeo não carrega. O botão de pausa existe porque o vídeo se move
 * sozinho por mais de 5 segundos (WCAG 2.2.2).
 */
export function VideoAbertura({ midia, children }: { midia: MidiaAbertura; children: React.ReactNode }) {
  const video = useRef<HTMLVideoElement>(null);
  const [src, setSrc] = useState<string | null>(null);
  const [tocando, setTocando] = useState(false);

  useEffect(() => {
    if (!midia.video) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const celular = window.matchMedia("(max-width: 767px)").matches;
    setSrc(celular ? midia.videoCelular : midia.video);
  }, [midia.video, midia.videoCelular]);

  useEffect(() => {
    const v = video.current;
    if (!v || !src) return;
    v.play().then(
      () => setTocando(true),
      () => setTocando(false), // autoplay bloqueado: fica o poster
    );
  }, [src]);

  const alternar = () => {
    const v = video.current;
    if (!v) return;
    if (v.paused) {
      v.play().then(() => setTocando(true), () => undefined);
    } else {
      v.pause();
      setTocando(false);
    }
  };

  const temFundo = midia.poster || midia.video;

  return (
    <header className="relative isolate -mt-16 overflow-hidden">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        {midia.poster ? (
          <picture>
            {midia.posterCelular && <source media="(max-width: 767px)" srcSet={midia.posterCelular} />}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={midia.poster} alt="" className="absolute inset-0 w-full h-full object-cover" />
          </picture>
        ) : (
          // Fundo provisório enquanto o vídeo não existe (ver lib/midia.ts).
          !temFundo && <div className="zil-abertura-provisoria absolute inset-0" />
        )}
        {src && (
          <video
            ref={video}
            src={src}
            muted
            loop
            playsInline
            preload="auto"
            poster={midia.poster ?? undefined}
            onError={() => setSrc(null)}
            className="absolute inset-0 w-full h-full object-cover"
          />
        )}
        <div className="zil-abertura-veu absolute inset-0" />
      </div>

      <div className="zil-container relative flex flex-col justify-end min-h-[min(88svh,880px)] pt-28 pb-12 md:pb-16">
        {children}
        {src && (
          <BotaoIcone
            icone={tocando ? "pausa" : "play"}
            rotulo={tocando ? "Pausar vídeo" : "Reproduzir vídeo"}
            variante="vidro"
            redondo
            tamanho="s"
            onClick={alternar}
            className="absolute right-4 bottom-12 md:right-12 md:bottom-16"
          />
        )}
      </div>
    </header>
  );
}
