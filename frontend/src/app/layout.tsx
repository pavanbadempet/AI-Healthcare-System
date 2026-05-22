import type { Metadata } from "next";
import { Fraunces, Manrope, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const manrope = Manrope({ subsets: ["latin"], variable: '--font-sans' });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: '--font-mono' });

export const metadata: Metadata = {
  title: "AI Healthcare System",
  description: "AI-powered health predictions, streaming medical chat, and personalized health insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`antialiased ${manrope.className} ${fraunces.variable} ${manrope.variable} ${jetbrainsMono.variable}`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
