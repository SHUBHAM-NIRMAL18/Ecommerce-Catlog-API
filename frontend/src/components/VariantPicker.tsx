"use client";

import { useState } from "react";

import { formatPrice, stockLabel } from "@/lib/format";
import type { Variant } from "@/lib/types";
import { colorOptions, findVariant, initialVariant, sizeOptions, variantForColor, type Option } from "@/lib/variants";

function OptionGroup({
  label,
  selected,
  options,
  onSelect,
}: {
  label: string;
  selected: string;
  options: Option[];
  onSelect: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm">
        <span className="text-muted">{label}:</span> <span className="font-medium">{selected}</span>
      </legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = option.value === selected;
          const state = !option.exists ? "Not available in this combination" : option.soldOut ? "Sold out" : undefined;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onSelect(option.value)}
              disabled={!option.exists}
              aria-pressed={isSelected}
              title={state}
              className={[
                "relative rounded-full px-4 py-2 text-sm ring-1 transition",
                isSelected ? "bg-ink text-white ring-ink" : "bg-white ring-line hover:ring-clay-600",
                option.soldOut && !isSelected ? "text-muted line-through decoration-muted/60" : "",
                option.soldOut && isSelected ? "line-through decoration-white/60" : "",
                !option.exists ? "cursor-not-allowed border-dashed bg-transparent text-muted/40 ring-line/60 hover:ring-line/60" : "",
              ].join(" ")}
            >
              {option.value}
              {state && <span className="sr-only"> ({state})</span>}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

function StockBadge({ stock }: { stock: number }) {
  const label = stockLabel(stock);
  const tone = stock <= 0 ? "bg-stone-200 text-stone-700" : stock <= 2 ? "bg-amber-100 text-amber-800" : "bg-emerald-50 text-emerald-800";
  const dot = stock <= 0 ? "bg-stone-500" : stock <= 2 ? "bg-amber-500" : "bg-emerald-600";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${tone}`}>
      <span aria-hidden className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

export function VariantPicker({ variants }: { variants: Variant[] }) {
  const [variant, setVariant] = useState<Variant | undefined>(() => initialVariant(variants));

  if (!variant) {
    return <p className="text-muted">This product is not available to order right now.</p>;
  }

  const colors = colorOptions(variants);
  const sizes = sizeOptions(variants, variant.color);
  const onSale = variant.compareAtPrice !== null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-baseline gap-3" aria-live="polite">
        <span className={`text-3xl font-semibold ${onSale ? "text-clay-700" : ""}`}>{formatPrice(variant.price)}</span>
        {onSale && (
          <>
            <span className="text-lg text-muted line-through">{formatPrice(variant.compareAtPrice)}</span>
            <span className="rounded-full bg-clay-600 px-2.5 py-0.5 text-xs font-semibold text-white">
              Save {formatPrice((variant.compareAtPrice ?? 0) - variant.price)}
            </span>
          </>
        )}
      </div>

      <OptionGroup
        label="Colour"
        selected={variant.color}
        options={colors}
        onSelect={(color) => setVariant(variantForColor(variants, color, variant.size))}
      />
      <OptionGroup
        label="Size"
        selected={variant.size}
        options={sizes}
        onSelect={(size) => setVariant(findVariant(variants, variant.color, size) ?? variant)}
      />

      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-5" aria-live="polite">
        <StockBadge stock={variant.stock} />
        <span className="text-sm text-muted">
          SKU <span className="font-mono text-ink">{variant.sku}</span>
        </span>
      </div>
    </div>
  );
}
