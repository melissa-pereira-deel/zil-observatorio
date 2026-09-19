import type { MetadataRoute } from "next";

import { indexacaoPublica } from "@/lib/flags";

/**
 * robots.txt gerado a partir da flag de indexação.
 *
 * Esta é a primeira das duas camadas: o robots.txt pede ao buscador que não
 * **rastreie**. Ele não impede que uma URL descoberta por link apareça no
 * índice — é para isso que existe a meta tag `noindex` no layout. Uma não
 * substitui a outra.
 *
 * `/em-breve` fica fora mesmo com a indexação ligada: é a página que o
 * middleware serve no lugar do ranking, não um destino.
 */
export default function robots(): MetadataRoute.Robots {
  if (!indexacaoPublica) {
    return { rules: { userAgent: "*", disallow: "/" } };
  }

  return {
    rules: { userAgent: "*", allow: "/", disallow: "/em-breve" },
  };
}
