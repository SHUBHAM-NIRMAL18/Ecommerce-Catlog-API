import { ActiveFilters, FilterPanel, FiltersProvider, Results, SearchBox, SortSelect } from "@/components/Filters";
import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductCard";
import { PrimaryLink, SecondaryLink, StateMessage } from "@/components/States";
import { ApiError, api, firstValue, productParams } from "@/lib/api";
import type { CategoryNode, Page, ProductCard, SearchParams } from "@/lib/types";

function categoryName(categories: CategoryNode[], slug: string | undefined): string | undefined {
  if (!slug) return undefined;
  for (const node of categories) {
    if (node.slug === slug) return node.name;
    const child = node.children.find((c) => c.slug === slug);
    if (child) return child.name;
  }
}

function hrefWithout(searchParams: SearchParams, keys: string[]) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    const first = firstValue(value);
    if (first && !keys.includes(key)) params.set(key, first);
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

type ProductsResult = { data: Page<ProductCard> } | { error: ApiError };

async function loadProducts(searchParams: SearchParams): Promise<ProductsResult> {
  try {
    return { data: await api.products(productParams(searchParams)) };
  } catch (error) {
    if (error instanceof ApiError && error.status === 400) return { error };
    throw error;
  }
}

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const [result, categories, brands] = await Promise.all([loadProducts(params), api.categories(), api.brands()]);

  const q = firstValue(params.q)?.trim();
  const sort = firstValue(params.sort);
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
          {"error" in result ? (
            <StateMessage
              icon="alert"
              title="Some filters aren't valid"
              message={
                <>
                  <p>This link contains values the shop can&apos;t use:</p>
                  <ul className="mt-3 space-y-1 text-sm">
                    {(result.error.details.length ? result.error.details : [{ field: null, value: null, message: result.error.message }]).map((detail, i) => (
                      <li key={i}>
                        {detail.field && <span className="font-medium text-ink">{detail.field}: </span>}
                        {detail.message}
                      </li>
                    ))}
                  </ul>
                </>
              }
            >
              <PrimaryLink href={hrefWithout(params, result.error.details.map((d) => d.field ?? "").concat("page"))}>
                Remove invalid filters
              </PrimaryLink>
              <SecondaryLink href="/">Reset all filters</SecondaryLink>
            </StateMessage>
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between gap-3">
                <p className="text-sm text-muted">
                  {q ? (
                    <>
                      {result.data.total} {result.data.total === 1 ? "result" : "results"} for{" "}
                      <span className="font-medium text-ink">“{q}”</span>
                    </>
                  ) : (
                    <>
                      {result.data.total} {result.data.total === 1 ? "product" : "products"}
                    </>
                  )}
                </p>
                <SortSelect />
              </div>
              <ActiveFilters categories={categories.items} brands={brands.items} />
              <Results>
                {result.data.total === 0 ? (
                  <StateMessage
                    icon="search"
                    title="No products match"
                    message={
                      q
                        ? `Nothing matches “${q}” with these filters. Try fewer words, a different spelling or fewer filters.`
                        : "Nothing matches these filters. Try removing one or two."
                    }
                  >
                    <PrimaryLink href={sort ? `/?sort=${encodeURIComponent(sort)}` : "/"}>Clear filters</PrimaryLink>
                  </StateMessage>
                ) : result.data.items.length === 0 ? (
                  <StateMessage
                    icon="box"
                    title="This page is empty"
                    message={`There are only ${result.data.totalPages} ${result.data.totalPages === 1 ? "page" : "pages"} of results.`}
                  >
                    <PrimaryLink href={hrefWithout(params, ["page"])}>Go to the first page</PrimaryLink>
                  </StateMessage>
                ) : (
                  <ProductGrid products={result.data.items} />
                )}
                <Pagination
                  page={result.data.page}
                  totalPages={result.data.totalPages}
                  total={result.data.total}
                  limit={result.data.limit}
                  searchParams={params}
                />
              </Results>
            </>
          )}
        </section>
      </div>
    </FiltersProvider>
  );
}
