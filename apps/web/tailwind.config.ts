import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#080b14",
        mist: "#b8c2e0",
        brand: "#4ecdc4",
        ember: "#ff8a5b",
        shell: "#121826",
        panel: "rgba(16, 22, 36, 0.72)",
      },
      boxShadow: {
        glow: "0 20px 80px rgba(78, 205, 196, 0.12)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top left, rgba(78,205,196,0.18), transparent 25%), radial-gradient(circle at bottom right, rgba(255,138,91,0.16), transparent 30%)",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
