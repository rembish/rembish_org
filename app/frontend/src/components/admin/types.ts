export interface TripDestination {
  name: string;
  is_partial: boolean;
}

export interface TripCity {
  name: string;
  is_partial: boolean;
}

export interface TripParticipant {
  id: number;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

export interface Trip {
  id: number;
  start_date: string;
  end_date: string | null;
  trip_type: "regular" | "work" | "relocation";
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  departure_type: string;
  arrival_type: string;
  destinations: TripDestination[];
  cities: TripCity[];
  participants: TripParticipant[];
  other_participants_count: number | null;
}

export interface VacationSummary {
  annual_days: number;
  used_days: number;
  planned_days: number;
  remaining_days: number;
}

export interface TripsResponse {
  trips: Trip[];
  total: number;
}

export interface TCCDestinationOption {
  id: number;
  name: string;
  region: string;
  country_code: string | null;
}

export interface Holiday {
  date: string;
  name: string;
  local_name: string | null;
  country_code?: string;
}

export interface UserBirthday {
  date: string; // MM-DD format
  name: string;
}

export interface PersonalEvent {
  id: number;
  event_date: string;
  end_date: string | null;
  title: string;
  note: string | null;
  category: string;
  category_emoji: string;
}

export type AdminTab =
  | "trips"
  | "instagram"
  | "people"
  | "documents"
  | "loyalty";

export type PeopleSection = "close-ones" | "addresses" | "fixers";

export const PEOPLE_SECTIONS: { key: PeopleSection; label: string }[] = [
  { key: "close-ones", label: "Close Ones" },
  { key: "addresses", label: "Addresses" },
  { key: "fixers", label: "Fixers" },
];

export type DocSection = "ids" | "vaccinations" | "visas";

export const DOC_SECTIONS: { key: DocSection; label: string }[] = [
  { key: "ids", label: "IDs" },
  { key: "vaccinations", label: "Vaccinations" },
  { key: "visas", label: "Visas" },
];

// Instagram labeling types
export interface InstagramMedia {
  id: number;
  media_type: string;
  storage_path: string | null;
  order: number;
}

export interface InstagramPost {
  id: number; // DB id (for media endpoints)
  ig_id: string; // Instagram ID (for routing)
  caption: string | null;
  media_type: string;
  posted_at: string;
  permalink: string;
  ig_location_name: string | null;
  ig_location_lat: number | null;
  ig_location_lng: number | null;
  media: InstagramMedia[];
  position: number;
  total: number;
  un_country_id: number | null;
  tcc_destination_id: number | null;
  trip_id: number | null;
  city_id: number | null;
  is_aerial: boolean | null;
  is_cover: boolean;
  cover_media_id: number | null;
  suggested_trip: {
    id: number;
    start_date: string;
    end_date: string | null;
    destinations: string[];
  } | null;
  previous_labels: {
    un_country_id: number | null;
    un_country_name: string | null;
    tcc_destination_id: number | null;
    tcc_destination_name: string | null;
    trip_id: number | null;
    city_id: number | null;
    city_name: string | null;
    is_aerial: boolean | null;
  } | null;
}

export interface LabelingStats {
  total: number;
  labeled: number;
  skipped: number;
  unlabeled: number;
}

export interface TripOption {
  id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
}

// --- Vault types ---

export interface VaultFile {
  id: number;
  label: string | null;
  mime_type: string;
  file_size: number;
  sort_order: number;
}

export interface VaultDocument {
  id: number;
  user_id: number;
  doc_type: "passport" | "id_card" | "drivers_license";
  label: string;
  proper_name: string | null;
  issuing_country: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  number_masked: string | null;
  number_decrypted: string | null;
  notes_masked: string | null;
  notes_decrypted: string | null;
  is_archived: boolean;
  files: VaultFile[];
}

export interface VaultLoyaltyProgram {
  id: number;
  user_id: number;
  program_name: string;
  alliance: "star_alliance" | "oneworld" | "skyteam" | "none";
  tier: string | null;
  membership_number_masked: string | null;
  membership_number_decrypted: string | null;
  notes_masked: string | null;
  notes_decrypted: string | null;
  is_favorite: boolean;
}

export interface ProgramOptionAirline {
  name: string;
  flights_count: number;
}

export interface ProgramOption {
  program_name: string;
  alliance: string;
  airlines: ProgramOptionAirline[];
  total_flights: number;
}

export interface VaultUser {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

export interface VaultVaccination {
  id: number;
  user_id: number;
  vaccine_name: string;
  brand_name: string | null;
  dose_type: string | null;
  date_administered: string | null;
  expiry_date: string | null;
  batch_number_masked: string | null;
  batch_number_decrypted: string | null;
  notes_masked: string | null;
  notes_decrypted: string | null;
  files: VaultFile[];
}

export interface VaultTravelDoc {
  id: number;
  user_id: number;
  doc_type: string;
  label: string;
  document_id: number | null;
  passport_label: string | null;
  country_code: string | null;
  valid_from: string | null;
  valid_until: string | null;
  entry_type: string | null;
  notes_masked: string | null;
  notes_decrypted: string | null;
  files: VaultFile[];
  trip_ids: number[];
}

export interface VaultAddress {
  id: number;
  name: string;
  address: string;
  country_code: string | null;
  user_id: number | null;
  user_name: string | null;
  user_picture: string | null;
  notes_masked: string | null;
  notes_decrypted: string | null;
}

export interface ExtractedDocMetadata {
  doc_type: string | null;
  label: string | null;
  country_code: string | null;
  valid_from: string | null;
  valid_until: string | null;
  entry_type: string | null;
  notes: string | null;
  document_id: number | null;
  error: string | null;
}

// --- Fixer types ---

export interface FixerLink {
  type: string;
  url: string;
}

export interface Fixer {
  id: number;
  name: string;
  type: "guide" | "fixer" | "driver" | "coordinator" | "agency";
  phone: string | null;
  whatsapp: string | null;
  email: string | null;
  notes: string | null;
  rating: number | null;
  links: FixerLink[];
  country_codes: string[];
}

export const FIXER_TYPE_LABELS: Record<string, string> = {
  guide: "Guide",
  fixer: "Fixer",
  driver: "Driver",
  coordinator: "Coordinator",
  agency: "Agency",
};

export const FIXER_RATING_LABELS: Record<
  number,
  { emoji: string; label: string }
> = {
  1: { emoji: "\u{1F620}", label: "Avoid" },
  2: { emoji: "\u{1F610}", label: "Okay" },
  3: { emoji: "\u{1F642}", label: "Good" },
  4: { emoji: "\u{1F929}", label: "Great" },
};

export const FIXER_LINK_TYPES: Record<string, string> = {
  website: "Website",
  instagram: "Instagram",
  facebook: "Facebook",
  tripadvisor: "TripAdvisor",
  tourhq: "TourHQ",
  getyourguide: "GetYourGuide",
  nomadmania: "NomadMania",
  other: "Other",
};

export interface CloseOneUser {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
  birthday: string | null;
  is_admin: boolean;
  is_active: boolean;
  role: string | null;
  trips_count: number;
}

// --- Shared constants ---

export const fmtDate = (iso: string) => {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
};

export const DOC_TYPE_LABELS: Record<string, string> = {
  passport: "Passport",
  id_card: "ID Card",
  drivers_license: "Driver's License",
};

export const TRAVEL_DOC_TYPE_LABELS: Record<string, string> = {
  e_visa: "e-Visa",
  eta: "ETA",
  esta: "ESTA",
  etias: "ETIAS",
  loi: "LOI",
  entry_permit: "Entry Permit",
  travel_insurance: "Travel Insurance",
  vaccination_cert: "Vaccination Cert",
  other: "Other",
};

export const ENTRY_TYPE_LABELS: Record<string, string> = {
  single: "Single entry",
  double: "Double entry",
  multiple: "Multiple entry",
};

export const fmtFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const ALLIANCE_LABELS: Record<string, string> = {
  star_alliance: "Star Alliance",
  oneworld: "Oneworld",
  skyteam: "SkyTeam",
  none: "Independent",
};

export function expiryClass(expiry: string | null, docType: string): string {
  if (!expiry) return "";
  const exp = new Date(expiry + "T00:00:00");
  const now = new Date();
  if (exp < now) return "expiry-expired";
  const warn = new Date();
  if (docType === "passport") {
    warn.setMonth(warn.getMonth() + 7);
  } else if (docType === "vaccination") {
    // Vaccinations: warn 3 months before expiry
    warn.setMonth(warn.getMonth() + 3);
  } else {
    const d = warn.getDate();
    warn.setMonth(warn.getMonth() + 1);
    warn.setDate(d + 15);
  }
  if (exp < warn) return "expiry-warning";
  return "";
}
