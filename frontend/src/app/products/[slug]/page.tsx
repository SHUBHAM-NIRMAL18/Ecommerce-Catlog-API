import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { Gallery } from "@/components/Gallery";
import { Rating } from "@/components/ProductCard";
import { VariantPicker } from "@/components/VariantPicker";
import { api, isNotFound } from "@/lib/api";
import { attributeRows } from "@/lib/format";

const getProduct = cache(async (slug: string) => {
  try {
    return await api.product(slug);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
});

export async function generateMetadata({ params }: PageProps<"/products/[slug]">): Promise<Metadata> {
  const product = await getProduct((await params).slug);
  return { title: `${product.name} · Home & Living`, description: product.description };
}

export default async function ProductPage({ params }: PageProps<"/products/[slug]">) {
  const product = await getProduct((await params).slug);
  const attributes = attributeRows(product.attributes);

  return (
    <article>
      <nav aria-label="Breadcrumb" className="mb-6 text-sm text-muted">
        <ol className="flex flex-wrap items-center gap-2">
          <li>
            <Link href="/" className="hover:text-ink">Shop</Link>
          </li>
          {product.categoryPath.map((category) => (
            <li key={category.slug} className="flex items-center gap-2">
              <span aria-hidden>›</span>
              <Link href={`/?category=${category.slug}`} className="hover:text-ink">{category.name}</Link>
            </li>
          ))}
        </ol>
      </nav>

      <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
        <Gallery key={product.id} images={product.images} name={product.name} />

        <div className="flex flex-col gap-6 lg:sticky lg:top-24 lg:self-start">
          <header className="flex flex-col gap-2">
            <Link
              href={`/?brand=${product.brand.slug}`}
              className="text-xs font-medium uppercase tracking-[0.16em] text-clay-600 hover:text-clay-800"
            >
              {product.brand.name}
            </Link>
            <h1 className="font-serif text-3xl leading-tight sm:text-4xl">{product.name}</h1>
            <a href="#reviews" className="self-start hover:underline">
              <Rating average={product.ratingAverage} count={product.reviewCount} />
            </a>
          </header>

          <VariantPicker key={product.id} variants={product.variants} />

          {product.description && <p className="leading-relaxed text-muted">{product.description}</p>}

          {product.features.length > 0 && (
            <section>
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-muted">Highlights</h2>
              <ul className="flex flex-col gap-2">
                {product.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <svg viewBox="0 0 24 24" className="mt-0.5 h-5 w-5 shrink-0 text-clay-600" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                      <path d="m5 12 5 5L20 7" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {attributes.length > 0 && (
            <section>
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-muted">Details</h2>
              <dl className="divide-y divide-line overflow-hidden rounded-2xl bg-white ring-1 ring-line">
                {attributes.map((row) => (
                  <div key={row.key} className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-4 px-4 py-3 text-sm">
                    <dt className="text-muted">{row.label}</dt>
                    <dd>{row.value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </div>
      </div>
    </article>
  );
}
