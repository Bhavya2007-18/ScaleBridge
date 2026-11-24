import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-space-grotesk)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      colors: {
        abyss: "#03060C",
        navy: {
          950: "#040812",
          900: "#080D18",
          800: "#0F172A",
          700: "#1E293B",
        },
        cyan: {
          400: "#22D3EE",
          500: "#06B6D4",
          sky: "#38BDF8",
        },
        bio: {
          400: "#34D399",
          500: "#10B981",
        },
        teal: {
          600: "#0D9488",
          500: "#14B8A6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
