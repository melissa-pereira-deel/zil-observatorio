"use client";

import { useState } from "react";
import { Aviso, Button, Campo } from "@/components/ui";

/**
 * Assinatura do manifesto: dois campos sem borda (ZIL Interface › Campo) e
 * um primário em bloco. Depois de assinar, confirma em Aviso `alinhado` e
 * oferece copiar o texto para compartilhar.
 */

export function ManifestoSignature() {
  const [signed, setSigned] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [count, setCount] = useState(148207);
  const [copied, setCopied] = useState(false);

  const handleSign = () => {
    if (name.trim().length > 1) {
      setSigned(true);
      setCount((c) => c + 1);
    }
  };

  const handleShare = () => {
    const text = `Assinei o Manifesto ZIL.\n\nO Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. O que falta não é capacidade — é convergência.\n\n#ManifestoZIL`;
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    });
  };

  if (signed) {
    return (
      <div className="w-full max-w-md grid gap-4 text-left">
        <Aviso tom="alinhado" titulo={name}>
          <span className="zil-num">
            {city || "Brasil"} &middot; n&ordm; {count.toLocaleString("pt-BR")}
          </span>
        </Aviso>
        <Button variante="secundario" bloco onClick={handleShare}>
          {copied ? "Copiado" : "Copiar para compartilhar"}
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md grid gap-5 text-left">
      <p className="text-texto text-zil-texto-2">
        Sua assinatura não é um voto em partido. É um compromisso com o método: convergência por dados, transparência radical, e a recusa de
        aceitar que polarização é destino.
      </p>

      <div className="grid gap-3">
        <Campo rotulo="Nome" type="text" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} />
        <Campo rotulo="Cidade, Estado" type="text" autoComplete="address-level2" value={city} onChange={(e) => setCity(e.target.value)} />
      </div>

      <Button variante="primario" bloco tamanho="l" onClick={handleSign}>
        Assinar o manifesto
      </Button>

      <p className="text-texto-s text-zil-texto-2 zil-num">{count.toLocaleString("pt-BR")} assinaturas</p>
    </div>
  );
}
