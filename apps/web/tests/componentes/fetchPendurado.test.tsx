import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RankingPreview } from "@/components/RankingPreview";
import { VotacaoDestaque } from "@/components/VotacaoDestaque";

/**
 * Uma API que aceita a conexão e nunca responde (um uvicorn --reload cujo
 * worker morreu segura a porta assim) deixa o fetch pendente até o timeout
 * de TCP do navegador, mais de um minuto. O fetch falso abaixo imita isso:
 * só termina se alguém abortar o sinal.
 */
function fetchQueNuncaResponde(_url: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return new Promise((_, rejeitar) => {
    init?.signal?.addEventListener("abort", () => rejeitar(init.signal?.reason));
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("fetch", vi.fn(fetchQueNuncaResponde));
  // Os componentes registram a falha no console; aqui ela é o esperado.
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

async function passar(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe("home com a API pendurada", () => {
  it("a votação em destaque sai do esqueleto e some em até 10 s", async () => {
    render(<VotacaoDestaque />);
    expect(screen.getByLabelText("Carregando votação")).toBeInTheDocument();

    await passar(10_000);

    expect(screen.queryByLabelText("Carregando votação")).not.toBeInTheDocument();
    expect(screen.queryByText("Onde o voto pela soberania está")).not.toBeInTheDocument();
  });

  it("a prévia do placar troca o esqueleto pelo aviso em até 10 s", async () => {
    render(<RankingPreview />);
    expect(screen.queryByText("Não foi possível carregar a prévia do placar")).not.toBeInTheDocument();

    await passar(10_000);

    expect(screen.getByText("Não foi possível carregar a prévia do placar")).toBeInTheDocument();
  });
});
