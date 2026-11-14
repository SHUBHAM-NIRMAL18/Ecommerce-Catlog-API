"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { createContext, useContext, useEffect, useState, useTransition, type FormEvent, type ReactNode } from "react";

import { formatPrice } from "@/lib/format";
import type { Brand, CategoryNode } from "@/lib/types";

const SORTS = [
  { value: "newest", label: "Newest" },
  { value: "popular", label: "Most popular" },
  { value: "rating", label: "Top rated" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
];

const RATINGS = [
  { value: "", label: "Any rating" },
  { value: "4", label: "4★ & up" },
  { value: "3", label: "3★ & up" },
  { value: "2", label: "2★ & up" },
];

type Changes = Record<string, string | null>;

type FiltersContextValue = {
  params: URLSearchParams;
  update: (changes: Changes) => void;
  hrefWith: (changes: Changes) => string;
  isPending: boolean;
};

const FiltersContext = createContext<FiltersContextValue | null>(null);

function withChanges(current: URLSearchParams, changes: Changes) {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(changes)) {
    if (value === null || value === "") next.delete(key);
    else next.set(key, value);
  }
  if (!("page" in changes)) next.delete("page");
  return next;
}

export function FiltersProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const params = new URLSearchParams(searchParams.toString());

  const hrefWith = (changes: Changes) => {
    const query = withChanges(params, changes).toString();
    return query ? `${pathname}?${query}` : pathname;
  };
  const update = (changes: Changes) => startTransition(() => router.push(hrefWith(changes), { scroll: false }));

  return <FiltersContext.Provider value={{ params, update, hrefWith, isPending }}>{children}</FiltersContext.Provider>;
}

function useFilters() {
  const context = useContext(FiltersContext);
  if (!context) throw new Error("useFilters must be used inside FiltersProvider");
  return context;
}

export function Results({ children }: { children: ReactNode }) {
  const { isPending } = useFilters();
  return (
    <div aria-busy={isPending} className={`transition-opacity duration-200 ${isPending ? "pointer-events-none opacity-50" : ""}`}>
      {children}
    </div>
  );
}

const normalize = (value: string) => value.trim().replace(/\s+/g, " ");

