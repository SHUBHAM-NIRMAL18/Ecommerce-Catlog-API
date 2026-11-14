import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductCard";
import { api, productParams } from "@/lib/api";

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const products = await api.products(productParams(params));

  return (
    <section>
      <header className="mb-8 flex flex-col gap-2 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-clay-600">The shop</p>
          <h1 className="mt-1 font-serif text-3xl sm:text-4xl">All products</h1>
          <p className="mt-2 max-w-xl text-muted">
            Rugs, lamps, furniture and small things that make a home feel calm.
          </p>
        </div>
        <p className="text-sm text-muted">
          {products.total} {products.total === 1 ? "product" : "products"}
        </p>
      </header>
      <ProductGrid products={products.items} />
      <Pagination
        page={products.page}
        totalPages={products.totalPages}
        total={products.total}
        limit={products.limit}
        searchParams={params}
      />
    </section>
  );
}
