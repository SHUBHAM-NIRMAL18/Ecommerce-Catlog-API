"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { ProductCard, Suggestions } from "@/lib/types";

export const MIN_SUGGEST_LENGTH = 2;

export type Option = {
  id: string;
  href: string;
  group: "Categories" | "Brands" | "Products";
  label: string;
  product?: ProductCard;
};

export function toOptions(data: Suggestions): Option[] {
  return [
    ...data.categories.map((c) => ({ id: `c-${c.slug}`, href: `/?category=${c.slug}`, group: "Categories" as const, label: c.name })),
    ...data.brands.map((b) => ({ id: `b-${b.slug}`, href: `/?brand=${b.slug}`, group: "Brands" as const, label: b.name })),
    ...data.products.map((p) => ({ id: `p-${p.slug}`, href: `/products/${p.slug}`, group: "Products" as const, label: p.name, product: p })),
  ];
}

export function useSuggestions(query: string) {
  const [result, setResult] = useState<{ query: string; data: Suggestions } | null>(null);

  useEffect(() => {
    if (query.length < MIN_SUGGEST_LENGTH) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api
        .suggest(query, controller.signal)
        .then((data) => setResult({ query, data }))
        .catch(() => {});
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return result && result.query === query ? result.data : null;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function Highlight({ text, words }: { text: string; words: string[] }) {
  const usable = words.filter(Boolean);
  if (usable.length === 0) return <>{text}</>;
  const pattern = new RegExp(`(${usable.map(escapeRegExp).join("|")})`, "gi");
  const parts: ReactNode[] = text.split(pattern).map((part, i) =>
    i % 2 === 1 ? (
      <mark key={i} className="bg-transparent font-semibold text-ink">
        {part}
      </mark>
    ) : (
      part
    ),
  );
  return <>{parts}</>;
}

export function SuggestionList({
  id,
  query,
  data,
  options,
  active,
  onPick,
  onSearchAll,
}: {
  id: string;
  query: string;
  data: Suggestions;
  options: Option[];
  active: number;
  onPick: () => void;
  onSearchAll: () => void;
}) {
  const words = (data.correctedQuery ?? query).toLowerCase().split(" ");
  const groups = (["Categories", "Brands", "Products"] as const).filter((g) => options.some((o) => o.group === g));

  return (
    <div
      className="absolute inset-x-0 top-full z-30 mt-2 overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-line"
      onMouseDown={(event) => event.preventDefault()}
    >
      {data.correctedQuery && (
        <p className="border-b border-line px-4 py-2.5 text-sm text-muted">
          Showing suggestions for <span className="font-medium text-ink">“{data.correctedQuery}”</span>
        </p>
      )}
      {options.length === 0 ? (
        <p className="px-4 py-4 text-sm text-muted">No suggestions for “{query}”.</p>
      ) : (
        <ul id={id} role="listbox" aria-label="Search suggestions" className="max-h-[min(70vh,28rem)] overflow-y-auto py-2">
          {groups.map((group) => (
            <li key={group} role="presentation">
              <p className="px-4 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{group}</p>
              <ul role="presentation">
                {options.map((option, index) =>
                  option.group !== group ? null : (
                    <li key={option.id} id={`${id}-${option.id}`} role="option" aria-selected={index === active}>
                      <Link
                        href={option.href}
                        onClick={onPick}
                        tabIndex={-1}
                        className={`flex items-center gap-3 px-4 py-2 text-sm ${index === active ? "bg-clay-50" : "hover:bg-canvas"}`}
                      >
                        {option.product ? (
                          <>
                            {option.product.image ? (
                              <Image
                                src={option.product.image.url}
                                alt=""
                                width={40}
                                height={40}
                                unoptimized
                                className="h-10 w-10 shrink-0 rounded-lg object-cover"
                              />
                            ) : (
                              <span className="h-10 w-10 shrink-0 rounded-lg bg-gradient-to-br from-clay-50 to-line" />
                            )}
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-muted">
                                <Highlight text={option.label} words={words} />
                              </span>
                              <span className="block truncate text-xs text-muted/80">{option.product.brand.name}</span>
                            </span>
                            <span className="shrink-0 text-sm font-medium">
                              {option.product.price === null ? "" : formatPrice(option.product.price)}
                            </span>
                          </>
                        ) : (
                          <span className="text-muted">
                            <Highlight text={option.label} words={words} />
                          </span>
                        )}
                      </Link>
                    </li>
                  ),
                )}
              </ul>
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        onClick={onSearchAll}
        className="flex w-full items-center gap-2 border-t border-line px-4 py-3 text-left text-sm font-medium text-clay-700 hover:bg-canvas"
      >
        See all results for “{query}” →
      </button>
    </div>
  );
}
