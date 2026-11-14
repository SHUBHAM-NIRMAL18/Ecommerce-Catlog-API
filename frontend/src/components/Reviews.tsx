"use client";

import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Page, Review } from "@/lib/types";

type Sort = "newest" | "helpful";

export function Stars({ rating, size = "text-base" }: { rating: number; size?: string }) {
  const filled = Math.round(rating);
  return (
    <span aria-hidden className={`tracking-tight ${size}`}>
      <span className="text-amber-500">{"★".repeat(filled)}</span>
      <span className="text-line">{"★".repeat(5 - filled)}</span>
    </span>
  );
}

function ReviewItem({ review }: { review: Review }) {
  return (
    <li className="flex flex-col gap-2 py-5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <Stars rating={review.rating} />
        <span className="sr-only">{`Rated ${review.rating} out of 5`}</span>
        <h3 className="font-medium">{review.title}</h3>
      </div>
      {review.body && <p className="leading-relaxed text-muted">{review.body}</p>}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <time dateTime={review.createdAt}>{formatDate(review.createdAt)}</time>
        {review.verifiedPurchase && <span className="font-medium text-emerald-700">✓ Verified purchase</span>}
        {review.helpfulCount > 0 && (
          <span>
            {review.helpfulCount} {review.helpfulCount === 1 ? "person" : "people"} found this helpful
          </span>
        )}
      </div>
    </li>
  );
}

export function Reviews({
  slug,
  average,
  initial,
}: {
  slug: string;
  average: number | null;
  initial: Page<Review> | null;
}) {
  const [sort, setSort] = useState<Sort>("newest");
  const [items, setItems] = useState<Review[]>(initial?.items ?? []);
  const [page, setPage] = useState(initial?.page ?? 0);
  const [totalPages, setTotalPages] = useState(initial?.totalPages ?? 0);
  const [loading, setLoading] = useState<number | null>(null);
  const [failed, setFailed] = useState<{ page: number; sort: Sort; message: string } | null>(
    initial ? null : { page: 1, sort: "newest", message: "Reviews couldn't be loaded right now." },
  );
  const total = initial?.total ?? 0;

  async function load(nextPage: number, nextSort: Sort) {
    setLoading(nextPage);
    setFailed(null);
    try {
      const result = await api.reviews(slug, nextPage, nextSort);
      setItems((current) => {
        if (nextPage === 1) return result.items;
        const seen = new Set(current.map((r) => r.id));
        return [...current, ...result.items.filter((r) => !seen.has(r.id))];
      });
      setPage(result.page);
      setTotalPages(result.totalPages);
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Reviews couldn't be loaded right now.";
      setFailed({ page: nextPage, sort: nextSort, message });
    } finally {
      setLoading(null);
    }
  }

  function changeSort(next: Sort) {
    if (next === sort) return;
    setSort(next);
    load(1, next);
  }

  return (
    <section id="reviews" aria-labelledby="reviews-title" className="scroll-mt-24">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
        <div className="flex flex-col gap-1">
          <h2 id="reviews-title" className="font-serif text-2xl">Customer reviews</h2>
          {average !== null && total > 0 ? (
            <p className="flex items-center gap-2">
              <Stars rating={average} size="text-lg" />
              <span className="font-semibold">{average.toFixed(1)}</span>
              <span className="text-sm text-muted">
                out of 5 · {total} {total === 1 ? "review" : "reviews"}
              </span>
            </p>
          ) : (
            initial && <p className="text-sm text-muted">No reviews yet. Be the first to share what you think.</p>
          )}
        </div>
        {total > 1 && (
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted">Sort by</span>
            <select
              value={sort}
              onChange={(e) => changeSort(e.target.value as Sort)}
              disabled={loading !== null}
              className="rounded-full bg-white px-3 py-1.5 ring-1 ring-line"
            >
              <option value="newest">Newest</option>
              <option value="helpful">Most helpful</option>
            </select>
          </label>
        )}
      </div>

      {items.length > 0 && (
        <ul className={`divide-y divide-line transition-opacity ${loading === 1 ? "opacity-50" : ""}`}>
          {items.map((review) => (
            <ReviewItem key={review.id} review={review} />
          ))}
        </ul>
      )}

      {failed && (
        <p role="alert" className="mt-4 flex flex-wrap items-center gap-3 text-sm text-clay-700">
          {failed.message}
          <button type="button" onClick={() => load(failed.page, failed.sort)} className="font-medium underline">
            Try again
          </button>
        </p>
      )}

      {!failed && page < totalPages && (
        <div className="mt-4 flex flex-col items-center gap-2">
          <button
            type="button"
            onClick={() => load(page + 1, sort)}
            disabled={loading !== null}
            className="rounded-full bg-white px-5 py-2.5 text-sm font-medium ring-1 ring-line transition hover:ring-clay-600 disabled:opacity-60"
          >
            {loading !== null ? "Loading…" : "Load more reviews"}
          </button>
          <span className="text-xs text-muted">
            Showing {items.length} of {total}
          </span>
        </div>
      )}
    </section>
  );
}
