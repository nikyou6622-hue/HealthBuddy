import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "var(--font-devanagari)", "system-ui", "sans-serif"],
      },
      colors: {
        hb: {
          canvas: "var(--hb-canvas)",
          surface: "var(--hb-surface)",
          subtle: "var(--hb-subtle)",
          border: "var(--hb-border)",
          ink: "var(--hb-ink)",
          muted: "var(--hb-ink-muted)",
          accent: "var(--hb-accent)",
          accentInk: "var(--hb-accent-ink)",
          accentSoft: "var(--hb-accent-soft)",
          cta: "var(--hb-cta-bg)",
          ctaInk: "var(--hb-cta-ink)",
          lowBg: "var(--hb-low-bg)",
          lowInk: "var(--hb-low-ink)",
          lowBorder: "var(--hb-low-border)",
          modBg: "var(--hb-mod-bg)",
          modInk: "var(--hb-mod-ink)",
          modBorder: "var(--hb-mod-border)",
          highBg: "var(--hb-high-bg)",
          highInk: "var(--hb-high-ink)",
          highBorder: "var(--hb-high-border)",
          skipBg: "var(--hb-skip-bg)",
          skipInk: "var(--hb-skip-ink)",
          skipBorder: "var(--hb-skip-border)",
          // Legacy aliases kept for backwards compatibility
          cream: "var(--hb-subtle)",
          amber: "var(--hb-cta-bg)",
          amberHover: "var(--hb-accent)",
          brown: "var(--hb-ink)",
          lowText: "var(--hb-low-ink)",
          modText: "var(--hb-mod-ink)",
          highText: "var(--hb-high-ink)",
          skipText: "var(--hb-skip-ink)",
        },
      },
      borderRadius: {
        md: "var(--hb-radius-md)",
        lg: "var(--hb-radius-lg)",
        card: "var(--hb-radius-lg)",
      },
      boxShadow: {
        sm: "var(--hb-shadow-sm)",
        md: "var(--hb-shadow-md)",
        warm: "var(--hb-shadow-sm)",
      },
    },
  },
  plugins: [],
};

export default config;
