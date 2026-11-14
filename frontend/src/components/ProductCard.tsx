import Image from "next/image";
import Link from "next/link";

import { formatPrice, formatPriceParts } from "@/lib/format";
import type { ProductCard as Product } from "@/lib/types";

export function ImagePlaceholder({ label = "No image yet" }: { label?: string }) {
  return (
    <div className="flex aspect-square w-full flex-col items-center justify-center gap-2 bg-gradient-to-br from-clay-50 to-line text-muted">
      <svg viewBox="0 0 24 24" className="h-10 w-10 opacity-60" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <circle cx="9" cy="10" r="2" />
        <path d="m21 16-5-5-9 9" />
      </svg>
      <span className="text-xs uppercase tracking-widest">{label}</span>
    </div>
  );
}

export function Rating({ average, count }: { average: number | null; count: number }) {
  if (average === null || count === 0) {
    return <span className="text-sm text-muted">No reviews yet</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 text-sm">
      <span aria-hidden className="text-amber-500">★</span>
      <span className="font-medium">{average.toFixed(1)}</span>
      <span className="text-muted">({count})</span>
      <span className="sr-only">{`${average.toFixed(1)} out of 5 from ${count} reviews`}</span>
    </span>
  );
}

function discount(price: number | null, compareAt: number | null) {
  if (price === null || compareAt === null || compareAt <= price) return null;
  return Math.round((1 - price / compareAt) * 100);
}

export function ProductCard({ product }: { product: Product }) {
  const off = discount(product.price, product.compareAtPrice);
  const { prefix, amount } = formatPriceParts(product.price, product.maxPrice);

  return (
    <Link
      href={`/products/${product.slug}`}
      className="group flex w-full flex-col overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-line transition duration-300 hover:-translate-y-0.5 hover:shadow-xl"
    >
      <div className="relative overflow-hidden bg-line">
        {product.image ? (
          <Image
            src={product.image.url}
            alt={product.image.alt}
            width={680}
            height={680}
            unoptimized
            className={`aspect-square w-full object-cover transition duration-500 group-hover:scale-105 ${product.inStock ? "" : "opacity-70 saturate-50"}`}
          />
        ) : (
          <ImagePlaceholder />
        )}
        <div className="absolute left-3 top-3 flex flex-col items-start gap-1.5">
          {off !== null && product.inStock && (
            <span className="rounded-full bg-clay-600 px-2.5 py-1 text-xs font-semibold text-white shadow-sm">
              −{off}%
            </span>
          )}
          {!product.inStock && (
            <span className="rounded-full bg-white/90 px-2.5 py-1 text-xs font-medium text-ink shadow-sm backdrop-blur">
              Sold out
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-1.5 p-4">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted">{product.brand.name}</p>
        <h3 className="line-clamp-2 font-serif text-lg leading-snug">{product.name}</h3>
        <Rating average={product.ratingAverage} count={product.reviewCount} />

        <p className="mt-auto flex flex-wrap items-baseline gap-x-2 pt-3">
          {prefix && <span className="text-sm text-muted">{prefix}</span>}
          <span className={`text-lg font-semibold ${off !== null ? "text-clay-700" : ""}`}>{amount}</span>
          {off !== null && (
            <span className="text-sm text-muted line-through">{formatPrice(product.compareAtPrice)}</span>
          )}
        </p>
      </div>
    </Link>
  );
}

export function ProductGrid({ products }: { products: Product[] }) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4">
      {products.map((product) => (
        <li key={product.id} className="flex">
          <ProductCard product={product} />
        </li>
      ))}
    </ul>
  );
}
