import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AETHERIS — Multi-Agent Research",
  description: "AI-powered multi-agent research intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
