import type { Variant } from "./types";

const unique = (values: string[]) => [...new Set(values)];

export function colorsOf(variants: Variant[]) {
  return unique(variants.map((v) => v.color));
}

export function sizesOf(variants: Variant[]) {
  return unique(variants.map((v) => v.size));
}

export function findVariant(variants: Variant[], color: string, size: string) {
  return variants.find((v) => v.color === color && v.size === size);
}

export function initialVariant(variants: Variant[]) {
  return variants.find((v) => v.stock > 0) ?? variants[0];
}

export function variantForColor(variants: Variant[], color: string, currentSize: string) {
  const options = variants.filter((v) => v.color === color);
  return (
    options.find((v) => v.size === currentSize && v.stock > 0) ??
    options.find((v) => v.size === currentSize) ??
    options.find((v) => v.stock > 0) ??
    options[0]
  );
}

export type Option = { value: string; exists: boolean; soldOut: boolean };

export function colorOptions(variants: Variant[]): Option[] {
  return colorsOf(variants).map((color) => {
    const options = variants.filter((v) => v.color === color);
    return { value: color, exists: true, soldOut: options.every((v) => v.stock <= 0) };
  });
}

export function sizeOptions(variants: Variant[], color: string): Option[] {
  return sizesOf(variants).map((size) => {
    const variant = findVariant(variants, color, size);
    return { value: size, exists: variant !== undefined, soldOut: variant !== undefined && variant.stock <= 0 };
  });
}
