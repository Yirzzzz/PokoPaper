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
        ink: "#eef4dc",
        mist: "#4f5b42",
        brand: "#7abf63",
        ember: "#ef737d",
        shell: "#f6f2df",
        panel: "rgba(255, 248, 229, 0.78)",
      },
      boxShadow: {
        glow: "0 20px 80px rgba(112, 198, 112, 0.16)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top left, rgba(112,198,112,0.2), transparent 25%), radial-gradient(circle at bottom right, rgba(239,115,125,0.12), transparent 30%)",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
