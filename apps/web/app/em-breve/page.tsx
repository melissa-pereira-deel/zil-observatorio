import { Aviso, Button, Painel } from "@/components/ui";

export const metadata = {
  title: "Ranking ainda não publicado — ZIL Observatório",
  description: "O ranking de parlamentares depende de curadoria editorial que ainda não tem base suficiente.",
};

/**
 * Página que recebe quem chega a /ranking ou /parlamentar enquanto o placar
 * não é público (ver lib/flags.ts): explica o motivo e aponta a saída.
 */
export default function EmBrevePage() {
  return (
    <div className="zil-container pt-10 md:pt-16">
      <Painel>
        <p className="text-rotulo uppercase text-zil-texto-2">Placar</p>
        <h1 className="text-titulo-1 md:text-display-m max-w-[18ch]">O ranking ainda não está publicado</h1>

        <div className="grid gap-5 max-w-[60ch] mt-4 text-left">
          <p className="text-texto text-zil-texto-2">
            O Score ZIL só considera votações cuja <em>direção esperada</em> foi definida por uma pessoa: decidir se votar SIM numa pauta
            favorece ou não a soberania industrial é um juízo editorial, nunca automático.
          </p>

          <Aviso tom="neutro" titulo="7 votações classificadas, nenhuma validada">
            Existem hoje <strong>7 votações classificadas</strong>, e todas estão marcadas como não validadas nos arquivos do projeto.
            Dessas, apenas <strong>4 alimentam o score</strong>: as outras três foram decididas por votação simbólica, em que a Câmara
            proclama só o resultado e não registra o voto de cada deputado. Com essa base, o ranking não discrimina: a maior parte dos
            parlamentares empataria na mesma nota.
          </Aviso>

          <p className="text-texto text-zil-texto-2">
            Publicar um ranking assim produziria um número com aparência de precisão e sem lastro — exatamente o oposto do que esta
            plataforma se propõe a fazer. Ele entra no ar quando a curadoria sustentar, e não antes.
          </p>

          <p className="text-texto text-zil-texto-2">
            Enquanto isso, o que já está disponível é verificável: as proposições monitoradas, com a ementa jurídica traduzida para linguagem
            simples a partir do texto real das leis citadas.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-3 mt-4">
          <Button href="/proposicoes" variante="primario">
            Ver proposições
          </Button>
          <Button href="/metodologia" variante="secundario">
            Como o score é calculado
          </Button>
        </div>
      </Painel>
    </div>
  );
}
