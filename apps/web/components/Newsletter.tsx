import { Button, Icone } from "@/components/ui";
import { NEWSLETTER_URL } from "@/lib/links";

/**
 * Chamada para a newsletter no Substack: um texto curto e um primário que
 * abre a inscrição em outra aba. Sem formulário próprio, sem contador. Com
 * o endereço ainda vazio, a frase diz que a newsletter está a caminho.
 */
export function Newsletter() {
  return (
    <div className="w-full max-w-md grid gap-6 justify-items-center">
      <p className="text-texto text-zil-texto-2">
        Uma newsletter sobre soberania industrial, sem partido: o que o Congresso votou, o que a Bússola mediu e o que mudou no
        placar. Sem ruído, sem spam.
      </p>
      {NEWSLETTER_URL ? (
        <Button href={NEWSLETTER_URL} variante="primario" tamanho="l" target="_blank" rel="noopener noreferrer">
          Assinar a newsletter
          <Icone nome="externo" />
        </Button>
      ) : (
        <p className="text-texto-s text-zil-texto-2">A newsletter abre em breve, no Substack.</p>
      )}
    </div>
  );
}
