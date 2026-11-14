"use client";

import Image from "next/image";
import { useState } from "react";

import { ImagePlaceholder } from "@/components/ProductCard";
import type { Image as ProductImage } from "@/lib/types";

export function Gallery({ images, name }: { images: ProductImage[]; name: string }) {
  const [index, setIndex] = useState(0);
  const current = images[index];

  if (!current) {
    return (
      <div className="self-start overflow-hidden rounded-2xl ring-1 ring-line">
        <ImagePlaceholder label="No photo yet" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 self-start">
      <div className="overflow-hidden rounded-2xl bg-line ring-1 ring-line">
        <Image
          src={current.url}
          alt={current.alt || name}
          width={680}
          height={680}
          unoptimized
          priority
          className="aspect-square w-full object-cover"
        />
      </div>
      {images.length > 1 && (
        <ul className="flex gap-3">
          {images.map((image, i) => (
            <li key={image.url}>
              <button
                type="button"
                onClick={() => setIndex(i)}
                aria-label={`Show photo ${i + 1} of ${images.length}`}
                aria-current={i === index}
                className={`block overflow-hidden rounded-xl ring-2 transition ${i === index ? "ring-clay-600" : "ring-transparent opacity-70 hover:opacity-100"}`}
              >
                <Image src={image.url} alt="" width={96} height={96} unoptimized className="h-20 w-20 object-cover sm:h-24 sm:w-24" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
