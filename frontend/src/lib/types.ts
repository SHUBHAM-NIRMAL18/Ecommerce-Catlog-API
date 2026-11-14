export type Ref = {
  slug: string;
  name: string;
};

export type Image = {
  url: string;
  alt: string;
};

export type ProductCard = {
  id: string;
  slug: string;
  name: string;
  brand: Ref;
  category: Ref;
  price: number | null;
  maxPrice: number | null;
  compareAtPrice: number | null;
  inStock: boolean;
  ratingAverage: number | null;
  reviewCount: number;
  image: Image | null;
};

export type Variant = {
  sku: string;
  color: string;
  size: string;
  price: number;
  compareAtPrice: number | null;
  stock: number;
};

export type AttributeValue = string | number | boolean;

export type ProductDetail = Omit<ProductCard, "category" | "image"> & {
  description: string;
  categoryPath: Ref[];
  attributes: Record<string, AttributeValue | null | undefined>;
  features: string[];
  tags: string[];
  images: Image[];
  variants: Variant[];
};

export type Review = {
  id: string;
  rating: number;
  title: string;
  body: string | null;
  verifiedPurchase: boolean;
  helpfulCount: number;
  createdAt: string;
};

export type Page<T> = {
  items: T[];
  page: number;
  limit: number;
  total: number;
  totalPages: number;
};

export type ProductPage = Page<ProductCard> & {
  correctedQuery: string | null;
};

export type Suggestions = {
  products: ProductCard[];
  categories: Ref[];
  brands: Ref[];
  correctedQuery: string | null;
};

export type CategoryNode = Ref & {
  productCount: number;
  children: CategoryNode[];
};

export type Brand = Ref & {
  country: string;
  productCount: number;
};

export type Collection = {
  id: string;
  slug: string;
  name: string;
  description: string;
  startsAt: string | null;
  endsAt: string | null;
  productCount: number;
};

export type CollectionPage = Page<ProductCard> & {
  collection: Collection;
};

export type ApiErrorDetail = {
  field: string | null;
  value: string | null;
  message: string;
};

export type SearchParams = Record<string, string | string[] | undefined>;
