/** Quanto a home espera a API antes de desistir e mostrar o estado de falha. */
export const PRAZO_API_MS = 8000;

/**
 * `fetch` que desiste depois de `prazoMs`. Sem prazo, uma API que aceita a
 * conexão e não responde (um uvicorn --reload cujo worker morreu segura a
 * porta assim) prende o componente no esqueleto até o timeout de TCP do
 * navegador, mais de um minuto. O sinal continua valendo durante a leitura
 * do corpo, então `res.json()` também respeita o prazo.
 */
export function fetchComPrazo(url: string, prazoMs: number = PRAZO_API_MS): Promise<Response> {
  const controle = new AbortController();
  setTimeout(() => controle.abort(new DOMException("A API não respondeu a tempo", "TimeoutError")), prazoMs);
  return fetch(url, { signal: controle.signal });
}
