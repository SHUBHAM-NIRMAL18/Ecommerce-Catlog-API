import { ProductGridSkeleton } from "@/components/States";

export default function Loading() {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">Loading products…</span>
      <div className="mb-8 border-b border-line pb-6">
        <div className="h-3 w-20 animate-pulse rounded bg-line" />
        <div className="mt-3 h-9 w-56 animate-pulse rounded bg-line" />
        <div className="mt-4 h-12 max-w-2xl animate-pulse rounded-full bg-white ring-1 ring-line" />
      </div>
      <div className="grid gap-8 lg:grid-cols-[250px_1fr]">
        <div className="hidden flex-col gap-3 lg:flex">
          {Array.from({ length: 10 }, (_, i) => (
            <div key={i} className="h-5 animate-pulse rounded bg-line" style={{ width: `${60 + ((i * 17) % 35)}%` }} />
          ))}
        </div>
        <ProductGridSkeleton />
      </div>
    </div>
  );
}
