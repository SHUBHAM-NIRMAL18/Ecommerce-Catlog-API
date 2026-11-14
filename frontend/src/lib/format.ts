import type { AttributeValue } from "./types";

const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });

export function formatPrice(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? euro.format(value) : "Price unavailable";
}

export function formatPriceParts(price: number | null, maxPrice: number | null) {
  const varies = price !== null && maxPrice !== null && maxPrice > price;
  return { prefix: varies ? "from" : "", amount: formatPrice(price) };
}

export function priceLabel(price: number | null, maxPrice: number | null) {
  const { prefix, amount } = formatPriceParts(price, maxPrice);
  return prefix ? `${prefix} ${amount}` : amount;
}

export function stockLabel(stock: number) {
  if (stock <= 0) return "Sold out";
  if (stock <= 2) return `Only ${stock} left`;
  return "In stock";
}

export function ratingLabel(average: number | null, count: number) {
  if (average === null || count === 0) return "No reviews yet";
  return `${average.toFixed(1)} (${count} ${count === 1 ? "review" : "reviews"})`;
}

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

export function formatDate(iso: string) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : dateFormat.format(date);
}

type AttributeSpec = { label: string; unit?: string };

const ATTRIBUTES: Record<string, AttributeSpec> = {
  material: { label: "Material" },
  origin: { label: "Origin" },
  care: { label: "Care" },
  construction: { label: "Construction" },
  pileHeightMm: { label: "Pile height", unit: "mm" },
  washable: { label: "Washable" },
  washTempC: { label: "Wash temperature", unit: "°C" },
  fillMaterial: { label: "Fill material" },
  assemblyRequired: { label: "Assembly required" },
  warrantyYears: { label: "Warranty", unit: "years" },
  maxLoadKg: { label: "Max load", unit: "kg" },
  bulbType: { label: "Bulb type" },
  maxWatt: { label: "Max wattage", unit: "W" },
  bulbIncluded: { label: "Bulb included" },
  dimmable: { label: "Dimmable" },
  cableLengthCm: { label: "Cable length", unit: "cm" },
  waterproof: { label: "Waterproof" },
  readyToHang: { label: "Ready to hang" },
  burnTimeHours: { label: "Burn time", unit: "hours" },
  scented: { label: "Scented" },
  dishwasherSafe: { label: "Dishwasher safe" },
  microwaveSafe: { label: "Microwave safe" },
  weightKg: { label: "Weight", unit: "kg" },
};

const ATTRIBUTE_ORDER = Object.keys(ATTRIBUTES);

function humanize(key: string) {
  const words = key.replace(/([a-z0-9])([A-Z])/g, "$1 $2").toLowerCase();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function formatValue(value: AttributeValue, unit?: string) {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return unit ? `${value} ${unit}` : String(value);
  const text = value.trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export type AttributeRow = { key: string; label: string; value: string };

export function attributeRows(attributes: Record<string, AttributeValue | null | undefined>): AttributeRow[] {
  return Object.entries(attributes)
    .filter((entry): entry is [string, AttributeValue] => {
      const value = entry[1];
      if (value === null || value === undefined) return false;
      if (typeof value === "number") return Number.isFinite(value);
      return typeof value === "boolean" || value.trim() !== "";
    })
    .sort(([a], [b]) => {
      const ia = ATTRIBUTE_ORDER.indexOf(a);
      const ib = ATTRIBUTE_ORDER.indexOf(b);
      return (ia === -1 ? Infinity : ia) - (ib === -1 ? Infinity : ib) || a.localeCompare(b);
    })
    .map(([key, value]) => {
      const spec = ATTRIBUTES[key];
      return { key, label: spec?.label ?? humanize(key), value: formatValue(value, spec?.unit) };
    });
}

export function collectionDates(endsAt: string | null) {
  const end = endsAt ? formatDate(endsAt) : "";
  return end ? `Until ${end}` : "";
}
