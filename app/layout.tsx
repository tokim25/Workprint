import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Workprint",
  description: "Turn project evidence into AI-assisted insights you can inspect.",
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
