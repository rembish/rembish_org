import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { BiSearch, BiError, BiTrash, BiX } from "react-icons/bi";
import Flag from "../Flag";
import { apiFetch } from "../../lib/api";
import type {
  TripFormData,
  TCCDestinationOption,
  UserOption,
  CitySearchResult,
  TripHoliday,
} from "./types";
import {
  useDebounce,
  parseLocalDate,
  formatLocalDate,
  groupByRegion,
} from "./helpers";

interface EditTabProps {
  formData: TripFormData;
  setFormData: React.Dispatch<React.SetStateAction<TripFormData>>;
  tccOptions: TCCDestinationOption[];
  userOptions: UserOption[];
  allEvents: {
    id: number;
    event_date: string;
    end_date: string | null;
    title: string;
    category_emoji: string;
  }[];
  isEdit: boolean;
  onSave: () => void;
  onDelete: () => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}

export default function EditTab({
  formData,
  setFormData,
  tccOptions,
  userOptions,
  allEvents,
  isEdit,
  onSave,
  onDelete,
  onCancel,
  saving,
  error,
}: EditTabProps) {
  const navigate = useNavigate();

  // Internal state
  const [destSearch, setDestSearch] = useState("");
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(
    new Set(),
  );
  const destSearchRef = useRef<HTMLInputElement>(null);
  const [citySearch, setCitySearch] = useState("");
  const [cityResults, setCityResults] = useState<CitySearchResult[]>([]);
  const [citySearching, setCitySearching] = useState(false);
  const debouncedCitySearch = useDebounce(citySearch, 400);
  const [tripHolidays, setTripHolidays] = useState<TripHoliday[]>([]);
  const [holidaysVisible, setHolidaysVisible] = useState(false);
  const [conflictingEvents, setConflictingEvents] = useState<typeof allEvents>(
    [],
  );
  const [eventsVisible, setEventsVisible] = useState(false);

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
    apiFetch(`/api/v1/travels/cities-search?${params}`)
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
          apiFetch(`/api/v1/travels/holidays/${year}/${countryCode}`)
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

  // Handlers
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

  const toggleDestination = (destId: number) => {
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
            { tcc_destination_id: destId, is_partial: false },
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave();
  };

  // Computed values
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

  return (
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
                formData.start_date ? parseLocalDate(formData.start_date) : null
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
                <span className="holidays-count">{tripHolidays.length}</span>
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
                      <span className="holiday-name" title={h.local_name || ""}>
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
                <img src={user.picture} alt="" className="participant-pic" />
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
            onClick={onDelete}
            title="Delete trip"
          >
            <BiTrash />
            <span className="btn-delete-label">Delete</span>
          </button>
        )}
        <div className="modal-actions-right">
          <button type="button" className="btn-cancel" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn-save" disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </form>
  );
}
