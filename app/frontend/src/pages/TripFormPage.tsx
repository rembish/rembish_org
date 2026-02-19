import { useEffect, useRef, useState } from "react";
import {
  Navigate,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
  BiArrowBack,
  BiSearch,
  BiError,
  BiTrash,
  BiX,
  BiSignal5,
  BiSolidPlane,
} from "react-icons/bi";
import Flag from "../components/Flag";
import { useAuth } from "../hooks/useAuth";

interface TCCDestinationOption {
  id: number;
  name: string;
  region: string;
  country_code: string | null;
}

interface UserOption {
  id: number;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

interface TripDestinationInput {
  tcc_destination_id: number;
  is_partial: boolean;
}

interface TripCityInput {
  name: string;
  is_partial: boolean;
}

interface CitySearchResult {
  name: string;
  country: string | null;
  country_code: string | null;
  display_name: string | null;
  source: string;
}

interface TripHoliday {
  date: string;
  name: string;
  local_name: string | null;
  country_code: string;
  country_name: string;
}

interface TripFormData {
  start_date: string;
  end_date: string | null;
  trip_type: string;
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  departure_type: string;
  arrival_type: string;
  destinations: TripDestinationInput[];
  cities: TripCityInput[];
  participant_ids: number[];
  other_participants_count: number | null;
}

// Country info types
interface CountryInfoTCCDest {
  name: string;
  is_partial: boolean;
}

interface CurrencyInfo {
  code: string;
  name: string | null;
  rates: Record<string, number> | null;
}

interface WeatherInfo {
  avg_temp_c: number | null;
  min_temp_c: number | null;
  max_temp_c: number | null;
  avg_precipitation_mm: number | null;
  rainy_days: number | null;
  month: string;
}

interface CountryHoliday {
  date: string;
  name: string;
  local_name: string | null;
}

interface SunriseSunset {
  sunrise: string;
  sunset: string;
  day_length_hours: number;
}

interface HealthVaccination {
  vaccine: string;
  priority: string;
  notes: string | null;
  covered: boolean;
}

interface MalariaInfo {
  risk: boolean;
  areas: string | null;
  species: string | null;
  prophylaxis: string[];
  drug_resistance: string[];
}

interface HealthRequirements {
  vaccinations_required: HealthVaccination[];
  vaccinations_recommended: HealthVaccination[];
  vaccinations_routine: string[];
  malaria: MalariaInfo | null;
  other_risks: string[];
}

interface CountryInfoData {
  country_name: string;
  iso_alpha2: string;
  tcc_destinations: CountryInfoTCCDest[];
  socket_types: string | null;
  voltage: string | null;
  phone_code: string | null;
  driving_side: string | null;
  emergency_number: string | null;
  tap_water: string | null;
  currency: CurrencyInfo | null;
  weather: WeatherInfo | null;
  timezone_offset_hours: number | null;
  holidays: CountryHoliday[];
  languages: string | null;
  tipping: string | null;
  speed_limits: string | null;
  visa_free_days: number | null;
  eu_roaming: boolean | null;
  adapter_needed: boolean | null;
  sunrise_sunset: SunriseSunset | null;
  health: HealthRequirements | null;
}

// Flight types
interface AirportData {
  id: number;
  iata_code: string;
  name: string | null;
  city: string | null;
  country_code: string | null;
}

interface FlightDataItem {
  id: number;
  trip_id: number;
  flight_date: string;
  flight_number: string;
  airline_name: string | null;
  departure_airport: AirportData;
  arrival_airport: AirportData;
  departure_time: string | null;
  arrival_time: string | null;
  arrival_date: string | null;
  terminal: string | null;
  arrival_terminal: string | null;
  gate: string | null;
  aircraft_type: string | null;
  seat: string | null;
  booking_reference: string | null;
  notes: string | null;
}

interface FlightLookupLeg {
  flight_number: string;
  airline_name: string | null;
  departure_iata: string;
  departure_name: string | null;
  arrival_iata: string;
  arrival_name: string | null;
  departure_time: string | null;
  arrival_time: string | null;
  departure_date: string | null;
  arrival_date: string | null;
  terminal: string | null;
  arrival_terminal: string | null;
  aircraft_type: string | null;
}

// Parse date string (YYYY-MM-DD) as local date, not UTC
function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

// Format date as YYYY-MM-DD in local timezone
function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// Group destinations by region
function groupByRegion(
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

// Socket type letter → common name
const SOCKET_NAMES: Record<string, string> = {
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

function formatSocketName(type: string): string {
  return SOCKET_NAMES[type] || type;
}

// Format currency rates with smart multiplier for weak currencies
function formatCurrencyRate(
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
function formatLocalTime(offsetHours: number): string {
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

function tapWaterLabel(value: string): { text: string; className: string } {
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

const emptyFormData: TripFormData = {
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

export default function TripFormPage() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { tripId } = useParams();
  const [searchParams] = useSearchParams();

  const isEdit = !!tripId;
  const preselectedDate = searchParams.get("date");

  // Tab from URL: /info, /edit, or /transport
  const activeTab: "edit" | "info" | "transport" = location.pathname.endsWith(
    "/transport",
  )
    ? "transport"
    : isEdit && !location.pathname.endsWith("/edit")
      ? "info"
      : "edit";

  const [formData, setFormData] = useState<TripFormData>(() => {
    if (preselectedDate) {
      return { ...emptyFormData, start_date: preselectedDate };
    }
    return emptyFormData;
  });
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);
  const [userOptions, setUserOptions] = useState<UserOption[]>([]);
  const [destSearch, setDestSearch] = useState("");
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(
    new Set(),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingTrip, setLoadingTrip] = useState(isEdit);
  const destSearchRef = useRef<HTMLInputElement>(null);

  // City search state
  const [citySearch, setCitySearch] = useState("");
  const [cityResults, setCityResults] = useState<CitySearchResult[]>([]);
  const [citySearching, setCitySearching] = useState(false);
  const debouncedCitySearch = useDebounce(citySearch, 400);

  // Holidays during trip state
  const [tripHolidays, setTripHolidays] = useState<TripHoliday[]>([]);
  const [holidaysVisible, setHolidaysVisible] = useState(false);

  // Personal events conflict state
  const [allEvents, setAllEvents] = useState<
    {
      id: number;
      event_date: string;
      end_date: string | null;
      title: string;
      category_emoji: string;
    }[]
  >([]);
  const [conflictingEvents, setConflictingEvents] = useState<typeof allEvents>(
    [],
  );
  const [eventsVisible, setEventsVisible] = useState(false);

  // Info tab state
  const [countryInfo, setCountryInfo] = useState<CountryInfoData[]>([]);
  const [loadingInfo, setLoadingInfo] = useState(false);

  // Transport tab state
  const [flights, setFlights] = useState<FlightDataItem[]>([]);
  const [loadingFlights, setLoadingFlights] = useState(false);
  const [lookupNumber, setLookupNumber] = useState("");
  const [lookupDate, setLookupDate] = useState("");
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupLegs, setLookupLegs] = useState<FlightLookupLeg[]>([]);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [selectedLegs, setSelectedLegs] = useState<Set<number>>(new Set());
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualForm, setManualForm] = useState({
    flight_number: "",
    flight_date: "",
    departure_iata: "",
    arrival_iata: "",
    departure_time: "",
    arrival_time: "",
    airline_name: "",
    aircraft_type: "",
  });
  const [addingFlights, setAddingFlights] = useState(false);
  const [tripCitiesDisplay, setTripCitiesDisplay] = useState<
    { name: string; country_code: string | null }[]
  >([]);

  // Load TCC options, user options, and personal events on mount
  useEffect(() => {
    Promise.all([
      fetch("/api/v1/travels/tcc-options", { credentials: "include" }).then(
        (r) => r.json(),
      ),
      fetch("/api/v1/travels/users-options", { credentials: "include" }).then(
        (r) => r.json(),
      ),
      fetch("/api/v1/travels/events", { credentials: "include" }).then((r) =>
        r.json(),
      ),
    ])
      .then(([tccData, usersData, eventsData]) => {
        setTccOptions(tccData.destinations || []);
        setUserOptions(usersData.users || []);
        setAllEvents(eventsData.events || []);
      })
      .catch((err) => {
        console.error("Failed to load options:", err);
        setError("Failed to load form options");
      });
  }, []);

  // Fetch trip data when editing (after tccOptions are loaded)
  useEffect(() => {
    if (!isEdit || tccOptions.length === 0) return;

    fetch(`/api/v1/travels/trips/${tripId}`, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Trip not found");
        return r.json();
      })
      .then((trip) => {
        setFormData({
          start_date: trip.start_date,
          end_date: trip.end_date,
          trip_type: trip.trip_type,
          flights_count: trip.flights_count,
          working_days: trip.working_days,
          rental_car: trip.rental_car,
          description: trip.description,
          departure_type: trip.departure_type || "morning",
          arrival_type: trip.arrival_type || "evening",
          destinations: (trip.destinations || [])
            .map((d: { name: string; is_partial: boolean }) => {
              const tccOpt = tccOptions.find((o) => o.name === d.name);
              return {
                tcc_destination_id: tccOpt?.id || 0,
                is_partial: d.is_partial,
              };
            })
            .filter(
              (d: { tcc_destination_id: number }) => d.tcc_destination_id !== 0,
            ),
          cities: (trip.cities || []).map(
            (c: { name: string; is_partial: boolean }) => ({
              name: c.name,
              is_partial: c.is_partial,
            }),
          ),
          participant_ids: (trip.participants || []).map(
            (p: { id: number }) => p.id,
          ),
          other_participants_count: trip.other_participants_count,
        });
        setTripCitiesDisplay(
          (trip.cities || []).map(
            (c: { name: string; country_code: string | null }) => ({
              name: c.name,
              country_code: c.country_code || null,
            }),
          ),
        );
        setLoadingTrip(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingTrip(false);
      });
  }, [isEdit, tripId, tccOptions]);

  // Fetch country info when switching to Info tab
  useEffect(() => {
    if (activeTab !== "info" || !isEdit) return;

    setLoadingInfo(true);
    fetch(`/api/v1/travels/trips/${tripId}/country-info`, {
      credentials: "include",
    })
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load country info");
        return r.json();
      })
      .then((data) => {
        setCountryInfo(data.countries || []);
      })
      .catch((err) => {
        console.error("Failed to load country info:", err);
      })
      .finally(() => setLoadingInfo(false));
  }, [activeTab, isEdit, tripId]);

  // Fetch flights when switching to Transport tab
  useEffect(() => {
    if (activeTab !== "transport" || !isEdit) return;

    setLoadingFlights(true);
    fetch(`/api/v1/travels/trips/${tripId}/flights`, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load flights");
        return r.json();
      })
      .then((data) => setFlights(data.flights || []))
      .catch((err) => console.error("Failed to load flights:", err))
      .finally(() => setLoadingFlights(false));
  }, [activeTab, isEdit, tripId]);

