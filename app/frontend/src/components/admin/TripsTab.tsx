import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BiBriefcase,
  BiCalendar,
  BiCar,
  BiCheck,
  BiChevronLeft,
  BiChevronRight,
  BiCopy,
  BiLink,
  BiPaperPlane,
  BiParty,
  BiPencil,
  BiPlus,
  BiRefresh,
  BiTable,
  BiTrash,
} from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type {
  Trip,
  TripsResponse,
  TCCDestinationOption,
  Holiday,
  UserBirthday,
  PersonalEvent,
  VacationSummary,
} from "./types";
import YearCalendarView from "./YearCalendar";
import {
  getYearsWithTrips,
  tripOverlapsYear,
  buildFirstVisitMap,
  buildFirstVisitInYearMap,
  formatDateRange,
  getDuration,
  isFutureTrip,
  getTripHolidays,
} from "./tripHelpers";

export default function TripsTab({
  selectedYear,
  onYearChange,
}: {
  selectedYear: number | null;
  onYearChange: (year: number) => void;
}) {
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);

  // View mode: table or calendar
  const [viewMode, setViewMode] = useState<"table" | "calendar">(() => {
    const stored = localStorage.getItem("trips-view-mode");
    return stored === "calendar" ? "calendar" : "table";
  });

  // Destination holidays for trip badges (calendar + table)
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  // Czech holidays for calendar background coloring
  const [czechHolidays, setCzechHolidays] = useState<Holiday[]>([]);

  // User birthdays for calendar view
  const [birthdays, setBirthdays] = useState<UserBirthday[]>([]);

  // Personal events
  const [events, setEvents] = useState<PersonalEvent[]>([]);

  // Vacation balance
  const [vacationSummary, setVacationSummary] =
    useState<VacationSummary | null>(null);

  // ICS feed
  const [feedUrl, setFeedUrl] = useState<string | null>(null);
  const [feedOpen, setFeedOpen] = useState(false);
  const [feedCopied, setFeedCopied] = useState(false);

  // Persist view mode
  useEffect(() => {
    localStorage.setItem("trips-view-mode", viewMode);
  }, [viewMode]);

  const fetchTrips = useCallback(() => {
    apiFetch("/api/v1/travels/trips")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch trips");
        return res.json();
      })
      .then((data: TripsResponse) => {
        setTrips(data.trips);
        // If no year selected, default to current year or most recent
        if (!selectedYear) {
          const years = getYearsWithTrips(data.trips);
          const currentYear = new Date().getFullYear();
          onYearChange(years.includes(currentYear) ? currentYear : years[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedYear, onYearChange]);

  useEffect(() => {
    fetchTrips();
    // Fetch personal events
    apiFetch("/api/v1/travels/events")
      .then((res) => res.json())
      .then((data) => setEvents(data.events || []))
      .catch(() => {});
    // Fetch TCC options for mapping names to IDs
    apiFetch("/api/v1/travels/tcc-options")
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
    // Fetch users for birthdays
    apiFetch("/api/v1/travels/users-options")
      .then((res) => res.json())
      .then((data) => {
        const users = data.users || [];
        // Also fetch admin users to get all birthdays
        apiFetch("/api/v1/admin/users/")
          .then((res) => res.json())
          .then((adminData) => {
            const allUsers = [...users, ...(adminData.users || [])];
            const bdays: UserBirthday[] = [];
            for (const u of allUsers) {
              if (u.birthday) {
                // birthday is YYYY-MM-DD, extract MM-DD
                const mmdd = u.birthday.slice(5); // "MM-DD"
                bdays.push({
                  date: mmdd,
                  name: u.nickname || u.name || "User",
                });
              }
            }
            setBirthdays(bdays);
          })
          .catch(() => {});
      })
      .catch(() => {});
    // Fetch ICS feed token
    apiFetch("/api/v1/travels/calendar/feed-token")
      .then((res) => res.json())
      .then((data) => {
        if (data.token) {
          setFeedUrl(
            `${window.location.origin}/api/v1/travels/calendar.ics?token=${data.token}`,
          );
        }
      })
      .catch(() => {});
  }, [fetchTrips]);

  const handleRegenerateToken = async () => {
    if (
      feedUrl &&
      !confirm("Regenerate token? The old link will stop working.")
    )
      return;
    try {
      const res = await apiFetch("/api/v1/travels/calendar/regenerate-token", {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to regenerate");
      const data = await res.json();
      setFeedUrl(
        `${window.location.origin}/api/v1/travels/calendar.ics?token=${data.token}`,
      );
      setFeedCopied(false);
    } catch {
      alert("Failed to regenerate feed token");
    }
  };

  const handleCopyFeedUrl = () => {
    if (!feedUrl) return;
    navigator.clipboard.writeText(feedUrl).then(() => {
      setFeedCopied(true);
      setTimeout(() => setFeedCopied(false), 2000);
    });
  };

  // Fetch holidays for destination countries of trips in selected year
  useEffect(() => {
    if (!selectedYear || trips.length === 0 || tccOptions.length === 0) {
      setHolidays([]);
      return;
    }

    // Get trips in selected year
    const yearTrips = trips.filter((t) => tripOverlapsYear(t, selectedYear));

    // Get unique country codes from those trips' destinations
    const countryCodes = new Set<string>();
    for (const trip of yearTrips) {
      for (const dest of trip.destinations) {
        const tcc = tccOptions.find((o) => o.name === dest.name);
        if (tcc?.country_code) {
          countryCodes.add(tcc.country_code);
        }
      }
    }

    if (countryCodes.size === 0) {
      setHolidays([]);
      return;
    }

    // Fetch holidays for each country
    const fetchPromises = Array.from(countryCodes).map((code) =>
      apiFetch(`/api/v1/travels/holidays/${selectedYear}/${code}`)
        .then((res) => res.json())
        .then((data) =>
          (data.holidays || []).map(
            (h: { date: string; name: string; local_name: string | null }) => ({
              ...h,
              country_code: code,
            }),
          ),
        )
        .catch(() => []),
    );

    Promise.all(fetchPromises).then((results) => {
      setHolidays(results.flat());
    });
  }, [selectedYear, trips, tccOptions]);

  // Fetch Czech holidays for calendar background (always, regardless of trips)
  useEffect(() => {
    if (!selectedYear) {
      setCzechHolidays([]);
      return;
    }

    apiFetch(`/api/v1/travels/holidays/${selectedYear}/CZ`)
      .then((res) => res.json())
      .then((data) => {
        setCzechHolidays(
          (data.holidays || []).map(
            (h: { date: string; name: string; local_name: string | null }) => ({
              ...h,
              country_code: "CZ",
            }),
          ),
        );
      })
      .catch(() => setCzechHolidays([]));
  }, [selectedYear]);

  // Fetch vacation balance for selected year
  useEffect(() => {
    if (!selectedYear) {
      setVacationSummary(null);
      return;
    }

    apiFetch(`/api/v1/travels/vacation-summary?year=${selectedYear}`)
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => setVacationSummary(data))
      .catch(() => setVacationSummary(null));
  }, [selectedYear]);

  // Flight dates for calendar icons
  const [flightDates, setFlightDates] = useState<Map<string, string[]>>(
    new Map(),
  );

  useEffect(() => {
    if (!selectedYear) {
      setFlightDates(new Map());
      return;
    }

    apiFetch(`/api/v1/travels/flights/dates?year=${selectedYear}`)
      .then((res) => res.json())
      .then((data) =>
        setFlightDates(
          new Map(Object.entries(data.dates || {}) as [string, string[]][]),
        ),
      )
      .catch(() => setFlightDates(new Map()));
  }, [selectedYear]);

  if (loading) {
    return <p>Loading trips...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  const years = getYearsWithTrips(trips);
  const filteredTrips = selectedYear
    ? trips.filter((t) => tripOverlapsYear(t, selectedYear))
    : trips;

  // Build first visit maps
  const firstVisitEver = buildFirstVisitMap(trips);
  const firstVisitThisYear = selectedYear
    ? buildFirstVisitInYearMap(trips, selectedYear)
    : new Map<string, string>();

  // Sort by start date descending within year
  const sortedTrips = [...filteredTrips].sort(
    (a, b) =>
      new Date(b.start_date).getTime() - new Date(a.start_date).getTime(),
  );

  // Calculate stats for selected year
  const yearTrips = sortedTrips;
  const totalDays = yearTrips.reduce(
    (sum, t) => sum + getDuration(t.start_date, t.end_date),
    0,
  );
  const workTrips = yearTrips.filter((t) => t.trip_type === "work").length;
  const uniqueDestinations = new Set(
    yearTrips.flatMap((t) => t.destinations.map((d) => d.name)),
  ).size;

  const handlePrevYear = () => {
    const idx = years.indexOf(selectedYear!);
    if (idx < years.length - 1) {
      onYearChange(years[idx + 1]);
    }
  };

  const handleNextYear = () => {
    const idx = years.indexOf(selectedYear!);
    if (idx > 0) {
      onYearChange(years[idx - 1]);
    }
  };

  const handleAddTrip = () => {
    navigate("/admin/trips/new");
  };

  const handleEditTrip = (trip: Trip) => {
    navigate(`/admin/trips/${trip.id}/info`);
  };

  // Handle calendar date click
  const handleCalendarDateClick = (
    date: string,
    trip?: Trip,
    event?: PersonalEvent,
  ) => {
    if (trip) {
      handleEditTrip(trip);
    } else if (event) {
      navigate(`/admin/events/${event.id}/edit`);
    } else {
      navigate(`/admin/trips/new?date=${date}`);
    }
  };

  const deleteTripById = async (tripId: number) => {
    const res = await apiFetch(`/api/v1/travels/trips/${tripId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete trip");
    fetchTrips();
  };

  const handleDeleteTrip = async (tripId: number) => {
    if (!confirm("Are you sure you want to delete this trip?")) return;

    try {
      await deleteTripById(tripId);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete trip");
    }
  };

  return (
    <div className="admin-trips">
      <div className="trips-header">
        <div className="year-selector">
          <button
            className="year-nav-btn"
            onClick={handlePrevYear}
            disabled={years.indexOf(selectedYear!) >= years.length - 1}
          >
            <BiChevronLeft />
          </button>
          <select
            value={selectedYear || ""}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="year-select"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <button
            className="year-nav-btn"
            onClick={handleNextYear}
            disabled={years.indexOf(selectedYear!) <= 0}
          >
            <BiChevronRight />
          </button>
          <button
            className="view-toggle-btn"
            onClick={() =>
              setViewMode((v) => (v === "table" ? "calendar" : "table"))
            }
            title={viewMode === "table" ? "Calendar view" : "Table view"}
          >
            {viewMode === "table" ? <BiCalendar /> : <BiTable />}
          </button>
          <button
            className="btn-add-trip"
            onClick={handleAddTrip}
            title="Add Trip"
          >
            <BiPlus /> <span className="btn-label">Add Trip</span>
          </button>
          <button
            className="btn-add-event"
            onClick={() => navigate("/admin/events/new")}
            title="Add Event"
          >
            <BiPlus /> <span className="btn-label">Add Event</span>
          </button>
          <div className="ics-feed-wrapper">
            <button
              className="view-toggle-btn"
              onClick={() => setFeedOpen((v) => !v)}
              title="ICS Calendar Feed"
            >
              <BiLink />
            </button>
            {feedOpen && (
              <div className="ics-feed-popup">
                {feedUrl ? (
                  <>
                    <div className="ics-feed-url">
                      <input type="text" value={feedUrl} readOnly />
                      <button onClick={handleCopyFeedUrl} title="Copy URL">
                        {feedCopied ? <BiCheck /> : <BiCopy />}
                      </button>
                    </div>
                    <button
                      className="ics-feed-regen"
                      onClick={handleRegenerateToken}
                    >
                      <BiRefresh /> Regenerate
                    </button>
                  </>
                ) : (
                  <button
                    className="ics-feed-regen"
                    onClick={handleRegenerateToken}
                  >
                    <BiRefresh /> Generate Feed URL
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="trips-stats">
          <span className="stat-trips">
            <b>{yearTrips.length}</b> trips
          </span>
          <span>
            <b>{totalDays}</b> days
          </span>
          <span>
            <b>{uniqueDestinations}</b> TCC
          </span>
          {workTrips > 0 && (
            <span className="stat-work">
              <b>{workTrips}</b> work
            </span>
          )}
          {selectedYear &&
            events.filter(
              (e) => new Date(e.event_date).getFullYear() === selectedYear,
            ).length > 0 && (
              <span className="stat-events">
                <b>
                  {
                    events.filter(
                      (e) =>
                        new Date(e.event_date).getFullYear() === selectedYear,
                    ).length
                  }
                </b>{" "}
                events
              </span>
            )}
          {vacationSummary && (
            <span
              className="vacation-balance"
              dangerouslySetInnerHTML={{
                __html: `🏖️ <b>${vacationSummary.used_days}</b>${vacationSummary.planned_days > 0 ? `<span class="vacation-planned"><b>+${vacationSummary.planned_days}</b></span>` : ""} spent / <span class="vacation-remaining ${vacationSummary.remaining_days > 0 ? "vacation-ok" : "vacation-low"}"><b>${vacationSummary.remaining_days}</b> left</span>`,
              }}
            />
          )}
        </div>
      </div>

      {viewMode === "calendar" && selectedYear ? (
        <YearCalendarView
          year={selectedYear}
          trips={filteredTrips}
          holidays={holidays}
          czechHolidays={czechHolidays}
          birthdays={birthdays}
          events={events.filter(
            (e) => new Date(e.event_date).getFullYear() === selectedYear,
          )}
          flightDates={flightDates}
          onDateClick={handleCalendarDateClick}
          tccOptions={tccOptions}
        />
      ) : (
        <div className="trips-rows">
          {sortedTrips.map((trip) => {
            const isOverlapping =
              new Date(trip.start_date).getFullYear() !==
              (trip.end_date
                ? new Date(trip.end_date).getFullYear()
                : new Date(trip.start_date).getFullYear());
            const isFuture = isFutureTrip(trip);

            return (
              <div
                key={trip.id}
                className={`trip-row ${trip.trip_type !== "regular" ? `${trip.trip_type}-trip` : ""} ${isOverlapping ? "overlapping" : ""} ${isFuture ? "future-trip" : ""}`}
              >
                <div className="trip-row-date">
                  <span className="trip-date-range">
                    {formatDateRange(trip.start_date, trip.end_date)}
                  </span>
                  <div className="trip-date-meta">
                    <span
                      className="trip-badge days"
                      title={`${getDuration(trip.start_date, trip.end_date)} days`}
                    >
                      {getDuration(trip.start_date, trip.end_date)}d
                    </span>
                    {isFuture && (
                      <span
                        className="trip-badge future"
                        title="Future trip (not in stats)"
                      >
                        ⏳
                      </span>
                    )}
                    {trip.trip_type === "work" && (
                      <span
                        className="trip-badge work"
                        title={
                          trip.working_days
                            ? `${trip.working_days} working days`
                            : "Work trip"
                        }
                      >
                        <BiBriefcase />
                        {trip.working_days && <span>{trip.working_days}</span>}
                      </span>
                    )}
                    {trip.trip_type === "relocation" && (
                      <span
                        className="trip-badge relocation"
                        title="Relocation"
                      >
                        📦
                      </span>
                    )}
                    {trip.flights_count && trip.flights_count > 0 && (
                      <span
                        className="trip-badge flights"
                        title={`${trip.flights_count} flights`}
                      >
                        <BiPaperPlane />
                        <span>{trip.flights_count}</span>
                      </span>
                    )}
                    {trip.rental_car && (
                      <span className="trip-badge car" title={trip.rental_car}>
                        <BiCar />
                      </span>
                    )}
                    {isFuture &&
                      (() => {
                        const tripHolidays = getTripHolidays(
                          trip,
                          holidays,
                          tccOptions,
                        );
                        if (tripHolidays.length > 0) {
                          const holidayNames = tripHolidays
                            .map((h) => h.name)
                            .join(", ");
                          return (
                            <span
                              className="trip-badge holiday"
                              title={holidayNames}
                            >
                              <BiParty />
                            </span>
                          );
                        }
                        return null;
                      })()}
                  </div>
                </div>
                <div className="trip-row-main">
                  <div className="trip-destinations-row">
                    <span className="trip-destinations">
                      {trip.destinations.map((d, i) => {
                        const isFirstEver =
                          firstVisitEver.get(d.name) === trip.start_date;
                        const isFirstThisYear =
                          !isFirstEver &&
                          firstVisitThisYear.get(d.name) === trip.start_date;
                        return (
                          <span key={i}>
                            {i > 0 && ", "}
                            <span
                              className={
                                isFirstEver
                                  ? "dest-first-ever"
                                  : isFirstThisYear
                                    ? "dest-first-year"
                                    : ""
                              }
                            >
                              {d.name}
                            </span>
                          </span>
                        );
                      })}
                      {trip.destinations.length === 0 && "—"}
                    </span>
                    {(trip.participants.length > 0 ||
                      (trip.other_participants_count &&
                        trip.other_participants_count > 0)) && (
                      <span className="trip-participants-inline">
                        {trip.participants.map((p) => (
                          <span
                            key={p.id}
                            className="participant-avatar"
                            title={p.name || p.nickname || "Unknown"}
                          >
                            {p.picture ? (
                              <img src={p.picture} alt={p.nickname || ""} />
                            ) : (
                              <span className="avatar-initial">
                                {(p.nickname || p.name || "?")[0]}
                              </span>
                            )}
                          </span>
                        ))}
                        {trip.other_participants_count &&
                          trip.other_participants_count > 0 && (
                            <span className="participant-count">
                              +{trip.other_participants_count}
                            </span>
                          )}
                      </span>
                    )}
                  </div>
                  {trip.cities.length > 0 && (
                    <div className="trip-cities">
                      {trip.cities.map((city, i) => (
                        <span key={city.name}>
                          {i > 0 && ", "}
                          {city.is_partial ? (
                            <span className="city-partial">({city.name})</span>
                          ) : (
                            city.name
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                  {trip.description && (
                    <div className="trip-description">{trip.description}</div>
                  )}
                  <div className="trip-row-actions">
                    <button
                      className="trip-action-btn"
                      onClick={() => handleEditTrip(trip)}
                      title="Edit trip"
                    >
                      <BiPencil />
                    </button>
                    <button
                      className="trip-action-btn delete"
                      onClick={() => handleDeleteTrip(trip.id)}
                      title="Delete trip"
                    >
                      <BiTrash />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="trips-total">
        Total: {trips.length} trips across {years.length} years
      </div>
    </div>
  );
}
