import type {
  ApiErrorDetail,
  Brand,
  CategoryNode,
  Collection,
  CollectionPage,
  Page,
  ProductCard,
  ProductDetail,
  ProductPage,
  Review,
  SearchParams,
  Suggestions,
} from "./types";

const SERVER_API_URL = process.env.API_URL ?? "http://localhost:8000";
const BROWSER_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const PRODUCT_PARAMS = [
  "q",
  "category",
  "brand",
  "minPrice",
  "maxPrice",
  "inStock",
  "minRating",
  "sort",
  "page",
  "limit",
] as const;

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: ApiErrorDetail[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function baseUrl() {
  return typeof window === "undefined" ? SERVER_API_URL : BROWSER_API_URL;
}

type Params = Record<string, string | number | undefined>;

async function request<T>(path: string, params: Params = {}, signal?: AbortSignal): Promise<T> {
  const url = new URL(path, baseUrl());
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", signal });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(0, "NETWORK_ERROR", "The catalog is not reachable right now. Please try again.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      body?.error?.code ?? "ERROR",
      body?.error?.message ?? `Request failed (${response.status})`,
      body?.error?.details ?? [],
    );
  }
  return response.json() as Promise<T>;
}

export function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export function productParams(searchParams: SearchParams): Params {
  return Object.fromEntries(PRODUCT_PARAMS.map((key) => [key, firstValue(searchParams[key])]));
}

const slugPath = (slug: string) => encodeURIComponent(slug);

export const api = {
  products: (params: Params) => request<ProductPage>("/api/products", params),
  suggest: (q: string, signal?: AbortSignal) => request<Suggestions>("/api/search/suggest", { q }, signal),
  product: (slug: string) => request<ProductDetail>(`/api/products/${slugPath(slug)}`),
  reviews: (slug: string, page = 1, sort = "newest", limit = 5) =>
    request<Page<Review>>(`/api/products/${slugPath(slug)}/reviews`, { page, sort, limit }),
  similar: (slug: string) => request<{ items: ProductCard[] }>(`/api/products/${slugPath(slug)}/similar`),
  categories: () => request<{ items: CategoryNode[] }>("/api/categories"),
  brands: () => request<{ items: Brand[] }>("/api/brands"),
  collections: () => request<{ items: Collection[] }>("/api/collections"),
  collection: (slug: string, page = 1, limit = 12) =>
    request<CollectionPage>(`/api/collections/${slugPath(slug)}`, { page, limit }),
};

export function isNotFound(error: unknown) {
  return error instanceof ApiError && error.status === 404;
}
