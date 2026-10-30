import { existsSync } from "node:fs";
import path from "node:path";

/**
 * Vídeo de fundo da abertura da home.
 *
 * Os arquivos vivem em `apps/web/public/abertura/` (especificação no
 * README da pasta). A página confere quais existem quando é renderizada no
 * servidor: sem vídeo e sem poster, a abertura mostra o fundo provisório
 * (gradiente nas cores da bandeira). Para trocar, basta pôr os arquivos na
 * pasta — sem flag. Hospedado fora (Vercel Blob, CDN), as variáveis
 * `NEXT_PUBLIC_ABERTURA_VIDEO_URL` e `NEXT_PUBLIC_ABERTURA_VIDEO_CELULAR_URL`
 * têm precedência sobre os arquivos locais.
 *
 * Só para componentes de servidor: usa `fs`.
 */

export interface MidiaAbertura {
  video: string | null;
  videoCelular: string | null;
  poster: string | null;
  posterCelular: string | null;
}

const PASTA = "abertura";

function local(arquivo: string): string | null {
  return existsSync(path.join(process.cwd(), "public", PASTA, arquivo)) ? `/${PASTA}/${arquivo}` : null;
}

export function midiaAbertura(): MidiaAbertura {
  const video = process.env.NEXT_PUBLIC_ABERTURA_VIDEO_URL || local("abertura.mp4");
  return {
    video,
    // Sem arquivo próprio, o celular usa o de desktop.
    videoCelular: process.env.NEXT_PUBLIC_ABERTURA_VIDEO_CELULAR_URL || local("abertura-celular.mp4") || video,
    poster: local("abertura-poster.webp"),
    posterCelular: local("abertura-poster-celular.webp"),
  };
}
