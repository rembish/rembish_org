import { useEffect, useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { BiX, BiSearch } from "react-icons/bi";
import Flag from "./Flag";

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

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export interface TripFormData {
  start_date: string;
  end_date: string | null;
  trip_type: string;
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  destinations: TripDestinationInput[];
  cities: TripCityInput[];
  participant_ids: number[];
  other_participants_count: number | null;
}

interface TripFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: TripFormData) => Promise<void>;
  initialData?: TripFormData | null;
  title: string;
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

const emptyFormData: TripFormData = {
  start_date: "",
  end_date: null,
  trip_type: "regular",
  flights_count: null,
  working_days: null,
  rental_car: null,
  description: null,
  destinations: [],
  cities: [],
  participant_ids: [],
  other_participants_count: null,
};

export default function TripFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  title,
}: TripFormModalProps) {
  const [formData, setFormData] = useState<TripFormData>(emptyFormData);
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);
  const [userOptions, setUserOptions] = useState<UserOption[]>([]);
  const [destSearch, setDestSearch] = useState("");
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(
    new Set(),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // City search state
  const [citySearch, setCitySearch] = useState("");
  const [cityResults, setCityResults] = useState<CitySearchResult[]>([]);
  const [citySearching, setCitySearching] = useState(false);
  const debouncedCitySearch = useDebounce(citySearch, 400);

  // Load options on mount
  useEffect(() => {
    if (!isOpen) return;

    Promise.all([
      fetch("/api/v1/travels/tcc-options", { credentials: "include" }).then(
        (r) => r.json(),
      ),
      fetch("/api/v1/travels/users-options", { credentials: "include" }).then(
        (r) => r.json(),
      ),
    ])
      .then(([tccData, usersData]) => {
        setTccOptions(tccData.destinations || []);
        setUserOptions(usersData.users || []);
      })
      .catch((err) => {
        console.error("Failed to load options:", err);
        setError("Failed to load form options");
      });
  }, [isOpen]);

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

  // Reset form when modal opens/closes or initialData changes
  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData(initialData);
      } else {
        setFormData(emptyFormData);
      }
      setError(null);
      setDestSearch("");
      setCitySearch("");
      setCityResults([]);
      setExpandedRegions(new Set());
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const addCity = (result: CitySearchResult) => {
    // Don't add duplicates
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

    setSaving(true);
    try {
      await onSave(dataToSave);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save trip");
    } finally {
      setSaving(false);
    }
  };

  const toggleDestination = (destId: number, isPartial: boolean = false) => {
    setFormData((prev) => {
      const existing = prev.destinations.find(
        (d) => d.tcc_destination_id === destId,
      );
      if (existing) {
        // Remove it
        return {
          ...prev,
          destinations: prev.destinations.filter(
            (d) => d.tcc_destination_id !== destId,
          ),
        };
      } else {
        // Add it - clear search field for quick next entry
        setDestSearch("");
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
    // Expand if manually toggled open
    if (expandedRegions.has(region)) return true;
    // Expand if has selected destinations
    if (selectedRegions.has(region)) return true;
    // Expand all when searching
    if (destSearch) return true;
    return false;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            <BiX />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="trip-form">
          {error && <div className="form-error">{error}</div>}

          {/* Dates Section */}
          <div className="form-section">
            <h3>Dates</h3>
            <div className="form-group">
              <label>Date Range *</label>
              <DatePicker
                selectsRange
                startDate={
                  formData.start_date ? new Date(formData.start_date) : null
                }
                endDate={formData.end_date ? new Date(formData.end_date) : null}
                onChange={(dates) => {
                  const [start, end] = dates as [Date | null, Date | null];
                  setFormData((prev) => ({
                    ...prev,
                    start_date: start ? start.toISOString().split("T")[0] : "",
                    end_date: end ? end.toISOString().split("T")[0] : null,
                  }));
                }}
                dateFormat="d MMM yyyy"
                placeholderText="Select date range"
                className="date-range-input"
                isClearable
                monthsShown={2}
                calendarStartDay={1}
              />
            </div>
          </div>

          {/* Destinations Section */}
          <div className="form-section">
            <h3>TCC Destinations</h3>

            {/* Selected destinations */}
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

            {/* Search input */}
            <div className="search-input">
              <BiSearch />
              <input
                type="text"
                placeholder="Search destinations..."
                value={destSearch}
                onChange={(e) => setDestSearch(e.target.value)}
              />
            </div>

            {/* Destination list - only show when searching */}
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

            {/* Selected cities as chips */}
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

            {/* City search */}
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

              {/* Search results dropdown */}
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
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-save" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
