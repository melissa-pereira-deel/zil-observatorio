import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { rankingPublico, ROTAS_DEPENDENTES_DE_SCORE } from "@/lib/flags";

/**
 * Esconder link não é esconder página: sem isto, /ranking continuaria acessível
 * por URL direta, por histórico e por buscador. O middleware fecha a rota na
 * borda, não só na navegação.
 */
export function middleware(request: NextRequest) {
  if (rankingPublico) return NextResponse.next();

  const { pathname } = request.nextUrl;
  const dependeDeScore = ROTAS_DEPENDENTES_DE_SCORE.some(
    (rota) => pathname === rota || pathname.startsWith(`${rota}/`),
  );

  if (dependeDeScore) {
    const url = request.nextUrl.clone();
    url.pathname = "/em-breve";
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/ranking/:path*", "/parlamentar/:path*"],
};
