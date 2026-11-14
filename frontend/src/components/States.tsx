import Link from "next/link";
import type { ReactNode } from "react";

type StateProps = {
  title: string;
  message: ReactNode;
  icon?: "search" | "alert" | "box";
  children?: ReactNode;
};

const ICONS = {
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  alert: (
    <>
      <path d="M12 9v4m0 4h.01" />
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    </>
  ),
  box: (
    <>
      <path d="M21 8 12 3 3 8v8l9 5 9-5V8Z" />
      <path d="m3 8 9 5 9-5M12 13v8" />
    </>
  ),
};

export function StateMessage({ title, message, icon = "box", children }: StateProps) {
  return (
    <div className="flex flex-col items-center rounded-2xl bg-white px-6 py-14 text-center shadow-sm ring-1 ring-line">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-clay-50 text-clay-600">
        <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          {ICONS[icon]}
        </svg>
      </div>
      <h2 className="mt-4 font-serif text-2xl">{title}</h2>
      <div className="mt-2 max-w-md text-muted">{message}</div>
      {children && <div className="mt-6 flex flex-wrap justify-center gap-3">{children}</div>}
    </div>
  );
}

export function PrimaryLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-clay-700">
      {children}
    </Link>
  );
}

export function SecondaryLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="rounded-full bg-white px-5 py-2.5 text-sm font-medium ring-1 ring-line transition hover:ring-clay-600">
      {children}
    </Link>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <ul aria-hidden className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <li key={i} className="overflow-hidden rounded-2xl bg-white ring-1 ring-line">
          <div className="aspect-square animate-pulse bg-line" />
          <div className="flex flex-col gap-2 p-4">
            <div className="h-3 w-1/3 animate-pulse rounded bg-line" />
            <div className="h-5 w-4/5 animate-pulse rounded bg-line" />
            <div className="h-4 w-1/4 animate-pulse rounded bg-line" />
            <div className="mt-3 h-5 w-1/3 animate-pulse rounded bg-line" />
          </div>
        </li>
      ))}
    </ul>
  );
}
