import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans", "system-ui", "sans-serif"],
      },
      colors: {
        hb: {
          cream: "#FFF9E3",
          amber: "#FFC83D",
          amberHover: "#F5B81D",
          brown: "#2B2208",
          muted: "#6B5B2E",
          border: "#EFE4BE",
          lowBg: "#DCFCE7",
          lowText: "#14532D",
          modBg: "#FEF3C7",
          modText: "#78350F",
          highBg: "#FEE2E2",
          highText: "#7F1D1D",
          skipBg: "#F1F5F9",
          skipText: "#475569",
        },
      },
      borderRadius: {
        card: "20px",
      },
      boxShadow: {
        warm: "0 10px 30px -10px rgba(43, 34, 8, 0.08), 0 2px 8px -2px rgba(43, 34, 8, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
