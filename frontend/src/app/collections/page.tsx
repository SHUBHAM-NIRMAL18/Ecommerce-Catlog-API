import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { PrimaryLink, StateMessage } from "@/components/States";
import { api } from "@/lib/api";
import { collectionDates } from "@/lib/format";
import type { Collection, Image as ProductImage } from "@/lib/types";

export const metadata: Metadata = { title: "Collections · Home & Living" };

function Mosaic({ images }: { images: ProductImage[] }) {
  const cells = Array.from({ length: 4 }, (_, i) => images[i]);
  return (
    <div className="grid aspect-[4/3] grid-cols-2 grid-rows-2 gap-0.5 bg-line">
      {cells.map((image, i) =>
        image ? (
          <Image
            key={image.url}
            src={image.url}
            alt=""
            width={240}
            height={180}
            unoptimized
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
        ) : (
          <div key={i} className="bg-gradient-to-br from-clay-50 to-line" />
        ),
      )}
    </div>
  );
}

function CollectionCard({ collection, images }: { collection: Collection; images: ProductImage[] }) {
  const dates = collectionDates(collection.endsAt);
  return (
    <Link
      href={`/collections/${collection.slug}`}
      className="group flex h-full w-full flex-col overflow-hidden rounded-2xl bg-white ring-1 ring-line transition hover:-translate-y-0.5 hover:shadow-lg hover:ring-clay-600/40"
    >
      <div className="overflow-hidden">
        <Mosaic images={images} />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-5">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
          <span>
            {collection.productCount} {collection.productCount === 1 ? "product" : "products"}
          </span>
          {dates && <span className="rounded-full bg-clay-50 px-2 py-0.5 font-medium text-clay-700">{dates}</span>}
        </div>
        <h2 className="font-serif text-2xl group-hover:text-clay-700">{collection.name}</h2>
        {collection.description && <p className="text-sm leading-relaxed text-muted">{collection.description}</p>}
        <span className="mt-auto pt-3 text-sm font-medium text-clay-700">Explore →</span>
      </div>
    </Link>
  );
}

export default async function CollectionsPage() {
  const { items } = await api.collections();
  const previews = await Promise.allSettled(items.map((c) => api.collection(c.slug, 1, 4)));
  const imagesFor = (i: number) => {
    const preview = previews[i];
    if (preview.status !== "fulfilled") return [];
    return preview.value.items.flatMap((p) => (p.image ? [p.image] : []));
  };

  return (
    <div>
      <header className="mb-8 border-b border-line pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-clay-600">Curated edits</p>
        <h1 className="mt-2 font-serif text-4xl">Collections</h1>
        <p className="mt-2 max-w-xl text-muted">Hand-picked groups of products for every room and season.</p>
      </header>

      {items.length === 0 ? (
        <StateMessage icon="box" title="No collections right now" message="Check back soon for new edits.">
          <PrimaryLink href="/">Browse all products</PrimaryLink>
        </StateMessage>
      ) : (
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((collection, i) => (
            <li key={collection.id} className="flex">
              <CollectionCard collection={collection} images={imagesFor(i)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