  // Sync flights_count in formData when flights list changes
  useEffect(() => {
    if (flights.length > 0) {
      setFormData((prev) => ({ ...prev, flights_count: flights.length }));
    }
  }, [flights]);

  // Default lookup date to trip start_date
  useEffect(() => {
    if (formData.start_date && !lookupDate) {
      setLookupDate(formData.start_date);
    }
  }, [formData.start_date, lookupDate]);

  // Search cities when debounced search changes
  useEffect(() => {
    if (!debouncedCitySearch || debouncedCitySearch.length < 2) {
      setCityResults([]);
      return;
    }

    // Get country codes from selected TCC destinations
    const countryCodes = formData.destinations
      .map((d) => {
        const tcc = tccOptions.find((t) => t.id === d.tcc_destination_id);
        return tcc?.country_code;
      })
      .filter((c): c is string => !!c);

    const params = new URLSearchParams({ q: debouncedCitySearch });
    if (countryCodes.length > 0) {
      params.set("country_codes", countryCodes.join(","));
    }

    setCitySearching(true);
    fetch(`/api/v1/travels/cities-search?${params}`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => {
        setCityResults(data.results || []);
      })
      .catch(() => setCityResults([]))
      .finally(() => setCitySearching(false));
  }, [debouncedCitySearch, formData.destinations, tccOptions]);

