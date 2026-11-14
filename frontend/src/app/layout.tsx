import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Home & Living Catalog",
  description: "Rugs, lamps, furniture, candles and more.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="flex min-h-full flex-col font-sans">
        <header className="border-b border-stone-200 bg-white">
          <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Home &amp; Living
            </Link>
            <div className="flex gap-5 text-sm font-medium text-stone-600">
              <Link href="/" className="hover:text-stone-900">Products</Link>
              <Link href="/collections" className="hover:text-stone-900">Collections</Link>
            </div>
          </nav>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">{children}</main>

        <footer className="border-t border-stone-200 bg-white">
          <p className="mx-auto max-w-7xl px-4 py-6 text-sm text-stone-500">
            Sample catalog. All prices in EUR.
          </p>
        </footer>
      </body>
    </html>
  );
}
