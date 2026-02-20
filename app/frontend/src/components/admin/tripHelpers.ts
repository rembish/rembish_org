import type { Trip, Holiday, TCCDestinationOption } from "./types";

// Check if trip overlaps with a given year (for NY trips spanning Dec-Jan)
export function countryFlag(iso: string): string {
  return iso
    .toUpperCase()
    .split("")
    .map((c) => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
    .join("");
}

export function tripOverlapsYear(trip: Trip, year: number): boolean {
  const startYear = new Date(trip.start_date).getFullYear();
  const endYear = trip.end_date
    ? new Date(trip.end_date).getFullYear()
    : startYear;
  return year >= startYear && year <= endYear;
}

// Build a map of TCC destination -> first visit date (across all trips)
export function buildFirstVisitMap(trips: Trip[]): Map<string, string> {
  const firstVisit = new Map<string, string>();
  // Sort trips by date ascending to find first visits
  const sorted = [...trips].sort(
    (a, b) =>
      new Date(a.start_date).getTime() - new Date(b.start_date).getTime(),
  );
  for (const trip of sorted) {
    for (const dest of trip.destinations) {
      if (!firstVisit.has(dest.name)) {
        firstVisit.set(dest.name, trip.start_date);
      }
    }
  }
  return firstVisit;
}

// Build a map of TCC destination -> first visit date within a specific year
export function buildFirstVisitInYearMap(
  trips: Trip[],
  year: number,
): Map<string, string> {
  const firstVisit = new Map<string, string>();
  const yearTrips = trips
    .filter((t) => tripOverlapsYear(t, year))
    .sort(
      (a, b) =>
        new Date(a.start_date).getTime() - new Date(b.start_date).getTime(),
    );

  for (const trip of yearTrips) {
    for (const dest of trip.destinations) {
      if (!firstVisit.has(dest.name)) {
        firstVisit.set(dest.name, trip.start_date);
      }
    }
  }
  return firstVisit;
}

// Get all years that have trips (including overlapping)
export function getYearsWithTrips(trips: Trip[]): number[] {
  const years = new Set<number>();
  for (const trip of trips) {
    const startYear = new Date(trip.start_date).getFullYear();
    const endYear = trip.end_date
      ? new Date(trip.end_date).getFullYear()
      : startYear;
    for (let y = startYear; y <= endYear; y++) {
      years.add(y);
    }
  }
  return Array.from(years).sort((a, b) => b - a);
}

// Format date as "D Mon" or "D Mon - D Mon" for ranges
export function formatDateRange(
  startDate: string,
  endDate: string | null,
): string {
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const start = new Date(startDate);
  const startStr = `${start.getDate()} ${months[start.getMonth()]}`;

  if (!endDate) return startStr;

  const end = new Date(endDate);
  const endStr = `${end.getDate()} ${months[end.getMonth()]}`;

  // Include year if different
  const startYear = start.getFullYear();
  const endYear = end.getFullYear();

  if (startYear !== endYear) {
    return `${start.getDate()} ${months[start.getMonth()]} ${startYear} – ${end.getDate()} ${months[end.getMonth()]} ${endYear}`;
  }

  if (startStr === endStr) return startStr;
  return `${startStr} – ${endStr}`;
}

// Calculate trip duration in days
export function getDuration(startDate: string, endDate: string | null): number {
  const start = new Date(startDate);
  const end = endDate ? new Date(endDate) : start;
  return (
    Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1
  );
}

// Check if trip is in the future (not yet completed)
export function isFutureTrip(trip: Trip): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const endDate = trip.end_date
    ? new Date(trip.end_date)
    : new Date(trip.start_date);
  return endDate > today;
}

// Get all dates in a trip's range
export function getTripDateRange(trip: Trip): string[] {
  const dates: string[] = [];
  const start = new Date(trip.start_date + "T00:00:00");
  const end = trip.end_date
    ? new Date(trip.end_date + "T00:00:00")
    : new Date(trip.start_date + "T00:00:00");
  const current = new Date(start);
  while (current <= end) {
    const y = current.getFullYear();
    const m = String(current.getMonth() + 1).padStart(2, "0");
    const d = String(current.getDate()).padStart(2, "0");
    dates.push(`${y}-${m}-${d}`);
    current.setDate(current.getDate() + 1);
  }
  return dates;
}

// Get holidays that match a trip's destinations and date range
export function getTripHolidays(
  trip: Trip,
  holidays: Holiday[],
  tccOptions: TCCDestinationOption[],
): Holiday[] {
  // Get country codes from trip destinations
  const tripCountryCodes = new Set<string>();
  for (const dest of trip.destinations) {
    const tcc = tccOptions.find((o) => o.name === dest.name);
    if (tcc?.country_code) tripCountryCodes.add(tcc.country_code);
  }
  if (tripCountryCodes.size === 0) return [];

  // Get all dates in trip range
  const tripDates = new Set(getTripDateRange(trip));

  // Find holidays that match both date and country
  return holidays.filter(
    (h) =>
      tripDates.has(h.date) &&
      h.country_code &&
      tripCountryCodes.has(h.country_code),
  );
}
