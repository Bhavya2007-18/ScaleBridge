import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScaleBridge Bio — Bioprocess Scale-Up & Intelligence Platform",
  description:
    "Vendor-agnostic, process-aware decision-support platform for microbial fermentation scale-up readiness and technology transfer.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
