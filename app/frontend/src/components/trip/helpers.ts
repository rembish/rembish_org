import { useEffect, useState } from "react";
import { BiTrain, BiBus, BiWater } from "react-icons/bi";
import type { TCCDestinationOption, TripFormData } from "./types";

export const PLATFORM_LABELS: Record<string, string> = {
  booking: "Booking.com",
  agoda: "Agoda",
  airbnb: "Airbnb",
  direct: "Direct",
  other: "Other",
};

export const PAYMENT_STATUS_LABELS: Record<string, string> = {
  paid: "Paid",
  pay_at_property: "Pay at property",
  pay_by_date: "Pay by date",
};

export const TRANSPORT_TYPE_ICONS: Record<
  string,
  React.ComponentType<{ size?: number }>
> = {
  train: BiTrain,
  bus: BiBus,
  ferry: BiWater,
};

export const TRANSPORT_TYPE_LABELS: Record<string, string> = {
  train: "Train",
  bus: "Bus",
  ferry: "Ferry",
};

// Socket type letter → common name
export const SOCKET_NAMES: Record<string, string> = {
  A: "US",
  B: "US-G",
  C: "EU",
  D: "IN",
  E: "FR",
  F: "Schuko",
  G: "UK",
  H: "IL",
  I: "AU",
  J: "CH",
  K: "DK",
  L: "IT",
  M: "ZA",
  N: "BR",
  O: "TH",
};

export const emptyFormData: TripFormData = {
  start_date: "",
  end_date: null,
  trip_type: "regular",
  flights_count: null,
  working_days: null,
  rental_car: null,
  description: null,
  departure_type: "morning",
  arrival_type: "evening",
  destinations: [],
  cities: [],
  participant_ids: [],
  other_participants_count: null,
};

export function formatRentalDatetime(dt: string): string {
  // Input: "YYYY-MM-DD HH:MM" or "YYYY-MM-DDTHH:MM"
  const normalized = dt.replace("T", " ");
  const [datePart, timePart] = normalized.split(" ");
  if (!datePart) return dt;
  const [y, m, d] = datePart.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const formatted = date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  return timePart ? `${formatted}, ${timePart}` : formatted;
}

// Parse date string (YYYY-MM-DD) as local date, not UTC
export function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

// Format date as YYYY-MM-DD in local timezone
export function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Debounce hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// Group destinations by region
export function groupByRegion(
  destinations: TCCDestinationOption[],
): Map<string, TCCDestinationOption[]> {
  const grouped = new Map<string, TCCDestinationOption[]>();
  for (const dest of destinations) {
    const region = dest.region;
    if (!grouped.has(region)) {
      grouped.set(region, []);
    }
    grouped.get(region)!.push(dest);
  }
  return grouped;
}

export function formatSocketName(type: string): string {
  return SOCKET_NAMES[type] || type;
}

// Format currency rates with smart multiplier for weak currencies
export function formatCurrencyRate(
  code: string,
  rates: Record<string, number>,
): string {
  const entries = Object.entries(rates).filter(([k]) => k !== code);
  if (entries.length === 0) return "";

  // Find the smallest rate value to determine multiplier
  const minRate = Math.min(...entries.map(([, v]) => v));
  let multiplier = 1;
  if (minRate < 0.01) multiplier = 1000;
  else if (minRate < 0.1) multiplier = 100;
  else if (minRate < 1) multiplier = 10;

  const parts = entries.map(([k, v]) => `${(v * multiplier).toFixed(2)} ${k}`);
  if (multiplier > 1) {
    return `${multiplier} ${code} = ${parts.join(" / ")}`;
  }
  return `1 ${code} = ${parts.join(" / ")}`;
}

// Format timezone as current local time
export function formatLocalTime(offsetHours: number): string {
  const now = new Date();
  // Get CET offset (UTC+1 in winter, UTC+2 in summer)
  const cetDate = new Date(
    now.toLocaleString("en-US", { timeZone: "Europe/Prague" }),
  );
  const utcDate = new Date(now.toLocaleString("en-US", { timeZone: "UTC" }));
  const cetOffsetHours = (cetDate.getTime() - utcDate.getTime()) / 3600000;
  // offsetHours is relative to CET, so country UTC offset = cetOffset + offsetHours
  const countryUtcOffset = cetOffsetHours + offsetHours;
  const countryTime = new Date(now.getTime() + countryUtcOffset * 3600000);
  // Format as HH:MM using UTC methods (since we already applied the offset)
  const hh = String(countryTime.getUTCHours()).padStart(2, "0");
  const mm = String(countryTime.getUTCMinutes()).padStart(2, "0");
  const sign = offsetHours >= 0 ? "+" : "";
  const offsetStr =
    offsetHours === Math.floor(offsetHours)
      ? `${sign}${offsetHours}`
      : `${sign}${offsetHours.toFixed(1)}`;
  return `${hh}:${mm} (CET${offsetStr})`;
}

export function tapWaterLabel(value: string): {
  text: string;
  className: string;
} {
  switch (value) {
    case "safe":
      return { text: "Safe", className: "tap-safe" };
    case "caution":
      return { text: "Caution", className: "tap-caution" };
    case "unsafe":
      return { text: "Unsafe", className: "tap-unsafe" };
    default:
      return { text: value, className: "" };
  }
}
