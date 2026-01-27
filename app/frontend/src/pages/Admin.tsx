import { useCallback, useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import {
  BiBriefcase,
  BiCake,
  BiCalendar,
  BiCar,
  BiChevronLeft,
  BiChevronRight,
  BiPaperPlane,
  BiPlus,
  BiPencil,
  BiTable,
  BiTrash,
} from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import TripFormModal, { TripFormData } from "../components/TripFormModal";
import UserFormModal, { UserFormData } from "../components/UserFormModal";

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
  country_code: string | null;
}

interface Holiday {
  date: string;
  name: string;
  local_name: string | null;
  country_code?: string;
}

interface UserBirthday {
  date: string; // MM-DD format
  name: string;
}

type AdminTab = "trips" | "close-ones";

interface CloseOneUser {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
  birthday: string | null;
  is_admin: boolean;
  is_active: boolean;
  trips_count: number;
}

function CloseOnesTab() {
  const [users, setUsers] = useState<CloseOneUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<CloseOneUser | null>(null);

  const fetchUsers = useCallback(() => {
    fetch("/api/v1/admin/users/", { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch users");
        return res.json();
      })
      .then((data) => {
        setUsers(data.users || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleAddUser = () => {
    setEditingUser(null);
    setModalOpen(true);
  };

  const handleEditUser = (user: CloseOneUser) => {
    setEditingUser(user);
    setModalOpen(true);
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("Are you sure you want to remove this user?")) return;

    try {
      const res = await fetch(`/api/v1/admin/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete user");
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  const handleSaveUser = async (data: UserFormData) => {
    const url = editingUser
      ? `/api/v1/admin/users/${editingUser.id}`
      : "/api/v1/admin/users/";
    const method = editingUser ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save user");
    }

    fetchUsers();
  };

  const getInitialFormData = (): UserFormData | null => {
    if (!editingUser) return null;
    return {
      email: editingUser.email,
      name: editingUser.name || "",
      nickname: editingUser.nickname || "",
      birthday: editingUser.birthday || "",
    };
  };

  if (loading) {
    return <p>Loading users...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  return (
    <div className="close-ones-tab">
      <div className="close-ones-header">
        <button className="btn-add-user" onClick={handleAddUser}>
          <BiPlus /> Add User
        </button>
      </div>

      <div className="users-grid">
        {users.length === 0 ? (
          <p className="no-users">No close ones added yet.</p>
        ) : (
          users.map((user) => (
            <div key={user.id} className="user-card">
              <div className="user-card-avatar">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.nickname || user.name || ""}
                  />
                ) : (
                  <span className="avatar-initial">
                    {(user.nickname ||
                      user.name ||
                      user.email)[0].toUpperCase()}
                  </span>
                )}
              </div>
              <div className="user-card-info">
                <div className="user-card-name">
                  {user.nickname || user.name || "—"}
                  {user.is_admin && <span className="admin-badge">Admin</span>}
                  <span
                    className={`status-badge ${user.is_active ? "active" : "pending"}`}
                  >
                    {user.is_active ? "Active" : "Pending"}
                  </span>
                </div>
                <div className="user-card-email">{user.email}</div>
                <div className="user-card-meta">
                  {user.birthday && (
                    <span className="birthday-badge">
                      <BiCake />{" "}
                      {new Date(user.birthday + "T00:00:00").toLocaleDateString(
                        "en-GB",
                        { day: "numeric", month: "short" },
                      )}
                    </span>
                  )}
                  {user.trips_count > 0 && (
                    <span className="trips-badge">
                      {user.trips_count} trip{user.trips_count !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <div className="user-card-actions">
                <button
                  className="user-action-btn"
                  onClick={() => handleEditUser(user)}
                  title="Edit"
                >
                  <BiPencil />
                </button>
                <button
                  className="user-action-btn delete"
                  onClick={() => handleDeleteUser(user.id)}
                  title="Remove"
                >
                  <BiTrash />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <UserFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveUser}
        initialData={getInitialFormData()}
        title={editingUser ? "Edit User" : "Add User"}
      />
    </div>
  );
}

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

// Check if trip is in the future (not yet completed)
function isFutureTrip(trip: Trip): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const endDate = trip.end_date
    ? new Date(trip.end_date)
    : new Date(trip.start_date);
  return endDate > today;
}

interface YearCalendarViewProps {
  year: number;
  trips: Trip[];
  holidays: Holiday[];
  birthdays: UserBirthday[];
  onDateClick: (date: string, trip?: Trip) => void;
  tccOptions: TCCDestinationOption[];
}

function YearCalendarView({
  year,
  trips,
  holidays,
  birthdays,
  onDateClick,
  tccOptions,
}: YearCalendarViewProps) {
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // Build lookup maps for quick access
  // Holiday map: date -> list of holidays (can have multiple countries)
  const holidayMap = new Map<string, Holiday[]>();
  for (const h of holidays) {
    if (!holidayMap.has(h.date)) holidayMap.set(h.date, []);
    holidayMap.get(h.date)!.push(h);
  }

  // Helper to get country codes for a trip's destinations
  const getTripCountryCodes = (trip: Trip): Set<string> => {
    const codes = new Set<string>();
    for (const dest of trip.destinations) {
      const tcc = tccOptions.find((o) => o.name === dest.name);
      if (tcc?.country_code) codes.add(tcc.country_code);
    }
    return codes;
  };

  // Helper to find holidays matching trip's destination countries
  const getMatchingHolidays = (
    trip: Trip,
    dateHolidays: Holiday[],
  ): Holiday[] => {
    const tripCodes = getTripCountryCodes(trip);
    return dateHolidays.filter(
      (h) => h.country_code && tripCodes.has(h.country_code),
    );
  };

  const birthdayMap = new Map<string, UserBirthday[]>();
  for (const b of birthdays) {
    const key = `${year}-${b.date}`; // YYYY-MM-DD
    if (!birthdayMap.has(key)) birthdayMap.set(key, []);
    birthdayMap.get(key)!.push(b);
  }

  // Format date as YYYY-MM-DD in local time (for trip iteration)
  const toLocalDateStr = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  };

  // Build trip date ranges
  const tripDates = new Map<string, Trip[]>();
  for (const trip of trips) {
    const start = new Date(trip.start_date + "T00:00:00");
    const end = trip.end_date
      ? new Date(trip.end_date + "T00:00:00")
      : new Date(trip.start_date + "T00:00:00");
    const current = new Date(start);
    while (current <= end) {
      const dateStr = toLocalDateStr(current);
      if (!tripDates.has(dateStr)) tripDates.set(dateStr, []);
      tripDates.get(dateStr)!.push(trip);
      current.setDate(current.getDate() + 1);
    }
  }

  const isWeekend = (date: Date) => {
    const day = date.getDay();
    return day === 0 || day === 6;
  };

  const getDaysInMonth = (month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month: number) => {
    // Returns 0-6 (Mon=0 to Sun=6)
    const day = new Date(year, month, 1).getDay();
    return day === 0 ? 6 : day - 1;
  };

  const getTripClass = (trip: Trip) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const endDate = trip.end_date
      ? new Date(trip.end_date)
      : new Date(trip.start_date);
    const isFuture = endDate > today;
    if (isFuture) return "future";
    if (trip.trip_type === "work") return "work";
    return "regular";
  };

  const renderMonth = (month: number) => {
    const daysInMonth = getDaysInMonth(month);
    const firstDay = getFirstDayOfMonth(month);
    const days: JSX.Element[] = [];

    // Empty cells for days before the 1st
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty" />);
    }

    // Today for future date check
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Day cells
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = toLocalDateStr(date);
      const dayTrips = tripDates.get(dateStr) || [];
      const dateHolidays = holidayMap.get(dateStr) || [];
      const dayBirthdays = birthdayMap.get(dateStr);
      const weekend = isWeekend(date);
      const isFutureDate = date >= today;

      // Check if trip overlaps with destination country holiday
      const trip = dayTrips.length > 0 ? dayTrips[0] : null;
      const matchingHolidays = trip
        ? getMatchingHolidays(trip, dateHolidays)
        : [];
      const hasTripOnHoliday = isFutureDate && matchingHolidays.length > 0;

      // Priority: trip > birthday > weekend (no standalone holidays shown)
      const classes = ["calendar-day"];
      let title = "";

      if (trip) {
        classes.push("trip", getTripClass(trip));

        // Check if start/end for border radius
        if (trip.start_date === dateStr) classes.push("trip-start");
        if ((trip.end_date || trip.start_date) === dateStr)
          classes.push("trip-end");

        // Build tooltip with destinations and matching holidays
        const destNames = trip.destinations.map((d) => d.name).join(", ");
        if (hasTripOnHoliday) {
          const holidayNames = matchingHolidays.map((h) => h.name).join(", ");
          title = `${destNames} - ${holidayNames}`;
        } else {
          title = destNames || "Trip";
        }
      } else if (dayBirthdays && dayBirthdays.length > 0) {
        classes.push("birthday");
        title = dayBirthdays.map((b) => `${b.name}'s birthday`).join(", ");
      } else if (weekend) {
        classes.push("weekend");
      }

      days.push(
        <div
          key={day}
          className={classes.join(" ")}
          title={title}
          onClick={() =>
            onDateClick(dateStr, dayTrips.length > 0 ? dayTrips[0] : undefined)
          }
        >
          {day}
          {hasTripOnHoliday && <span className="holiday-badge">!</span>}
        </div>,
      );
    }

    return (
      <div key={month} className="calendar-month">
        <div className="calendar-month-header">{monthNames[month]}</div>
        <div className="calendar-days-header">
          {weekDays.map((d) => (
            <div key={d}>{d}</div>
          ))}
        </div>
        <div className="calendar-days">{days}</div>
      </div>
    );
  };

  return (
    <div className="year-calendar">
      {Array.from({ length: 12 }, (_, i) => renderMonth(i))}
    </div>
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
  const [preselectedDate, setPreselectedDate] = useState<string | null>(null);

  // View mode: table or calendar
  const [viewMode, setViewMode] = useState<"table" | "calendar">(() => {
    const stored = localStorage.getItem("trips-view-mode");
    return stored === "calendar" ? "calendar" : "table";
  });

  // Holidays for calendar view
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  // User birthdays for calendar view
  const [birthdays, setBirthdays] = useState<UserBirthday[]>([]);

  // Persist view mode
  useEffect(() => {
    localStorage.setItem("trips-view-mode", viewMode);
  }, [viewMode]);

  const fetchTrips = useCallback(() => {
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
  }, [selectedYear, onYearChange]);

  useEffect(() => {
    fetchTrips();
    // Fetch TCC options for mapping names to IDs
    fetch("/api/v1/travels/tcc-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
    // Fetch users for birthdays
    fetch("/api/v1/travels/users-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        const users = data.users || [];
        // Also fetch admin users to get all birthdays
        fetch("/api/v1/admin/users/", { credentials: "include" })
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
  }, [fetchTrips]);

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
      fetch(`/api/v1/travels/holidays/${selectedYear}/${code}`, {
        credentials: "include",
      })
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
    setPreselectedDate(null);
    setModalOpen(true);
  };

  const handleEditTrip = (trip: Trip) => {
    setEditingTrip(trip);
    setPreselectedDate(null);
    setModalOpen(true);
  };

  // Handle calendar date click
  const handleCalendarDateClick = (date: string, trip?: Trip) => {
    if (trip) {
      handleEditTrip(trip);
    } else {
      setEditingTrip(null);
      setPreselectedDate(date);
      setModalOpen(true);
    }
  };

  const deleteTripById = async (tripId: number) => {
    const res = await fetch(`/api/v1/travels/trips/${tripId}`, {
      method: "DELETE",
      credentials: "include",
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

  // Convert Trip to TripFormData for editing or preselected date for new trip
  const getInitialFormData = (): TripFormData | null => {
    if (editingTrip) {
      return {
        start_date: editingTrip.start_date,
        end_date: editingTrip.end_date,
        trip_type: editingTrip.trip_type,
        flights_count: editingTrip.flights_count,
        working_days: editingTrip.working_days,
        rental_car: editingTrip.rental_car,
        description: editingTrip.description,
        destinations: editingTrip.destinations
          .map((d) => {
            const tccOpt = tccOptions.find((o) => o.name === d.name);
            return {
              tcc_destination_id: tccOpt?.id || 0,
              is_partial: d.is_partial,
            };
          })
          .filter((d) => d.tcc_destination_id !== 0),
        cities: editingTrip.cities.map((c) => ({
          name: c.name,
          is_partial: c.is_partial,
        })),
        participant_ids: editingTrip.participants.map((p) => p.id),
        other_participants_count: editingTrip.other_participants_count,
      };
    }

    // If preselected date from calendar, return form with that date
    if (preselectedDate) {
      return {
        start_date: preselectedDate,
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
    }

    return null;
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

      {viewMode === "calendar" && selectedYear ? (
        <YearCalendarView
          year={selectedYear}
          trips={filteredTrips}
          holidays={holidays}
          birthdays={birthdays}
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
      )}

      <div className="trips-total">
        Total: {trips.length} trips across {years.length} years
      </div>

      <TripFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrip}
        onDelete={
          editingTrip
            ? async () => {
                await deleteTripById(editingTrip.id);
              }
            : undefined
        }
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
    if (newTab === "trips" && selectedYear) {
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

  // Remove year from URL for close-ones tab
  if (activeTab === "close-ones" && year) {
    return <Navigate to="/admin/close-ones" replace />;
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
          <button
            className={`admin-tab ${activeTab === "close-ones" ? "active" : ""}`}
            onClick={() => setActiveTab("close-ones")}
          >
            Close Ones
          </button>
        </div>

        <div className="admin-content">
          {activeTab === "trips" && (
            <TripsTab
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />
          )}
          {activeTab === "close-ones" && <CloseOnesTab />}
        </div>
      </div>
    </section>
  );
}