export function SearchBox() {
  const { params, update } = useFilters();
  const urlQ = params.get("q") ?? "";
  const [q, setQ] = useState(urlQ);
  const [seenUrlQ, setSeenUrlQ] = useState(urlQ);
  const [pushed, setPushed] = useState(urlQ);

  if (urlQ !== seenUrlQ) {
    setSeenUrlQ(urlQ);
    if (urlQ !== pushed) {
      setQ(urlQ);
      setPushed(urlQ);
    }
  }

  const search = (value: string) => {
    setPushed(value);
    update({ q: value || null });
  };

  useEffect(() => {
    const value = normalize(q);
    if (value === pushed) return;
    const timer = setTimeout(() => search(value), 350);
    return () => clearTimeout(timer);
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    const value = normalize(q);
    if (value !== pushed) search(value);
  };

  return (
    <form role="search" onSubmit={onSubmit} className="relative">
      <label htmlFor="search" className="sr-only">Search products</label>
      <svg viewBox="0 0 24 24" className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        id="search"
        type="search"
        value={q}
        onChange={(event) => setQ(event.target.value)}
        placeholder="Search rugs, lamps, oak, linen…"
        maxLength={100}
        autoComplete="off"
        className="w-full rounded-full border-0 bg-white py-3 pl-12 pr-11 text-base shadow-sm ring-1 ring-line placeholder:text-muted/70 focus:outline-none focus:ring-2 focus:ring-clay-600"
      />
      {q && (
        <button
          type="button"
          onClick={() => {
            setQ("");
            search("");
          }}
          aria-label="Clear search"
          className="absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full text-muted hover:bg-canvas hover:text-ink"
        >
          ×
        </button>
      )}
    </form>
  );
}

export function SortSelect() {
  const { params, update } = useFilters();
  return (
    <label className="flex items-center gap-2 text-sm text-muted">
      <span className="hidden sm:inline">Sort by</span>
      <select
        value={params.get("sort") ?? "newest"}
        onChange={(event) => update({ sort: event.target.value === "newest" ? null : event.target.value })}
        className="rounded-full border-0 bg-white py-2 pl-4 pr-9 text-sm font-medium text-ink shadow-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-clay-600"
      >
        {SORTS.map((sort) => (
          <option key={sort.value} value={sort.value}>{sort.label}</option>
        ))}
      </select>
    </label>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-b border-line py-5 first:pt-0 last:border-0">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-muted">{title}</h2>
      {children}
    </section>
  );
}

function CategoryLink({ node, active, child = false }: { node: CategoryNode; active: string | null; child?: boolean }) {
  const { hrefWith } = useFilters();
  const base = `flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 ${child ? "pl-5 text-sm" : "font-medium"}`;
  if (node.productCount === 0) {
    return (
      <span className={`${base} cursor-default text-muted/50`} title="No products yet">
        {node.name}
        <span className="text-xs">0</span>
      </span>
    );
  }
  const isActive = node.slug === active;
  return (
    <Link
      href={hrefWith({ category: node.slug })}
      scroll={false}
      aria-current={isActive ? "page" : undefined}
      className={`${base} transition ${isActive ? "bg-clay-50 text-clay-700" : "hover:bg-white"}`}
    >
      {node.name}
      <span className={`text-xs ${isActive ? "text-clay-600" : "text-muted"}`}>{node.productCount}</span>
    </Link>
  );
}

function CategoryNav({ categories }: { categories: CategoryNode[] }) {
  const { params, hrefWith } = useFilters();
  const active = params.get("category");
  const total = categories.reduce((sum, node) => sum + node.productCount, 0);

  return (
    <nav aria-label="Categories" className="flex flex-col gap-0.5">
      <Link
        href={hrefWith({ category: null })}
        scroll={false}
        className={`flex items-center justify-between rounded-lg px-2 py-1.5 font-medium transition ${active ? "hover:bg-white" : "bg-clay-50 text-clay-700"}`}
      >
        All products
        <span className="text-xs text-muted">{total}</span>
      </Link>
      {categories.map((main) => (
        <div key={main.slug} className="mt-1">
          <CategoryLink node={main} active={active} />
          {main.children.map((child) => (
            <CategoryLink key={child.slug} node={child} active={active} child />
          ))}
        </div>
      ))}
    </nav>
  );
}

function BrandFilter({ brands }: { brands: Brand[] }) {
  const { params, update } = useFilters();
  const selected = (params.get("brand") ?? "").split(",").filter(Boolean);

  const toggle = (slug: string) => {
    const next = selected.includes(slug) ? selected.filter((s) => s !== slug) : [...selected, slug];
    update({ brand: next.length ? next.join(",") : null });
  };

  return (
    <ul className="flex flex-col gap-1.5">
      {brands.map((brand) => {
        const empty = brand.productCount === 0 && !selected.includes(brand.slug);
        return (
          <li key={brand.slug}>
            <label
              title={empty ? "No products yet" : undefined}
              className={`flex items-center gap-3 text-sm ${empty ? "cursor-default text-muted/50" : "cursor-pointer"}`}
            >
              <input
                type="checkbox"
                checked={selected.includes(brand.slug)}
                disabled={empty}
                onChange={() => toggle(brand.slug)}
                className="h-4 w-4 rounded border-line accent-clay-600"
              />
              <span className="flex-1">{brand.name}</span>
              <span className={`text-xs ${empty ? "" : "text-muted"}`}>{brand.productCount}</span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}

function PriceFilter() {
  const { params, update } = useFilters();
  const min = params.get("minPrice") ?? "";
  const max = params.get("maxPrice") ?? "";
  const [error, setError] = useState("");

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const low = String(form.get("minPrice") ?? "").trim();
    const high = String(form.get("maxPrice") ?? "").trim();
    if (low && high && Number(low) > Number(high)) {
      setError("Min price must be lower than max price.");
      return;
    }
    setError("");
    update({ minPrice: low || null, maxPrice: high || null });
  };

  const input =
    "w-full min-w-0 rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-clay-600";

  return (
    <form key={`${min}|${max}`} onSubmit={onSubmit} className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <label className="sr-only" htmlFor="minPrice">Minimum price in euro</label>
        <input id="minPrice" name="minPrice" type="number" min="0" step="0.01" inputMode="decimal" placeholder="Min €" defaultValue={min} className={input} />
        <span className="text-muted">–</span>
        <label className="sr-only" htmlFor="maxPrice">Maximum price in euro</label>
        <input id="maxPrice" name="maxPrice" type="number" min="0" step="0.01" inputMode="decimal" placeholder="Max €" defaultValue={max} className={input} />
      </div>
      {error && <p className="text-xs text-clay-700">{error}</p>}
      <button type="submit" className="self-start rounded-full bg-ink px-4 py-1.5 text-sm font-medium text-white transition hover:bg-clay-700">
        Apply
      </button>
    </form>
  );
}

function AvailabilityFilter() {
  const { params, update } = useFilters();
  return (
    <div className="flex flex-col gap-3">
      <label className="flex cursor-pointer items-center gap-3 text-sm">
        <input
          type="checkbox"
          checked={params.get("inStock") === "true"}
          onChange={(event) => update({ inStock: event.target.checked ? "true" : null })}
          className="h-4 w-4 rounded border-line accent-clay-600"
        />
        In stock only
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="sr-only">Minimum rating</span>
        <select
          value={params.get("minRating") ?? ""}
          onChange={(event) => update({ minRating: event.target.value || null })}
          className="rounded-lg border-0 bg-white py-2 pl-3 pr-8 text-sm shadow-sm ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-clay-600"
        >
          {RATINGS.map((rating) => (
            <option key={rating.value} value={rating.value}>{rating.label}</option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function FilterPanel({ categories, brands }: { categories: CategoryNode[]; brands: Brand[] }) {
  const [open, setOpen] = useState(false);

  return (
    <aside>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="filter-panel"
        className="mb-4 flex w-full items-center justify-between rounded-full bg-white px-5 py-3 text-sm font-medium shadow-sm ring-1 ring-line lg:hidden"
      >
        Filters &amp; categories
        <svg viewBox="0 0 24 24" aria-hidden className={`h-5 w-5 text-muted transition ${open ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      <div id="filter-panel" className={`${open ? "block" : "hidden"} rounded-2xl bg-canvas lg:block`}>
        <Section title="Categories">
          <CategoryNav categories={categories} />
        </Section>
        <Section title="Brand">
          <BrandFilter brands={brands} />
        </Section>
        <Section title="Price">
          <PriceFilter />
        </Section>
        <Section title="Availability & rating">
          <AvailabilityFilter />
        </Section>
      </div>
    </aside>
  );
}

function findCategory(categories: CategoryNode[], slug: string): CategoryNode | undefined {
  for (const node of categories) {
    if (node.slug === slug) return node;
    const child = findCategory(node.children, slug);
    if (child) return child;
  }
}

export function ActiveFilters({ categories, brands }: { categories: CategoryNode[]; brands: Brand[] }) {
  const { params, hrefWith } = useFilters();
  const chips: { label: string; changes: Changes }[] = [];

  const q = params.get("q");
  if (q) chips.push({ label: `“${q}”`, changes: { q: null } });
  const category = params.get("category");
  if (category) chips.push({ label: findCategory(categories, category)?.name ?? category, changes: { category: null } });
  const selectedBrands = (params.get("brand") ?? "").split(",").filter(Boolean);
  for (const slug of selectedBrands) {
    const rest = selectedBrands.filter((s) => s !== slug);
    chips.push({ label: brands.find((b) => b.slug === slug)?.name ?? slug, changes: { brand: rest.length ? rest.join(",") : null } });
  }
  const min = params.get("minPrice");
  const max = params.get("maxPrice");
  if (min || max) {
    const label = min && max ? `${formatPrice(Number(min))} – ${formatPrice(Number(max))}` : min ? `From ${formatPrice(Number(min))}` : `Up to ${formatPrice(Number(max))}`;
    chips.push({ label, changes: { minPrice: null, maxPrice: null } });
  }
  if (params.get("inStock") === "true") chips.push({ label: "In stock", changes: { inStock: null } });
  const minRating = params.get("minRating");
  if (minRating) chips.push({ label: `${minRating}★ & up`, changes: { minRating: null } });

  if (chips.length === 0) return null;

  const sort = params.get("sort");
  return (
    <div className="mb-5 flex flex-wrap items-center gap-2">
      {chips.map((chip) => (
        <Link
          key={chip.label}
          href={hrefWith(chip.changes)}
          scroll={false}
          className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-sm shadow-sm ring-1 ring-line transition hover:ring-clay-600"
        >
          {chip.label}
          <span aria-hidden className="text-muted">×</span>
          <span className="sr-only">Remove filter</span>
        </Link>
      ))}
      <Link href={sort ? `/?sort=${sort}` : "/"} scroll={false} className="text-sm font-medium text-clay-700 underline-offset-4 hover:underline">
        Clear all
      </Link>
    </div>
  );
}
