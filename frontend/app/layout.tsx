import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HealthBuddy — Health Risk Assessment",
  description:
    "Educational, India-focused multi-disease health screening and care guidance platform.",
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
    <html lang="en">
      <body className="min-h-screen bg-[#FFF9E3] text-[#2B2208] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
