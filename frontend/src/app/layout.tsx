import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Home & Living",
  description: "Rugs, lamps, furniture, candles and more.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="flex min-h-full flex-col font-sans">
        <header className="sticky top-0 z-20 border-b border-line bg-canvas/90 backdrop-blur">
          <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <Link href="/" className="font-serif text-xl tracking-tight sm:text-2xl">
              Home <span className="text-clay-600">&amp;</span> Living
            </Link>
            <div className="flex gap-1 text-sm font-medium sm:gap-2">
              <Link href="/" className="rounded-full px-3 py-1.5 text-muted transition hover:bg-white hover:text-ink">
                Shop
              </Link>
              <Link href="/collections" className="rounded-full px-3 py-1.5 text-muted transition hover:bg-white hover:text-ink">
                Collections
              </Link>
            </div>
          </nav>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">{children}</main>

        <footer className="mt-12 border-t border-line">
          <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-8 text-sm text-muted sm:flex-row sm:justify-between sm:px-6">
            <p className="font-serif text-base text-ink">Home &amp; Living</p>
            <p>Sample catalog · All prices in EUR</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
