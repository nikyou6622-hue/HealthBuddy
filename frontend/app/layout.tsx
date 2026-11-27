import type { Metadata } from "next";
import { Noto_Sans_Devanagari, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-devanagari",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HealthBuddy — Clinical Health Risk Assessment",
  description:
    "Educational, India-focused multi-disease clinical decision support, risk screening, and verified care matching platform.",
  icons: {
    icon: "/healthbuddy-logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${plusJakarta.variable} ${notoDevanagari.variable}`}>
      <body className="min-h-screen bg-hb-canvas text-hb-ink font-sans text-[15px] leading-relaxed antialiased">
        {children}
      </body>
    </html>
  );
}
