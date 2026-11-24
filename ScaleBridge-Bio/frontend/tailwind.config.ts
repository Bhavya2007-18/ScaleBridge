import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      colors: {
        obsidian: {
          950: "#09090B",
          900: "#111114",
          850: "#16161A",
          800: "#18181B",
          700: "#27272A",
        },
        bio: {
          400: "#34D399",
          500: "#10B981",
        },
      },
    },
  },
  plugins: [],
};

export default config;
