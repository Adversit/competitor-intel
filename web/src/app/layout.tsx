import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Molt Intel | Competitive Intelligence",
  description: "AI-powered competitive intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased min-h-screen bg-background`}>
        <Navbar />
        <main className="md:pl-64 min-h-screen">
          <div className="max-w-7xl mx-auto p-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
