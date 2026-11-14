import { ActiveFilters, FilterPanel, FiltersProvider, Results, SearchBox, SortSelect } from "@/components/Filters";
import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductCard";
import { api, firstValue, productParams } from "@/lib/api";
import type { CategoryNode } from "@/lib/types";

function categoryName(categories: CategoryNode[], slug: string | undefined): string | undefined {
  if (!slug) return undefined;
  for (const node of categories) {
    if (node.slug === slug) return node.name;
    const child = node.children.find((c) => c.slug === slug);
    if (child) return child.name;
  }
}

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const [products, categories, brands] = await Promise.all([
    api.products(productParams(params)),
    api.categories(),
    api.brands(),
  ]);

  const q = firstValue(params.q)?.trim();
  const title = categoryName(categories.items, firstValue(params.category)) ?? "All products";

  return (
    <FiltersProvider>
      <header className="mb-8 border-b border-line pb-6">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-clay-600">The shop</p>
        <h1 className="mt-1 font-serif text-3xl sm:text-4xl">{title}</h1>
        <p className="mt-2 max-w-xl text-muted">
          Rugs, lamps, furniture and small things that make a home feel calm.
        </p>
        <div className="mt-6 max-w-2xl">
          <SearchBox />
        </div>
      </header>

      <div className="grid gap-8 lg:grid-cols-[250px_1fr]">
        <FilterPanel categories={categories.items} brands={brands.items} />

        <section aria-label="Products" className="min-w-0">
          <div className="mb-4 flex items-center justify-between gap-3">
            <p className="text-sm text-muted">
              {q ? (
                <>
                  {products.total} {products.total === 1 ? "result" : "results"} for <span className="font-medium text-ink">“{q}”</span>
                </>
              ) : (
                <>
                  {products.total} {products.total === 1 ? "product" : "products"}
                </>
              )}
            </p>
            <SortSelect />
          </div>
          <ActiveFilters categories={categories.items} brands={brands.items} />
          <Results>
            <ProductGrid products={products.items} />
            <Pagination
              page={products.page}
              totalPages={products.totalPages}
              total={products.total}
              limit={products.limit}
              searchParams={params}
            />
          </Results>
        </section>
      </div>
    </FiltersProvider>
  );
}
