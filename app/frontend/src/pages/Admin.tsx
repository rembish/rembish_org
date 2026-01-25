import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import {
  BiBriefcase,
  BiCar,
  BiChevronLeft,
  BiChevronRight,
  BiPaperPlane,
  BiPlus,
  BiPencil,
  BiTrash,
} from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import TripFormModal, { TripFormData } from "../components/TripFormModal";

interface TripDestination {
  name: string;
  is_partial: boolean;
}

interface TripCity {
  name: string;
  is_partial: boolean;
}

interface TripParticipant {
  id: number;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

interface Trip {
  id: number;
  start_date: string;
  end_date: string | null;
  trip_type: "regular" | "work" | "relocation";
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  destinations: TripDestination[];
  cities: TripCity[];
  participants: TripParticipant[];
  other_participants_count: number | null;
}

interface TripsResponse {
  trips: Trip[];
  total: number;
}

interface TCCDestinationOption {
  id: number;
  name: string;
  region: string;
}

type AdminTab = "trips";

// Check if trip overlaps with a given year (for NY trips spanning Dec-Jan)
function tripOverlapsYear(trip: Trip, year: number): boolean {
  const startYear = new Date(trip.start_date).getFullYear();
  const endYear = trip.end_date
    ? new Date(trip.end_date).getFullYear()
    : startYear;
  return year >= startYear && year <= endYear;
}

// Build a map of TCC destination -> first visit date (across all trips)
function buildFirstVisitMap(trips: Trip[]): Map<string, string> {
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
function buildFirstVisitInYearMap(
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
function getYearsWithTrips(trips: Trip[]): number[] {
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
function formatDateRange(startDate: string, endDate: string | null): string {
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
function getDuration(startDate: string, endDate: string | null): number {
  const start = new Date(startDate);
  const end = endDate ? new Date(endDate) : start;
  return (
    Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1
  );
}

function TripsTab({
  selectedYear,
  onYearChange,
}: {
  selectedYear: number | null;
  onYearChange: (year: number) => void;
}) {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTrip, setEditingTrip] = useState<Trip | null>(null);
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);

  const fetchTrips = () => {
    fetch("/api/v1/travels/trips", { credentials: "include" })
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
  };

  useEffect(() => {
    fetchTrips();
    // Fetch TCC options for mapping names to IDs
    fetch("/api/v1/travels/tcc-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
  }, []);

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
    setEditingTrip(null);
    setModalOpen(true);
  };

  const handleEditTrip = (trip: Trip) => {
    setEditingTrip(trip);
    setModalOpen(true);
  };

  const handleDeleteTrip = async (tripId: number) => {
    if (!confirm("Are you sure you want to delete this trip?")) return;

    try {
      const res = await fetch(`/api/v1/travels/trips/${tripId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete trip");
      fetchTrips();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete trip");
    }
  };

  const handleSaveTrip = async (data: TripFormData) => {
    const url = editingTrip
      ? `/api/v1/travels/trips/${editingTrip.id}`
      : "/api/v1/travels/trips";
    const method = editingTrip ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save trip");
    }

    fetchTrips();
  };

  // Convert Trip to TripFormData for editing
  const getInitialFormData = (): TripFormData | null => {
    if (!editingTrip) return null;

    return {
      start_date: editingTrip.start_date,
      end_date: editingTrip.end_date,
      trip_type: editingTrip.trip_type,
      flights_count: editingTrip.flights_count,
      working_days: editingTrip.working_days,
      rental_car: editingTrip.rental_car,
      description: editingTrip.description,
      destinations: editingTrip.destinations.map((d) => {
        const tccOpt = tccOptions.find((o) => o.name === d.name);
        return {
          tcc_destination_id: tccOpt?.id || 0,
          is_partial: d.is_partial,
        };
      }).filter((d) => d.tcc_destination_id !== 0),
      cities: editingTrip.cities.map((c) => ({
        name: c.name,
        is_partial: c.is_partial,
      })),
      participant_ids: editingTrip.participants.map((p) => p.id),
      other_participants_count: editingTrip.other_participants_count,
    };
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
          <button className="btn-add-trip" onClick={handleAddTrip}>
            <BiPlus /> Add Trip
          </button>
        </div>
        <div className="trips-stats">
          <span>{yearTrips.length} trips</span>
          <span>{totalDays} days</span>
          <span>{uniqueDestinations} TCC</span>
          {workTrips > 0 && <span>{workTrips} work</span>}
        </div>
      </div>

      <div className="trips-rows">
        {sortedTrips.map((trip) => {
          const isOverlapping =
            new Date(trip.start_date).getFullYear() !==
            (trip.end_date
              ? new Date(trip.end_date).getFullYear()
              : new Date(trip.start_date).getFullYear());

          return (
            <div
              key={trip.id}
              className={`trip-row ${trip.trip_type !== "regular" ? `${trip.trip_type}-trip` : ""} ${isOverlapping ? "overlapping" : ""}`}
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
                    <span className="trip-badge relocation" title="Relocation">
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
                      <span
                        key={i}
                        className={city.is_partial ? "city-partial" : ""}
                      >
                        {i > 0 && ", "}
                        {city.name}
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

      <div className="trips-total">
        Total: {trips.length} trips across {years.length} years
      </div>

      <TripFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrip}
        initialData={getInitialFormData()}
        title={editingTrip ? "Edit Trip" : "Add Trip"}
      />
    </div>
  );
}

export default function Admin() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { tab, year } = useParams();
  const activeTab = (tab as AdminTab) || "trips";
  const selectedYear = year ? Number(year) : null;

  const setActiveTab = (newTab: AdminTab) => {
    if (selectedYear) {
      navigate(`/admin/${newTab}/${selectedYear}`);
    } else {
      navigate(`/admin/${newTab}`);
    }
  };

  const setSelectedYear = (newYear: number) => {
    navigate(`/admin/${activeTab}/${newYear}`);
  };

  // Redirect non-admin users
  if (!authLoading && !user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  if (authLoading) {
    return (
      <section id="admin" className="admin">
        <div className="container">
          <p>Loading...</p>
        </div>
      </section>
    );
  }

  return (
    <section id="admin" className="admin">
      <div className="container">
        <div className="admin-header">
          <h1>Admin</h1>
        </div>

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "trips" ? "active" : ""}`}
            onClick={() => setActiveTab("trips")}
          >
            Trips
          </button>
          {/* Future tabs can be added here */}
        </div>

        <div className="admin-content">
          {activeTab === "trips" && (
            <TripsTab
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />
          )}
        </div>
      </div>
    </section>
  );
}
