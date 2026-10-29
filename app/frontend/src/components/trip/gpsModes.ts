// Leg modes for GPS tracks. Colour encodes the family (validated as a 5-hue set,
// all pairs, since any two can sit side by side on a map); the line pattern tells
// modes within a family apart, so identity never rests on colour alone.

export type LegMode =
  | "stop"
  | "gap"
  | "foot"
  | "vehicle"
  | "walk"
  | "bicycle"
  | "animal"
  | "car"
  | "bus"
  | "motorbike"
  | "train"
  | "tram"
  | "metro"
  | "boat"
  | "ferry"
  | "plane"
  | "cable_car";

type Family = "pace" | "road" | "rail" | "water" | "air" | "neutral";

const FAMILY_COLORS: Record<Family, string> = {
  pace: "#eda100",
  road: "#2a78d6",
  rail: "#008300",
  water: "#1baf7a",
  air: "#e87ba4",
  neutral: "#8a8985",
};

const DASHED = "10 6";
const DOTTED = "1 7";

interface ModeStyle {
  label: string;
  family: Family;
  dash?: string;
}

export const MODES: Record<LegMode, ModeStyle> = {
  // automatic processing only knows these four
  stop: { label: "Stop", family: "neutral" },
  gap: { label: "No fix", family: "neutral", dash: "4 6" },
  foot: { label: "On foot (auto)", family: "pace" },
  vehicle: { label: "Vehicle (auto)", family: "road" },
  // specific modes come from the analysis upload
  walk: { label: "Walk", family: "pace" },
  bicycle: { label: "Bicycle", family: "pace", dash: DASHED },
  animal: { label: "Animal", family: "pace", dash: DOTTED },
  car: { label: "Car", family: "road" },
  bus: { label: "Bus", family: "road", dash: DASHED },
  motorbike: { label: "Motorbike", family: "road", dash: DOTTED },
  train: { label: "Train", family: "rail" },
  tram: { label: "Tram", family: "rail", dash: DASHED },
  metro: { label: "Metro", family: "rail", dash: DOTTED },
  boat: { label: "Boat", family: "water" },
  ferry: { label: "Ferry", family: "water", dash: DASHED },
  plane: { label: "Plane", family: "air" },
  cable_car: { label: "Cable car", family: "air", dash: DASHED },
};

// Legend order: by family, generic before specific, stop and gap last.
export const MODE_ORDER: LegMode[] = [
  "foot",
  "walk",
  "bicycle",
  "animal",
  "vehicle",
  "car",
  "bus",
  "motorbike",
  "train",
  "tram",
  "metro",
  "boat",
  "ferry",
  "plane",
  "cable_car",
  "stop",
  "gap",
];

export function modeColor(mode: LegMode): string {
  return FAMILY_COLORS[MODES[mode].family];
}

/** True for modes where top speed is worth showing. */
export function isMotorised(mode: LegMode): boolean {
  const family = MODES[mode].family;
  return family !== "pace" && family !== "neutral";
}
