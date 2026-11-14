import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductCard";
import { PrimaryLink, SecondaryLink, StateMessage } from "@/components/States";
import { api, firstValue, isNotFound } from "@/lib/api";
import { collectionDates } from "@/lib/format";

const LIMIT = 12;

function pageFrom(value: string | string[] | undefined) {
  const page = Number(firstValue(value));
  return Number.isInteger(page) && page >= 1 && page <= 10000 ? page : 1;
}

const getCollection = cache(async (slug: string, page: number) => {
  try {
    return await api.collection(slug, page, LIMIT);
  } catch (error) {
    if (isNotFound(error)) notFound();
    throw error;
  }
});

export async function generateMetadata({ params }: PageProps<"/collections/[slug]">): Promise<Metadata> {
  const { collection } = await getCollection((await params).slug, 1);
  return { title: `${collection.name} · Home & Living`, description: collection.description };
}

export default async function CollectionPage({ params, searchParams }: PageProps<"/collections/[slug]">) {
  const { slug } = await params;
  const query = await searchParams;
  const page = pageFrom(query.page);
  const data = await getCollection(slug, page);
  const { collection } = data;
  const dates = collectionDates(collection.endsAt);

  return (
    <div>
      <nav aria-label="Breadcrumb" className="mb-6 text-sm text-muted">
        <ol className="flex flex-wrap items-center gap-2">
          <li>
            <Link href="/collections" className="hover:text-ink">Collections</Link>
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden>›</span>
            <span aria-current="page" className="text-ink">{collection.name}</span>
          </li>
        </ol>
      </nav>

      <header className="mb-8 border-b border-line pb-6">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
          <span className="font-medium uppercase tracking-[0.16em] text-clay-600">Collection</span>
          {dates && <span className="rounded-full bg-clay-50 px-2 py-0.5 font-medium text-clay-700">{dates}</span>}
        </div>
        <h1 className="mt-2 font-serif text-4xl">{collection.name}</h1>
        {collection.description && <p className="mt-2 max-w-xl text-muted">{collection.description}</p>}
      </header>

      {data.items.length > 0 ? (
        <ProductGrid products={data.items} />
      ) : data.total === 0 ? (
        <StateMessage icon="box" title="Nothing here yet" message="This collection has no products available right now.">
          <PrimaryLink href="/">Browse all products</PrimaryLink>
          <SecondaryLink href="/collections">See other collections</SecondaryLink>
        </StateMessage>
      ) : (
        <StateMessage
          icon="search"
          title="This page is empty"
          message={`This collection has ${data.totalPages} ${data.totalPages === 1 ? "page" : "pages"} of products.`}
        >
          <PrimaryLink href={`/collections/${collection.slug}`}>Go to first page</PrimaryLink>
        </StateMessage>
      )}

      <Pagination
        page={page}
        totalPages={data.totalPages}
        total={data.total}
        limit={LIMIT}
        searchParams={query}
        basePath={`/collections/${collection.slug}`}
      />
    </div>
  );
}
