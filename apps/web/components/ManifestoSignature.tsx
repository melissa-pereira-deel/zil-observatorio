"use client";

import { useState } from "react";
import { Button } from "@/components/ui";

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
      <div className="max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 bg-zil-green text-white flex items-center justify-center font-display text-sm">
            &#10003;
          </div>
          <div>
            <div className="font-semibold text-sm md:text-base">{name}</div>
            <div className="font-mono text-xs text-zil-muted">
              {city || "Brasil"} &middot; n&ordm;{" "}
              {count.toLocaleString("pt-BR")}
            </div>
          </div>
        </div>
        <Button
          variant="secondary"
          fullWidth
          onClick={handleShare}
        >
          {copied ? "\u2713 Copiado" : "Copiar para compartilhar"}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md">
      <p className="text-xs md:text-sm text-zil-soft leading-relaxed mb-5">
        Sua assinatura não é um voto em partido. É um compromisso com o método:
        convergência por dados, transparência radical, e a recusa de aceitar que
        polarização é destino.
      </p>

      <div className="space-y-2 mb-4">
        <input
          type="text"
          placeholder="Nome"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-4 py-3 bg-transparent border-[1.5px] border-zil-divider text-sm font-body text-zil-fg placeholder:text-zil-muted focus:outline-none focus:border-zil-green transition-colors"
        />
        <input
          type="text"
          placeholder="Cidade, Estado"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-full px-4 py-3 bg-transparent border-[1.5px] border-zil-divider text-sm font-body text-zil-fg placeholder:text-zil-muted focus:outline-none focus:border-zil-green transition-colors"
        />
      </div>

      <Button variant="primary" fullWidth onClick={handleSign}>
        Assinar o manifesto
      </Button>

      <p className="font-mono text-xs text-zil-muted mt-3 tracking-wider">
        {count.toLocaleString("pt-BR")} assinaturas
      </p>
    </div>
  );
}
