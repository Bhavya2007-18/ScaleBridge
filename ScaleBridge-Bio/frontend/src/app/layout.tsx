import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ScaleBridge.bio — Bioprocess Digital Twin & Scale-Up Engineering Platform",
  description:
    "Deterministic bioprocess scale-up engineering, telemetry normalization, vessel capability envelopes, and audit-ready technology transfer.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} dark scroll-smooth`}
    >
      <body className="min-h-screen bg-[#09090B] text-[#FAFAFA] font-sans antialiased selection:bg-white/15 selection:text-white">
        {children}
      </body>
    </html>
  );
}
