import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

const satoshi = localFont({
  src: "../../public/fonts/Satoshi-Variable.woff2",
  variable: "--font-display",
  display: "swap",
  weight: "300 900",
});

const geist = localFont({
  src: "../../public/fonts/GeistVF.woff2",
  variable: "--font-body",
  display: "swap",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "SwampFindr",
  description:
    "AI-powered housing search for University of Florida students. Find your perfect off-campus home near UF.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${satoshi.variable} ${geist.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
