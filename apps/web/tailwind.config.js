/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        zil: {
          bg: "#F0EBE0",
          fg: "#1A1714",
          soft: "#5C564C",
          muted: "#8A8478",
          green: "#1B6B3A",
          "green-dark": "#0E3D20",
          gold: "#C4940A",
          "gold-dark": "#8C6A08",
          blue: "#1A3E5C",
          divider: "#D6CFC3",
          card: "#E8E2D6",
        },
      },
      fontFamily: {
        display: ['"Archivo Black"', "sans-serif"],
        body: ['"Archivo"', "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
