import Link from "next/link";

import type { SearchParams } from "@/lib/types";

type Props = {
  page: number;
  totalPages: number;
  total: number;
  limit: number;
  searchParams: SearchParams;
  basePath?: string;
};

function hrefFor(basePath: string, searchParams: SearchParams, page: number) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    const first = Array.isArray(value) ? value[0] : value;
    if (first && key !== "page") params.set(key, first);
  }
  if (page > 1) params.set("page", String(page));
  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}

function pageNumbers(page: number, totalPages: number): (number | "gap")[] {
  const wanted = new Set([1, totalPages, page - 1, page, page + 1]);
  const pages = [...wanted].filter((n) => n >= 1 && n <= totalPages).sort((a, b) => a - b);
  return pages.flatMap((n, i) => (i > 0 && n - pages[i - 1] > 1 ? ["gap" as const, n] : [n]));
}

const base = "flex h-10 min-w-10 items-center justify-center rounded-full px-3 text-sm transition";

export function Pagination({ page, totalPages, total, limit, searchParams, basePath = "/" }: Props) {
  if (total === 0) return null;

  const first = Math.min((page - 1) * limit + 1, total);
  const last = Math.min(page * limit, total);
  const summary = page <= totalPages ? `Showing ${first}–${last} of ${total}` : `Page ${page} is past the last page`;

  return (
    <nav aria-label="Pagination" className="mt-12 flex flex-col items-center gap-4">
      <p className="text-sm text-muted">{summary}</p>
      {totalPages > 1 && (
        <ul className="flex flex-wrap items-center justify-center gap-1">
          <li>
            {page > 1 ? (
              <Link href={hrefFor(basePath, searchParams, Math.min(page - 1, totalPages))} className={`${base} bg-white ring-1 ring-line hover:text-clay-700 hover:ring-clay-600`}>
                Previous
              </Link>
            ) : (
              <span className={`${base} cursor-not-allowed text-muted/40`}>Previous</span>
            )}
          </li>
          {pageNumbers(Math.min(page, totalPages), totalPages).map((n, i) =>
            n === "gap" ? (
              <li key={`gap-${i}`} className="px-1 text-muted">…</li>
            ) : (
              <li key={n}>
                {n === page ? (
                  <span aria-current="page" className={`${base} bg-ink font-medium text-white`}>{n}</span>
                ) : (
                  <Link href={hrefFor(basePath, searchParams, n)} className={`${base} bg-white ring-1 ring-line hover:text-clay-700 hover:ring-clay-600`}>
                    {n}
                  </Link>
                )}
              </li>
            ),
          )}
          <li>
            {page < totalPages ? (
              <Link href={hrefFor(basePath, searchParams, page + 1)} className={`${base} bg-white ring-1 ring-line hover:text-clay-700 hover:ring-clay-600`}>
                Next
              </Link>
            ) : (
              <span className={`${base} cursor-not-allowed text-muted/40`}>Next</span>
            )}
          </li>
        </ul>
      )}
    </nav>
  );
}
