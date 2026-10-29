// Shapes returned by the GPS tracks API, and their display formatting.
import type { LegMode } from "./gpsModes";

export interface GpsLeg {
  id: number;
  seq: number;
  mode: LegMode;
  started_at: string;
  ended_at: string;
  distance_km: number;
  max_speed_kmh: number;
  lat: number;
  lon: number;
  lines: [number, number][][];
  title: string | null;
  note: string | null;
  is_hidden: boolean;
}

export interface GpsTrack {
  id: number;
  source_file: string;
  local_date: string;
  timezone: string;
  started_at: string;
  ended_at: string;
  point_count: number;
  wake_count: number;
  poi_count: number;
  distance_km: number;
  max_speed_kmh: number;
  title: string | null;
  note: string | null;
  legs_source: "auto" | "annotated";
  legs: GpsLeg[];
}

export interface UploadResult {
  file: string;
  status: "created" | "replaced" | "error";
  detail: string | null;
}

export function fmtTime(iso: string, tz: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: tz,
  });
}

export function fmtDay(localDate: string): string {
  // local_date is already the local calendar day; format it without shifting
  return new Date(`${localDate}T12:00:00Z`).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

export function fmtDuration(fromIso: string, toIso: string): string {
  const min = Math.round(
    (new Date(toIso).getTime() - new Date(fromIso).getTime()) / 60000,
  );
  if (min < 60) return `${min} min`;
  return `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")} min`;
}

export function fmtKm(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km < 10 ? km.toFixed(1) : Math.round(km)} km`;
}
