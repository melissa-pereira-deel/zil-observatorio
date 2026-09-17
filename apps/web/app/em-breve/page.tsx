import { Button, Callout, SectionHeader } from "@/components/ui";

export const metadata = {
  title: "Ranking ainda não publicado — ZIL Observatório",
  description:
    "O ranking de parlamentares depende de curadoria editorial que ainda não tem base suficiente.",
};

export default function EmBrevePage() {
  return (
    <main className="zil-container py-16 md:py-24">
      <SectionHeader number="—" title="O ranking ainda não está publicado" />

      <div className="max-w-2xl space-y-5 text-sm text-zil-soft leading-relaxed mt-8">
        <p>
          O Score ZIL só considera votações cuja <em>direção esperada</em> foi
          definida por uma pessoa: decidir se votar SIM numa pauta favorece ou
          não a soberania industrial é um juízo editorial, nunca automático.
        </p>

        <Callout>
          Existem hoje <strong>7 votações classificadas</strong>, e todas estão
          marcadas como não validadas nos arquivos do projeto. Com essa base, o
          ranking não discrimina: a maior parte dos parlamentares empataria na
          mesma nota.
        </Callout>

        <p>
          Publicar um ranking assim produziria um número com aparência de
          precisão e sem lastro — exatamente o oposto do que esta plataforma se
          propõe a fazer. Ele entra no ar quando a curadoria sustentar, e não
          antes.
        </p>

        <p>
          Enquanto isso, o que já está disponível é verificável: as proposições
          monitoradas, com a ementa jurídica traduzida para linguagem simples a
          partir do texto real das leis citadas.
        </p>

        <div className="flex flex-wrap gap-2 pt-2">
          <Button href="/proposicoes" variant="primary" size="sm">
            Ver proposições
          </Button>
          <Button href="/metodologia" variant="ghost" size="sm">
            Como o score é calculado
          </Button>
        </div>
      </div>
    </main>
  );
}