  // Fetch holidays for trip dates and destinations
  useEffect(() => {
    if (!formData.start_date || formData.destinations.length === 0) {
      setTripHolidays([]);
      return;
    }

    // Get unique country codes from selected destinations
    const countryMap = new Map<string, string>(); // code -> name
    for (const dest of formData.destinations) {
      const tcc = tccOptions.find((t) => t.id === dest.tcc_destination_id);
      if (tcc?.country_code) {
        countryMap.set(
          tcc.country_code,
          tcc.name.split(",")[0] || tcc.country_code,
        );
      }
    }

    if (countryMap.size === 0) {
      setTripHolidays([]);
      return;
    }

    const startDate = new Date(formData.start_date);
    const endDate = formData.end_date ? new Date(formData.end_date) : startDate;

    // Get years to fetch (handle multi-year trips)
    const years = new Set<number>();
    const current = new Date(startDate);
    while (current <= endDate) {
      years.add(current.getFullYear());
      current.setMonth(current.getMonth() + 1);
    }

    // Fetch holidays for each country/year combo
    const fetchPromises: Promise<TripHoliday[]>[] = [];
    for (const [countryCode, countryName] of countryMap) {
      for (const year of years) {
        fetchPromises.push(
          fetch(`/api/v1/travels/holidays/${year}/${countryCode}`, {
            credentials: "include",
          })
            .then((r) => r.json())
            .then((data) => {
              const holidays = data.holidays || [];
              return holidays
                .filter((h: { date: string }) => {
                  const d = new Date(h.date);
                  return d >= startDate && d <= endDate;
                })
                .map(
                  (h: {
                    date: string;
                    name: string;
                    local_name: string | null;
                  }) => ({
                    date: h.date,
                    name: h.name,
                    local_name: h.local_name,
                    country_code: countryCode,
                    country_name: countryName,
                  }),
                );
            })
            .catch(() => [] as TripHoliday[]),
        );
      }
    }

    Promise.all(fetchPromises).then((results) => {
      const allHolidays = results
        .flat()
        .sort((a, b) => a.date.localeCompare(b.date));
      setTripHolidays(allHolidays);
      if (allHolidays.length > 0) {
        setHolidaysVisible(true);
      }
    });
  }, [
    formData.start_date,
    formData.end_date,
    formData.destinations,
    tccOptions,
  ]);

  // Check for personal event conflicts when dates change
  useEffect(() => {
    if (!formData.start_date || allEvents.length === 0) {
      setConflictingEvents([]);
      return;
    }

    const tripStart = formData.start_date;
    const tripEnd = formData.end_date || formData.start_date;

    const conflicts = allEvents.filter((e) => {
      const eventStart = e.event_date;
      const eventEnd = e.end_date || e.event_date;
      return eventStart <= tripEnd && eventEnd >= tripStart;
    });

    setConflictingEvents(conflicts);
    if (conflicts.length > 0) {
      setEventsVisible(true);
    }
  }, [formData.start_date, formData.end_date, allEvents]);

  const goBack = () => {
    // Navigate back to trips tab, picking the year from start_date or current year
    const year = formData.start_date
      ? new Date(formData.start_date).getFullYear()
      : new Date().getFullYear();
    navigate(`/admin/trips/${year}`);
  };

  // Auth guard
  if (authLoading) return null;
  if (!user?.is_admin) return <Navigate to="/" replace />;

  if (loadingTrip) {
    return (
      <div className="trip-form-page">
        <p>Loading trip...</p>
      </div>
    );
  }

  const addCity = (result: CitySearchResult) => {
    if (formData.cities.some((c) => c.name === result.name)) return;
    setFormData((prev) => ({
      ...prev,
      cities: [...prev.cities, { name: result.name, is_partial: false }],
    }));
    setCitySearch("");
    setCityResults([]);
  };

  const removeCity = (name: string) => {
    setFormData((prev) => ({
      ...prev,
      cities: prev.cities.filter((c) => c.name !== name),
    }));
  };

