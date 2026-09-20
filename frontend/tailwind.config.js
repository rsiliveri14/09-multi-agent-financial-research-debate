/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "ui-sans-serif", "system-ui"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        ink: "#070b14",
        panel: "#10182a",
        line: "#243049",
        accent: "#3ee0c4",
        bull: "#3ee0c4",
        bear: "#ff5d73",
        warn: "#f5c15d",
      },
    },
  },
  plugins: [],
};
