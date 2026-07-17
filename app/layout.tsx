import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Workprint",
  description: "See what you did, what AI did, and how the work came together.",
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
