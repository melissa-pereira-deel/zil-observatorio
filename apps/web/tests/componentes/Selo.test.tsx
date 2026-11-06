import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Selo } from "@/components/ui";
import { classesDeAlinhamento } from "../helpers/paleta";
import { axe } from "../setup/axe";

describe("Selo", () => {
  it("mostra o texto e esconde o ponto do leitor de tela", () => {
    const { container, rerender } = render(
      <h2>
        <Selo ponto>Pronta para Pauta</Selo>
      </h2>,
    );
    expect(screen.getByText("Pronta para Pauta")).toBeInTheDocument();
    // getByText acha texto sob aria-hidden; o nome do heading, não. Sem esta
    // conferência, o Selo inteiro poderia sumir do leitor de tela.
    expect(screen.getByRole("heading", { name: "Pronta para Pauta" })).toBeInTheDocument();
    const seletorDoPonto = "span > span[aria-hidden='true']";
    expect(container.querySelector(seletorDoPonto)).not.toBeNull();

    rerender(
      <h2>
        <Selo>Pronta para Pauta</Selo>
      </h2>,
    );
    expect(container.querySelector(seletorDoPonto)).toBeNull();
  });

  it("põe o texto inteiro no title quando o conteúdo é string", () => {
    render(<Selo>Aguardando Designação de Relator(a)</Selo>);
    expect(screen.getByTitle("Aguardando Designação de Relator(a)")).toBeInTheDocument();
  });

  it("aplica o par cor/fundo do tom", () => {
    const { container } = render(<Selo tom="neutro">Não validado</Selo>);
    expect(container.firstElementChild).toHaveClass("bg-zil-neutro-fundo", "text-zil-neutro");
  });

  it("o tom padrão não usa cor de alinhamento", () => {
    const { container } = render(<Selo>Indústria</Selo>);
    expect(container.firstElementChild).toHaveClass("bg-zil-superficie-2", "text-zil-texto-2");
    expect(classesDeAlinhamento(container)).toEqual([]);
  });

  it("não tem violações de acessibilidade", async () => {
    const { container } = render(
      <p>
        Situação: <Selo tom="neutro" ponto>Não validado</Selo>
      </p>,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
