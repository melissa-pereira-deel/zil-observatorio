/** @type {import('tailwindcss').Config} */

// Tokens do ZIL Interface (design system). Os valores vivem como variáveis
// CSS em app/globals.css, com os dois temas; aqui só se dá nome Tailwind a
// cada um. Trocar um valor é editar o globals.css, não este arquivo.
//
// Espaçamento: a escala padrão do Tailwind já é a grade de 4px do sistema
// (espaco-6 = `6` = 24px), então não há escala própria.

const v = (nome) => `var(--${nome})`;

module.exports = {
  // lib/ entra porque CATEGORIA_COR (lib/categorias.ts) nomeia classes de cor.
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        zil: {
          fundo: v("fundo"),
          "superficie-1": v("superficie-1"),
          "superficie-2": v("superficie-2"),
          "superficie-3": v("superficie-3"),
          "superficie-4": v("superficie-4"),
          texto: v("texto"),
          "texto-2": v("texto-2"),
          "texto-3": v("texto-3"),
          inverso: v("inverso-fundo"),
          "inverso-hover": v("inverso-fundo-hover"),
          "inverso-texto": v("inverso-texto"),
          polegar: v("polegar"),
          vidro: v("vidro"),
          "vidro-forte": v("vidro-forte"),
          "vidro-solido": v("vidro-solido"),
          "vidro-hover": v("vidro-hover"),
          "vidro-ativo": v("vidro-ativo"),
          separador: v("separador"),
          veu: v("veu"),
          foco: v("foco"),
          "foco-halo": v("foco-halo"),
          alinhado: v("alinhado"),
          "alinhado-fundo": v("alinhado-fundo"),
          contra: v("contra"),
          "contra-fundo": v("contra-fundo"),
          neutro: v("neutro"),
          "neutro-fundo": v("neutro-fundo"),
          "brasil-verde": v("brasil-verde"),
          "brasil-amarelo": v("brasil-amarelo"),
          "brasil-azul": v("brasil-azul"),
          "brasil-vermelho": v("brasil-vermelho"),
          "brasil-ciano": v("brasil-ciano"),
          "brasil-roxo": v("brasil-roxo"),
        },
      },
      // Uma família só: Archivo, carregada por next/font em app/layout.tsx
      // (variável --font-sans). A leitura longa também é Archivo, por
      // decisão editorial de 2026-10-29.
      fontFamily: {
        sans: ["var(--font-sans)", '"SF Pro Text"', "-apple-system", "system-ui", '"Segoe UI"', "sans-serif"],
        mono: ["ui-monospace", '"SF Mono"', "Menlo", "Consolas", "monospace"],
      },
      // Os estilos de texto do sistema, pelo nome: `text-titulo-2`,
      // `text-texto-s`. Peso e tracking vêm junto.
      fontSize: {
        "display-xl": ["96px", { lineHeight: "92px", letterSpacing: "-0.035em", fontWeight: "600" }],
        "display-l": ["72px", { lineHeight: "72px", letterSpacing: "-0.03em", fontWeight: "600" }],
        "display-m": ["56px", { lineHeight: "58px", letterSpacing: "-0.025em", fontWeight: "600" }],
        "titulo-1": ["40px", { lineHeight: "46px", letterSpacing: "-0.02em", fontWeight: "600" }],
        "titulo-2": ["32px", { lineHeight: "38px", letterSpacing: "-0.015em", fontWeight: "600" }],
        "titulo-3": ["24px", { lineHeight: "30px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "titulo-4": ["20px", { lineHeight: "26px", letterSpacing: "-0.005em", fontWeight: "600" }],
        "texto-l": ["21px", { lineHeight: "32px", letterSpacing: "-0.005em", fontWeight: "400" }],
        texto: ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "texto-ui": ["16px", { lineHeight: "22px", letterSpacing: "-0.005em", fontWeight: "500" }],
        "texto-s": ["15px", { lineHeight: "20px", fontWeight: "400" }],
        legenda: ["13px", { lineHeight: "18px", letterSpacing: "0.005em", fontWeight: "500" }],
        rotulo: ["13px", { lineHeight: "16px", letterSpacing: "0.04em", fontWeight: "600" }],
        manchete: ["48px", { lineHeight: "54px", letterSpacing: "-0.02em", fontWeight: "600" }],
        leitura: ["19px", { lineHeight: "30px", fontWeight: "400" }],
        citacao: ["28px", { lineHeight: "38px", letterSpacing: "-0.015em", fontWeight: "500" }],
        "numero-xl": ["80px", { lineHeight: "80px", letterSpacing: "-0.04em", fontWeight: "600" }],
        "numero-l": ["44px", { lineHeight: "48px", letterSpacing: "-0.03em", fontWeight: "600" }],
      },
      borderRadius: {
        xs: "8px",
        s: "12px",
        m: "14px",
        l: "20px",
        xl: "28px",
        pilula: "999px",
      },
      boxShadow: {
        polegar: v("sombra-polegar"),
        flutuante: v("sombra-flutuante"),
        elevada: v("sombra-elevada"),
        halo: `0 0 0 3px ${v("foco-halo")}`,
      },
      transitionDuration: {
        toque: "120ms",
        padrao: "220ms",
        lenta: "420ms",
      },
      transitionTimingFunction: {
        padrao: "cubic-bezier(0.2, 0.8, 0.2, 1)",
        mola: "cubic-bezier(0.34, 1.36, 0.64, 1)",
      },
      scale: {
        toque: "0.97",
      },
      maxWidth: {
        leitura: "68ch",
      },
      keyframes: {
        "zil-gira": { to: { transform: "rotate(360deg)" } },
        "zil-surge": {
          from: { opacity: "0", transform: "scale(.96) translateY(-4px)" },
          to: { opacity: "1", transform: "none" },
        },
        "zil-brilho": {
          from: { backgroundPosition: "150% 0" },
          to: { backgroundPosition: "-50% 0" },
        },
        "zil-respira": { "0%, 100%": { opacity: "1" }, "50%": { opacity: ".45" } },
      },
      animation: {
        "zil-gira": "zil-gira .8s linear infinite",
        "zil-surge": "zil-surge 220ms cubic-bezier(0.2, 0.8, 0.2, 1)",
        "zil-brilho": "zil-brilho 1.4s ease-in-out infinite",
        "zil-respira": "zil-respira 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
