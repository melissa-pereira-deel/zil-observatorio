import { type ComponentPropsWithoutRef, useId } from "react";

/**
 * Campo — rótulo, entrada de 52px em `superficie-2` com raio 16 e halo de
 * foco, e texto de ajuda (ZIL Interface › Campo). Erro diz o que corrigir e
 * fica em `contra`; `ok` em `alinhado`.
 */

interface CampoProps extends Omit<ComponentPropsWithoutRef<"input">, "id" | "className"> {
  rotulo: string;
  ajuda?: React.ReactNode;
  estado?: "padrao" | "erro" | "ok";
  className?: string;
}

export const ENTRADA =
  "h-[52px] px-[18px] rounded-2xl bg-zil-superficie-2 text-zil-texto text-[17px] outline-none placeholder:text-zil-texto-3 transition-[background-color,box-shadow] duration-padrao ease-padrao hover:bg-zil-superficie-3 focus:bg-zil-superficie-1 focus:shadow-halo";

export function Campo({ rotulo, ajuda, estado = "padrao", className = "", ...props }: CampoProps) {
  const id = useId();
  const ajudaId = `${id}-ajuda`;
  return (
    <div className={`grid gap-1.5 ${className}`}>
      <label htmlFor={id} className="text-[15px] leading-5 font-semibold">
        {rotulo}
      </label>
      <input
        id={id}
        aria-describedby={ajuda ? ajudaId : undefined}
        aria-invalid={estado === "erro" || undefined}
        className={`${ENTRADA} ${estado === "erro" ? "shadow-[0_0_0_2px_var(--contra)]" : ""}`}
        {...props}
      />
      {ajuda && (
        <p id={ajudaId} className={`text-[14px] leading-[18px] ${estado === "erro" ? "text-zil-contra" : estado === "ok" ? "text-zil-alinhado" : "text-zil-texto-2"}`}>
          {ajuda}
        </p>
      )}
    </div>
  );
}
