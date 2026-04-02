/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        zil: {
          // ── Core palette ──
          bg: "#F0EBE0",
          fg: "#1A1714",
          soft: "#5C564C",
          muted: "#8A8478",

          // ── Greens (sovereignty / positive) ──
          green: "#1B6B3A",
          "green-dark": "#0E3D20",
          "green-light": "#E8F0EA",

          // ── Golds (neutral / accent) ──
          gold: "#C4940A",
          "gold-dark": "#8C6A08",
          "gold-light": "#FDF6E3",

          // ── Signal colors ──
          orange: "#C4760A",
          "orange-light": "#FEF0EE",
          red: "#B54A3A",

          // ── Surfaces ──
          blue: "#1A3E5C",
          divider: "#D6CFC3",
          card: "#E8E2D6",
          white: "#FDFBF7",
        },
      },
      fontFamily: {
        display: ['"Archivo Black"', "sans-serif"],
        body: ['"Archivo"', "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
      },
      letterSpacing: {
        "widest-xl": "0.25em",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
