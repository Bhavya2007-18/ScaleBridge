import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#0B192C",
          800: "#112240",
          700: "#1E3A5F",
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