  const toggleCityPartial = (name: string) => {
    setFormData((prev) => ({
      ...prev,
      cities: prev.cities.map((c) =>
        c.name === name ? { ...c, is_partial: !c.is_partial } : c,
      ),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.start_date) {
      setError("Start date is required");
      return;
    }

    // Auto-set trip_type based on working_days
    const tripType =
      formData.working_days && formData.working_days > 0 ? "work" : "regular";

    const dataToSave: TripFormData = {
      ...formData,
      trip_type: tripType,
    };

    const url = isEdit
      ? `/api/v1/travels/trips/${tripId}`
      : "/api/v1/travels/trips";
    const method = isEdit ? "PUT" : "POST";

    setSaving(true);
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(dataToSave),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save trip");
      }

      goBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save trip");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!isEdit) return;
    if (!confirm("Are you sure you want to delete this trip?")) return;

    try {
      const res = await fetch(`/api/v1/travels/trips/${tripId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete trip");
      goBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete trip");
    }
  };

  const toggleDestination = (destId: number, isPartial: boolean = false) => {
    setFormData((prev) => {
      const existing = prev.destinations.find(
        (d) => d.tcc_destination_id === destId,
      );
      if (existing) {
        return {
          ...prev,
          destinations: prev.destinations.filter(
            (d) => d.tcc_destination_id !== destId,
          ),
        };
      } else {
        setDestSearch("");
        setTimeout(() => destSearchRef.current?.focus(), 0);
        return {
          ...prev,
          destinations: [
            ...prev.destinations,
            { tcc_destination_id: destId, is_partial: isPartial },
          ],
        };
      }
    });
  };

  const toggleParticipant = (userId: number) => {
    setFormData((prev) => {
      if (prev.participant_ids.includes(userId)) {
        return {
          ...prev,
          participant_ids: prev.participant_ids.filter((id) => id !== userId),
        };
      } else {
        return {
          ...prev,
          participant_ids: [...prev.participant_ids, userId],
        };
      }
    });
  };

  const toggleRegion = (region: string) => {
    setExpandedRegions((prev) => {
      const next = new Set(prev);
      if (next.has(region)) {
        next.delete(region);
      } else {
        next.add(region);
      }
      return next;
    });
  };

  // Filter destinations by search
  const filteredDestinations = destSearch
    ? tccOptions.filter((d) =>
        d.name.toLowerCase().includes(destSearch.toLowerCase()),
      )
    : tccOptions;

  const groupedDestinations = groupByRegion(filteredDestinations);

  // Get selected destinations with names
  const selectedDestinations = formData.destinations.map((d) => {
    const opt = tccOptions.find((o) => o.id === d.tcc_destination_id);
    return { ...d, name: opt?.name || "Unknown", region: opt?.region };
  });

  // Regions that should be auto-expanded (have selections or match search)
  const selectedRegions = new Set(
    selectedDestinations.map((d) => d.region).filter(Boolean),
  );
  const isRegionExpanded = (region: string) => {
    if (expandedRegions.has(region)) return true;
    if (selectedRegions.has(region)) return true;
    if (destSearch) return true;
    return false;
  };

  const handleLookup = async () => {
    if (!lookupNumber || !lookupDate) return;
    setLookupLoading(true);
    setLookupLegs([]);
    setLookupError(null);
    setSelectedLegs(new Set());
    try {
      const params = new URLSearchParams({
        flight_number: lookupNumber,
        date: lookupDate,
      });
      const res = await fetch(`/api/v1/travels/flights/lookup?${params}`, {
        credentials: "include",
      });
      if (res.status === 501) {
        setLookupError("Flight lookup not configured. Use manual entry.");
        setShowManualForm(true);
        return;
      }
      if (!res.ok) throw new Error("Lookup failed");
      const data = await res.json();
      if (data.error) setLookupError(data.error);
      setLookupLegs(data.legs || []);
      if ((data.legs || []).length === 0 && !data.error) {
        setLookupError("No flights found. Try manual entry.");
      }
    } catch {
      setLookupError("Lookup failed. Try manual entry.");
    } finally {
      setLookupLoading(false);
    }
  };

  const handleAddSelectedLegs = async () => {
    if (selectedLegs.size === 0 || !lookupDate) return;
    setAddingFlights(true);
    try {
      for (const idx of Array.from(selectedLegs).sort()) {
        const leg = lookupLegs[idx];
        await fetch(`/api/v1/travels/trips/${tripId}/flights`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            flight_date: leg.departure_date || lookupDate,
            flight_number: leg.flight_number,
            airline_name: leg.airline_name,
            departure_iata: leg.departure_iata,
            arrival_iata: leg.arrival_iata,
            departure_time: leg.departure_time,
            arrival_time: leg.arrival_time,
            arrival_date: leg.arrival_date,
            terminal: leg.terminal,
            arrival_terminal: leg.arrival_terminal,
            aircraft_type: leg.aircraft_type,
          }),
        });
      }
      // Refresh flights list
      const res = await fetch(`/api/v1/travels/trips/${tripId}/flights`, {
        credentials: "include",
      });
      const data = await res.json();
      setFlights(data.flights || []);
      setLookupLegs([]);
      setSelectedLegs(new Set());
      setLookupNumber("");
    } catch (err) {
      console.error("Failed to add flights:", err);
    } finally {
      setAddingFlights(false);
    }
  };

  const handleManualAdd = async () => {
    if (
      !manualForm.flight_number ||
      !manualForm.departure_iata ||
      !manualForm.arrival_iata
    )
      return;
    setAddingFlights(true);
    try {
      const res = await fetch(`/api/v1/travels/trips/${tripId}/flights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          flight_date:
            manualForm.flight_date || lookupDate || formData.start_date,
          flight_number: manualForm.flight_number,
          departure_iata: manualForm.departure_iata,
          arrival_iata: manualForm.arrival_iata,
          departure_time: manualForm.departure_time || null,
          arrival_time: manualForm.arrival_time || null,
          airline_name: manualForm.airline_name || null,
          aircraft_type: manualForm.aircraft_type || null,
        }),
      });
      if (!res.ok) throw new Error("Failed to add flight");
      // Refresh
      const listRes = await fetch(`/api/v1/travels/trips/${tripId}/flights`, {
        credentials: "include",
      });
      const data = await listRes.json();
      setFlights(data.flights || []);
      setManualForm({
        flight_number: "",
        flight_date: "",
        departure_iata: "",
        arrival_iata: "",
        departure_time: "",
        arrival_time: "",
        airline_name: "",
        aircraft_type: "",
      });
      setShowManualForm(false);
    } catch (err) {
      console.error("Failed to add flight:", err);
    } finally {
      setAddingFlights(false);
    }
  };

  const handleDeleteFlight = async (flightId: number) => {
    if (!confirm("Delete this flight?")) return;
    try {
      await fetch(`/api/v1/travels/flights/${flightId}`, {
        method: "DELETE",
        credentials: "include",
      });
      setFlights((prev) => prev.filter((f) => f.id !== flightId));
    } catch (err) {
      console.error("Failed to delete flight:", err);
    }
  };

  const toggleLeg = (idx: number) => {
    setSelectedLegs((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const renderTransportTab = () => {
    if (loadingFlights) {
      return (
        <div className="trip-transport-tab">
          <p>Loading flights...</p>
        </div>
      );
    }

    const tripDests = formData.destinations
      .map((d) => tccOptions.find((o) => o.id === d.tcc_destination_id)?.name)
      .filter(Boolean);
    const dateFrom = formData.start_date
      ? new Date(formData.start_date + "T00:00:00").toLocaleDateString(
          "en-GB",
          { day: "numeric", month: "short", year: "numeric" },
        )
      : "";
    const dateTo = formData.end_date
      ? new Date(formData.end_date + "T00:00:00").toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "";

    return (
      <div className="trip-transport-tab">
        {/* Trip context for email search */}
        <div className="transport-trip-context">
          <span className="transport-dates">
            {dateFrom}
            {dateTo && ` – ${dateTo}`}
          </span>
          {tripDests.length > 0 && (
            <span className="transport-destinations">
              {tripDests.join(", ")}
            </span>
          )}
          {tripCitiesDisplay.length > 0 && (
            <div className="transport-cities">
              {tripCitiesDisplay.map((c, i) => (
                <span key={i} className="transport-city">
                  {c.country_code && <Flag code={c.country_code} size={14} />}
                  {c.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Flight list */}
        <div className="form-section">
          <h3>Flights ({flights.length})</h3>
          {flights.length === 0 ? (
            <p className="flight-empty">No flights added yet.</p>
          ) : (
            <div className="flight-list">
              {flights.map((f) => (
                <div key={f.id} className="flight-card">
                  <div className="flight-card-main">
                    <div className="flight-card-header">
                      <span className="flight-number">{f.flight_number}</span>
                      {f.airline_name && (
                        <span className="flight-airline">{f.airline_name}</span>
                      )}
                      {f.aircraft_type && (
                        <span className="flight-aircraft">
                          {f.aircraft_type}
                        </span>
                      )}
                    </div>
                    <div className="flight-route">
                      <span className="flight-airport">
                        <strong>{f.departure_airport.iata_code}</strong>
                        {f.departure_time && (
                          <span className="flight-time">
                            {f.departure_time}
                          </span>
                        )}
                        <span className="flight-date">
                          {new Date(
                            f.flight_date + "T00:00:00",
                          ).toLocaleDateString("en-GB", {
                            day: "numeric",
                            month: "short",
                          })}
                        </span>
                        {f.terminal && (
                          <span className="flight-terminal">T{f.terminal}</span>
                        )}
                      </span>
                      <span className="flight-arrow">
                        <BiSolidPlane />
                      </span>
                      <span className="flight-airport">
                        <strong>{f.arrival_airport.iata_code}</strong>
                        {f.arrival_time && (
                          <span className="flight-time">{f.arrival_time}</span>
                        )}
                        <span className="flight-date">
                          {new Date(
                            (f.arrival_date || f.flight_date) + "T00:00:00",
                          ).toLocaleDateString("en-GB", {
                            day: "numeric",
                            month: "short",
                          })}
                        </span>
                        {f.arrival_terminal && (
                          <span className="flight-terminal">
                            T{f.arrival_terminal}
                          </span>
                        )}
                      </span>
                    </div>
                    {(f.seat || f.booking_reference) && (
                      <div className="flight-details">
                        {f.seat && (
                          <span className="flight-badge">Seat {f.seat}</span>
                        )}
                        {f.booking_reference && (
                          <span className="flight-badge">
                            {f.booking_reference}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <button
                    className="flight-delete-btn"
                    onClick={() => handleDeleteFlight(f.id)}
                    title="Delete flight"
                  >
                    <BiTrash />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add flight section */}
        <div className="form-section">
          <h3>Add Flight</h3>
          {(() => {
            const today = new Date();
            const yearAgo = new Date(today);
            yearAgo.setFullYear(yearAgo.getFullYear() - 1);
            const weeksAhead = new Date(today);
            weeksAhead.setDate(weeksAhead.getDate() + 42);
            const tripStart = formData.start_date
              ? new Date(formData.start_date)
              : null;
            const tripEnd = formData.end_date
              ? new Date(formData.end_date)
              : tripStart;
            if (tripEnd && tripEnd < yearAgo) {
              return (
                <p className="flight-api-notice">
                  This trip is older than 1 year — flight lookup is unavailable.
                  Use manual entry below.
                </p>
              );
            }
            if (tripStart && tripStart > weeksAhead) {
              return (
                <p className="flight-api-notice">
                  This trip is more than 6 weeks away — airline schedules may
                  not be published yet. Lookup may return no results.
                </p>
              );
            }
            return null;
          })()}
          <div className="flight-lookup-row">
            <div className="form-group">
              <label>Flight Number</label>
              <input
                type="text"
                value={lookupNumber}
                onChange={(e) => setLookupNumber(e.target.value.toUpperCase())}
                placeholder="TK1770"
                className="flight-input"
              />
            </div>
            <div className="form-group">
              <label>Date</label>
              <input
                type="date"
                value={lookupDate}
                onChange={(e) => setLookupDate(e.target.value)}
                min={formData.start_date || undefined}
                max={formData.end_date || undefined}
                className="flight-input"
              />
            </div>
            <button
              type="button"
              className="btn-save flight-lookup-btn"
              onClick={handleLookup}
              disabled={lookupLoading || !lookupNumber || !lookupDate}
            >
              {lookupLoading ? "Looking up..." : "Lookup"}
            </button>
          </div>

          {lookupError && <p className="flight-lookup-error">{lookupError}</p>}

          {lookupLegs.length > 0 && (
            <div className="flight-lookup-results">
              {lookupLegs.map((leg, idx) => (
                <label key={idx} className="flight-lookup-leg">
                  <input
                    type="checkbox"
                    checked={selectedLegs.has(idx)}
                    onChange={() => toggleLeg(idx)}
                  />
                  <div className="flight-leg-info">
                    <span className="flight-leg-route">
                      <strong>{leg.departure_iata}</strong>
                      {leg.departure_name && (
                        <span className="flight-leg-airport-name">
                          {leg.departure_name}
                        </span>
                      )}
                      {leg.departure_time && ` ${leg.departure_time}`}
                      {" → "}
                      <strong>{leg.arrival_iata}</strong>
                      {leg.arrival_name && (
                        <span className="flight-leg-airport-name">
                          {leg.arrival_name}
                        </span>
                      )}
                      {leg.arrival_time && ` ${leg.arrival_time}`}
                      {leg.arrival_date && (
                        <span className="flight-next-day">+1</span>
                      )}
                    </span>
                    <span className="flight-leg-details">
                      {[
                        leg.airline_name,
                        leg.aircraft_type,
                        leg.terminal ? `Terminal ${leg.terminal}` : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </div>
                </label>
              ))}
              <button
                type="button"
                className="btn-save"
                onClick={handleAddSelectedLegs}
                disabled={selectedLegs.size === 0 || addingFlights}
              >
                {addingFlights
                  ? "Adding..."
                  : `Add selected (${selectedLegs.size})`}
              </button>
            </div>
          )}

          {!showManualForm && (
            <button
              type="button"
              className="flight-manual-link"
              onClick={() => setShowManualForm(true)}
            >
              Manual entry
            </button>
          )}

          {showManualForm && (
            <div className="flight-manual-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Flight Number *</label>
                  <input
                    type="text"
                    value={manualForm.flight_number}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        flight_number: e.target.value.toUpperCase(),
                      }))
                    }
                    placeholder="TK1770"
                  />
                </div>
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={manualForm.flight_date || lookupDate}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        flight_date: e.target.value,
                      }))
                    }
                    min={formData.start_date || undefined}
                    max={formData.end_date || undefined}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>From IATA *</label>
                  <input
                    type="text"
                    value={manualForm.departure_iata}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        departure_iata: e.target.value.toUpperCase(),
                      }))
                    }
                    placeholder="PRG"
                    maxLength={3}
                  />
                </div>
                <div className="form-group">
                  <label>To IATA *</label>
                  <input
                    type="text"
                    value={manualForm.arrival_iata}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        arrival_iata: e.target.value.toUpperCase(),
                      }))
                    }
                    placeholder="IST"
                    maxLength={3}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Departure Time</label>
                  <input
                    type="time"
                    value={manualForm.departure_time}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        departure_time: e.target.value,
                      }))
                    }
                  />
                </div>
                <div className="form-group">
                  <label>Arrival Time</label>
                  <input
                    type="time"
                    value={manualForm.arrival_time}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        arrival_time: e.target.value,
                      }))
                    }
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Airline</label>
                  <input
                    type="text"
                    value={manualForm.airline_name}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        airline_name: e.target.value,
                      }))
                    }
                    placeholder="Turkish Airlines"
                  />
                </div>
                <div className="form-group">
                  <label>Aircraft</label>
                  <input
                    type="text"
                    value={manualForm.aircraft_type}
                    onChange={(e) =>
                      setManualForm((prev) => ({
                        ...prev,
                        aircraft_type: e.target.value,
                      }))
                    }
                    placeholder="Airbus A321"
                  />
                </div>
              </div>
              <div className="flight-manual-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowManualForm(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-save"
                  onClick={handleManualAdd}
                  disabled={
                    addingFlights ||
                    !manualForm.flight_number ||
                    !manualForm.departure_iata ||
                    !manualForm.arrival_iata
                  }
                >
                  {addingFlights ? "Adding..." : "Add Flight"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderInfoPanel = () => {
    if (loadingInfo) {
      return (
        <div className="country-info-panel">
          <p className="country-info-loading">Loading country info...</p>
        </div>
      );
    }

    if (countryInfo.length === 0) {
      return (
        <div className="country-info-panel">
          <p className="country-info-empty">
            No destination countries for this trip.
          </p>
        </div>
      );
    }

    return (
      <div className="country-info-panel">
        {countryInfo.map((country) => (
          <div
            key={country.iso_alpha2 || country.country_name}
            className="country-info-card"
          >
            <div className="country-info-header">
              <Flag code={country.iso_alpha2} size={24} />
              <h3>{country.country_name}</h3>
            </div>

            {country.tcc_destinations.length > 0 && (
              <div className="country-tcc-tags">
                {country.tcc_destinations.map((d) => (
                  <span
                    key={d.name}
                    className={`country-tcc-tag ${d.is_partial ? "partial" : ""}`}
                  >
                    {d.name}
                  </span>
                ))}
              </div>
            )}

            <div className="country-info-grid">
              {country.socket_types && (
                <div className="country-info-item">
                  <span className="info-label">
                    Sockets
                    {country.adapter_needed !== null && (
                      <span
                        className={`adapter-badge ${country.adapter_needed ? "adapter-yes" : "adapter-no"}`}
                      >
                        {country.adapter_needed
                          ? " — adapter needed"
                          : " — compatible"}
                      </span>
                    )}
                  </span>
                  <span className="info-value socket-types">
                    {country.socket_types.split(",").map((t) => (
                      <span
                        key={t}
                        className="socket-type"
                        title={`Type ${t} (${formatSocketName(t)})`}
                      >
                        <img
                          src={`/sockets/${t.toLowerCase()}.svg`}
                          alt={formatSocketName(t)}
                          className="socket-icon"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display =
                              "none";
                          }}
                        />
                        <span className="socket-label">
                          {formatSocketName(t)}
                        </span>
                      </span>
                    ))}
                  </span>
                </div>
              )}

              {country.voltage && (
                <div className="country-info-item">
                  <span className="info-label">Voltage</span>
                  <span className="info-value">{country.voltage}</span>
                </div>
              )}

              {country.phone_code && (
                <div className="country-info-item">
                  <span className="info-label">Phone</span>
                  <span className="info-value phone-info">
                    <span>{country.phone_code}</span>
                    {country.eu_roaming !== null && (
                      <span
                        className={`roaming-badge ${country.eu_roaming ? "roaming-eu" : "roaming-local"}`}
                      >
                        <BiSignal5 />
                        {country.eu_roaming ? "EU roaming" : "Local SIM"}
                      </span>
                    )}
                  </span>
                </div>
              )}

              {country.driving_side && (
                <div className="country-info-item">
                  <span className="info-label">Driving</span>
                  <span className="info-value driving-info">
                    <span>
                      {country.driving_side === "left"
                        ? "Left side"
                        : "Right side"}
                    </span>
                    {country.speed_limits && (
                      <span className="speed-limits">
                        {(() => {
                          const [city, rural, hwy] =
                            country.speed_limits.split("/");
                          return `${city}/${rural}/${hwy === "none" ? "∞" : hwy} km/h`;
                        })()}
                      </span>
                    )}
                  </span>
                </div>
              )}

              {country.emergency_number && (
                <div className="country-info-item">
                  <span className="info-label">Emergency</span>
                  <span className="info-value emergency-number">
                    {country.emergency_number}
                  </span>
                </div>
              )}

              {country.tap_water && (
                <div className="country-info-item">
                  <span className="info-label">Tap Water</span>
                  <span
                    className={`info-value ${tapWaterLabel(country.tap_water).className}`}
                  >
                    {tapWaterLabel(country.tap_water).text}
                  </span>
                </div>
              )}

              {country.currency && (
                <div className="country-info-item">
                  <span className="info-label">Currency</span>
                  <span className="info-value">
                    {country.currency.code}
                    {country.currency.name && (
                      <span className="currency-name">
                        {" "}
                        ({country.currency.name})
                      </span>
                    )}
                    {country.currency.rates && (
                      <span className="currency-rates">
                        {formatCurrencyRate(
                          country.currency.code,
                          country.currency.rates,
                        )}
                      </span>
                    )}
                    {country.tipping && (
                      <span className="tipping-info">
                        Tip: {country.tipping}
                      </span>
                    )}
                  </span>
                </div>
              )}

              {country.weather && (
                <div className="country-info-item">
                  <span className="info-label">
                    Weather ({country.weather.month})
                  </span>
                  <span className="info-value weather-details">
                    {country.weather.min_temp_c !== null &&
                      country.weather.max_temp_c !== null && (
                        <span className="weather-temp">
                          {country.weather.min_temp_c}°…
                          {country.weather.max_temp_c}°C
                        </span>
                      )}
                    {country.weather.min_temp_c === null &&
                      country.weather.avg_temp_c !== null && (
                        <span className="weather-temp">
                          {country.weather.avg_temp_c}°C
                        </span>
                      )}
                    {country.weather.rainy_days !== null && (
                      <span className="weather-rain">
                        {country.weather.rainy_days} rainy days
                      </span>
                    )}
                    {country.weather.rainy_days === null &&
                      country.weather.avg_precipitation_mm !== null && (
                        <span className="weather-rain">
                          {country.weather.avg_precipitation_mm} mm/day
                        </span>
                      )}
                  </span>
                </div>
              )}

              {country.timezone_offset_hours !== null && (
                <div className="country-info-item">
                  <span className="info-label">Local Time</span>
                  <span className="info-value">
                    {formatLocalTime(country.timezone_offset_hours)}
                  </span>
                </div>
              )}

              {country.languages && (
                <div className="country-info-item">
                  <span className="info-label">Languages</span>
                  <span className="info-value">{country.languages}</span>
                </div>
              )}

              {country.visa_free_days !== null && (
                <div className="country-info-item">
                  <span className="info-label">Visa (CZ)</span>
                  <span
                    className={`info-value ${country.visa_free_days === 0 ? "visa-required" : "visa-free"}`}
                  >
                    {country.visa_free_days === 0
                      ? "Visa required"
                      : `${country.visa_free_days} days`}
                  </span>
                </div>
              )}
              {country.visa_free_days === null && country.eu_roaming && (
                <div className="country-info-item">
                  <span className="info-label">Visa (CZ)</span>
                  <span className="info-value visa-free">EU / Unlimited</span>
                </div>
              )}

              {country.sunrise_sunset && (
                <div className="country-info-item">
                  <span className="info-label">Daylight</span>
                  <span className="info-value sunrise-sunset">
                    {country.sunrise_sunset.sunrise} –{" "}
                    {country.sunrise_sunset.sunset} (
                    {country.sunrise_sunset.day_length_hours}h)
                  </span>
                </div>
              )}
            </div>

            {country.holidays.length > 0 && (
              <div className="country-info-holidays">
                <span className="info-label">Public Holidays</span>
                <div className="country-holidays-list">
                  {country.holidays.map((h, i) => (
                    <div
                      key={`${h.date}-${i}`}
                      className="country-holiday-item"
                    >
                      <span className="country-holiday-date">
                        {new Date(h.date + "T00:00:00").toLocaleDateString(
                          "en-GB",
                          { day: "numeric", month: "short" },
                        )}
                      </span>
                      <span
                        className="country-holiday-name"
                        title={h.local_name || ""}
                      >
                        {h.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {country.health && (
              <div className="country-info-health">
                {country.health.vaccinations_required.length > 0 && (
                  <div className="health-section">
                    <span className="info-label">Required Vaccinations</span>
                    <div className="health-vaccines">
                      {country.health.vaccinations_required.map((v) => (
                        <span
                          key={v.vaccine}
                          className={`health-vaccine ${v.covered ? "health-vaccine-covered" : "health-vaccine-required"}`}
                          title={v.notes || ""}
                        >
                          {v.covered && "✓ "}
                          {v.vaccine}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {country.health.vaccinations_recommended.length > 0 && (
                  <div className="health-section">
                    <span className="info-label">Recommended Vaccinations</span>
                    <div className="health-vaccines">
                      {country.health.vaccinations_recommended.map((v) => (
                        <span
                          key={v.vaccine}
                          className={`health-vaccine ${v.covered ? "health-vaccine-covered" : v.priority === "consider" ? "health-vaccine-consider" : "health-vaccine-recommended"}`}
                          title={v.notes || ""}
                        >
                          {v.covered && "✓ "}
                          {v.vaccine}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {country.health.malaria && country.health.malaria.risk && (
                  <div className="health-section health-malaria">
                    <span className="info-label">Malaria Risk</span>
                    <div className="health-malaria-details">
                      {country.health.malaria.areas && (
                        <span className="health-malaria-areas">
                          {country.health.malaria.areas}
                        </span>
                      )}
                      {country.health.malaria.prophylaxis.length > 0 && (
                        <span className="health-malaria-prophylaxis">
                          Prophylaxis:{" "}
                          {country.health.malaria.prophylaxis.join(", ")}
                        </span>
                      )}
                      {country.health.malaria.drug_resistance.length > 0 && (
                        <span className="health-malaria-resistance">
                          Resistance:{" "}
                          {country.health.malaria.drug_resistance.join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {country.health.other_risks.length > 0 && (
                  <div className="health-section">
                    <span className="info-label">Other Risks</span>
                    <div className="health-risks">
                      {country.health.other_risks.map((r) => (
                        <span key={r} className="health-risk-tag">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="trip-form-page">
      <div className="trip-form-page-header">
        <button type="button" className="trip-form-back-btn" onClick={goBack}>
          <BiArrowBack />
        </button>
        <h2>{isEdit ? "Edit Trip" : "Add Trip"}</h2>
      </div>

      {isEdit && (
        <div className="trip-form-tabs">
          <button
            className={`trip-form-tab ${activeTab === "info" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/info`, { replace: true })
            }
          >
            Info
          </button>
          <button
            className={`trip-form-tab ${activeTab === "edit" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/edit`, { replace: true })
            }
          >
            Edit
          </button>
          <button
            className={`trip-form-tab ${activeTab === "transport" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/transport`, { replace: true })
            }
          >
            Transport
          </button>
        </div>
      )}

      {activeTab === "transport" && isEdit ? (
        renderTransportTab()
      ) : activeTab === "info" && isEdit ? (
        renderInfoPanel()
      ) : (
        <form onSubmit={handleSubmit} className="trip-form">
          {error && <div className="form-error">{error}</div>}

          {/* Dates Section */}
          <div className="form-section">
            <h3>Dates</h3>
            <div className="dates-row">
              <div className="form-group">
                <label>Date Range *</label>
                <DatePicker
                  selectsRange
                  startDate={
                    formData.start_date
                      ? parseLocalDate(formData.start_date)
                      : null
                  }
                  endDate={
                    formData.end_date ? parseLocalDate(formData.end_date) : null
                  }
                  onChange={(dates) => {
                    const [start, end] = dates as [Date | null, Date | null];
                    setFormData((prev) => ({
                      ...prev,
                      start_date: start ? formatLocalDate(start) : "",
                      end_date: end ? formatLocalDate(end) : null,
                    }));
                  }}
                  dateFormat="d MMM yyyy"
                  placeholderText="Select date range"
                  className="date-range-input"
                  isClearable
                  monthsShown={2}
                  calendarStartDay={1}
                  popperPlacement="bottom-start"
                />
              </div>

              {/* Holidays Warning Icon */}
              {tripHolidays.length > 0 && (
                <div className="holidays-warning-container">
                  <button
                    type="button"
                    className="holidays-warning-btn"
                    onClick={() => setHolidaysVisible(!holidaysVisible)}
                    title={`${tripHolidays.length} public holiday(s) during trip`}
                  >
                    <BiError />
                    <span className="holidays-count">
                      {tripHolidays.length}
                    </span>
                  </button>
                  {holidaysVisible && (
                    <div className="holidays-dropdown">
                      <h4>Public Holidays During Trip</h4>
                      {tripHolidays.map((h, i) => (
                        <div
                          key={`${h.date}-${h.country_code}-${i}`}
                          className="holiday-item"
                        >
                          <span className="holiday-date">
                            {new Date(h.date + "T00:00:00").toLocaleDateString(
                              "en-GB",
                              {
                                day: "numeric",
                                month: "short",
                              },
                            )}
                          </span>
                          <span
                            className="holiday-name"
                            title={h.local_name || ""}
                          >
                            {h.name}
                          </span>
                          <span className="holiday-country">
                            <Flag code={h.country_code} size={14} />
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {/* Personal Events Warning Icon */}
              {conflictingEvents.length > 0 && (
                <div className="holidays-warning-container">
                  <button
                    type="button"
                    className="events-warning-btn"
                    onClick={() => setEventsVisible(!eventsVisible)}
                    title={`${conflictingEvents.length} personal event(s) during trip`}
                  >
                    <BiError />
                    <span className="holidays-count">
                      {conflictingEvents.length}
                    </span>
                  </button>
                  {eventsVisible && (
                    <div className="holidays-dropdown">
                      <h4>Personal Events During Trip</h4>
                      {conflictingEvents.map((e) => (
                        <div
                          key={e.id}
                          className="holiday-item holiday-item-link"
                          onClick={() => navigate(`/admin/events/${e.id}/edit`)}
                        >
                          <span className="holiday-date">
                            {new Date(
                              e.event_date + "T00:00:00",
                            ).toLocaleDateString("en-GB", {
                              day: "numeric",
                              month: "short",
                            })}
                            {e.end_date &&
                              e.end_date !== e.event_date &&
                              ` – ${new Date(e.end_date + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`}
                          </span>
                          <span className="holiday-name">
                            {e.category_emoji} {e.title}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div className="form-group departure-arrival-group">
                <label>Departure</label>
                <select
                  value={formData.departure_type}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      departure_type: e.target.value,
                    }))
                  }
                >
                  <option value="morning">Morning</option>
                  <option value="midday">Half-day</option>
                  <option value="evening">Late evening</option>
                </select>
              </div>
              <div className="form-group departure-arrival-group">
                <label>Arrival</label>
                <select
                  value={formData.arrival_type}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      arrival_type: e.target.value,
                    }))
                  }
                >
                  <option value="morning">Early morning</option>
                  <option value="midday">Half-day</option>
                  <option value="evening">Evening</option>
                </select>
              </div>
            </div>
          </div>

          {/* Destinations Section */}
          <div className="form-section">
            <h3>TCC Destinations</h3>

            {selectedDestinations.length > 0 && (
              <div className="selected-items">
                {selectedDestinations.map((dest) => (
                  <div key={dest.tcc_destination_id} className="selected-chip">
                    <span>{dest.name}</span>
                    <button
                      type="button"
                      className="chip-remove"
                      onClick={() => toggleDestination(dest.tcc_destination_id)}
                    >
                      <BiX />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="search-input">
              <BiSearch />
              <input
                ref={destSearchRef}
                type="text"
                placeholder="Search destinations..."
                value={destSearch}
                onChange={(e) => setDestSearch(e.target.value)}
              />
            </div>

            {destSearch && (
              <div className="destination-list">
                {Array.from(groupedDestinations.entries()).map(
                  ([region, dests]) => {
                    const expanded = isRegionExpanded(region);
                    return (
                      <div key={region} className="region-group">
                        <button
                          type="button"
                          className="region-header"
                          onClick={() => toggleRegion(region)}
                        >
                          <span>
                            {expanded ? "▼" : "▶"} {region}
                          </span>
                          <span className="region-count">{dests.length}</span>
                        </button>
                        {expanded && (
                          <div className="region-items">
                            {dests.map((dest) => {
                              const isSelected = formData.destinations.some(
                                (d) => d.tcc_destination_id === dest.id,
                              );
                              return (
                                <label
                                  key={dest.id}
                                  className={`dest-item ${isSelected ? "selected" : ""}`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => toggleDestination(dest.id)}
                                  />
                                  <span>{dest.name}</span>
                                </label>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  },
                )}
              </div>
            )}
          </div>

          {/* Cities Section */}
          <div className="form-section">
            <h3>Cities</h3>

            {formData.cities.length > 0 && (
              <div className="selected-items">
                {formData.cities.map((city) => (
                  <div
                    key={city.name}
                    className={`selected-chip ${city.is_partial ? "partial" : ""}`}
                  >
                    <span
                      className="chip-name"
                      onClick={() => toggleCityPartial(city.name)}
                      title={
                        city.is_partial
                          ? "Click to mark as full visit"
                          : "Click to mark as partial"
                      }
                    >
                      {city.name}
                    </span>
                    <button
                      type="button"
                      className="chip-remove"
                      onClick={() => removeCity(city.name)}
                    >
                      <BiX />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="city-search-container">
              <div className="search-input">
                <BiSearch />
                <input
                  type="text"
                  placeholder="Search cities..."
                  value={citySearch}
                  onChange={(e) => setCitySearch(e.target.value)}
                />
                {citySearching && <span className="search-spinner">...</span>}
              </div>

              {cityResults.length > 0 && (
                <div className="city-results">
                  {cityResults.map((result, i) => (
                    <button
                      key={`${result.name}-${i}`}
                      type="button"
                      className="city-result-item"
                      onClick={() => addCity(result)}
                    >
                      {result.country_code && (
                        <Flag
                          code={result.country_code}
                          size={16}
                          title={result.country || ""}
                        />
                      )}
                      <span className="city-name">{result.name}</span>
                      {result.country && (
                        <span className="city-country">{result.country}</span>
                      )}
                      <span className={`city-source ${result.source}`}>
                        {result.source === "local" ? "✓" : "🌐"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Participants Section */}
          <div className="form-section">
            <h3>Participants</h3>
            <div className="participants-grid">
              {userOptions.map((user) => (
                <label
                  key={user.id}
                  className={`participant-item ${formData.participant_ids.includes(user.id) ? "selected" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={formData.participant_ids.includes(user.id)}
                    onChange={() => toggleParticipant(user.id)}
                  />
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt=""
                      className="participant-pic"
                    />
                  ) : (
                    <span className="participant-initial">
                      {(user.nickname || user.name || "?")[0]}
                    </span>
                  )}
                  <span>{user.nickname || user.name || "Unknown"}</span>
                </label>
              ))}
              <div
                className={`participant-item other-participant ${(formData.other_participants_count || 0) > 0 ? "selected" : ""}`}
              >
                <input
                  type="number"
                  min="0"
                  value={formData.other_participants_count || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      other_participants_count: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    }))
                  }
                  className="other-count-input"
                  onClick={(e) => e.stopPropagation()}
                />
                <span>Other</span>
              </div>
            </div>
          </div>

          {/* Details Section */}
          <div className="form-section">
            <h3>Details</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Flights</label>
                <input
                  type="number"
                  min="0"
                  value={formData.flights_count || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      flights_count: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    }))
                  }
                  placeholder="0"
                />
              </div>
              <div className="form-group">
                <label>Working Days</label>
                <input
                  type="number"
                  min="0"
                  value={formData.working_days || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      working_days: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    }))
                  }
                  placeholder="0"
                />
              </div>
              <div className="form-group">
                <label>Rental Car</label>
                <input
                  type="text"
                  value={formData.rental_car || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      rental_car: e.target.value || null,
                    }))
                  }
                  placeholder="e.g., Toyota Corolla"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description || ""}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value || null,
                  }))
                }
                placeholder="Trip notes..."
                rows={3}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="modal-actions">
            {isEdit && (
              <button
                type="button"
                className="btn-delete"
                onClick={handleDelete}
                title="Delete trip"
              >
                <BiTrash />
                <span className="btn-delete-label">Delete</span>
              </button>
            )}
            <div className="modal-actions-right">
              <button type="button" className="btn-cancel" onClick={goBack}>
                Cancel
              </button>
              <button type="submit" className="btn-save" disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
