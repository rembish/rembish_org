import { BiCake, BiPaperPlane, BiParty } from "react-icons/bi";
import type {
  Trip,
  Holiday,
  UserBirthday,
  PersonalEvent,
  TCCDestinationOption,
} from "./types";
import { countryFlag } from "./tripHelpers";

interface YearCalendarViewProps {
  year: number;
  trips: Trip[];
  holidays: Holiday[];
  czechHolidays: Holiday[];
  birthdays: UserBirthday[];
  events: PersonalEvent[];
  flightDates: Map<string, string[]>;
  onDateClick: (date: string, trip?: Trip, event?: PersonalEvent) => void;
  tccOptions: TCCDestinationOption[];
}

export default function YearCalendarView({
  year,
  trips,
  holidays,
  czechHolidays,
  birthdays,
  events,
  flightDates,
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

  // Czech holiday map: date -> holiday name (for background coloring)
  const czechHolidayMap = new Map<string, string>();
  for (const h of czechHolidays) {
    czechHolidayMap.set(h.date, h.local_name || h.name);
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

  // Build event dates map (supports multi-day events)
  const eventDates = new Map<string, PersonalEvent>();
  for (const event of events) {
    const start = new Date(event.event_date + "T00:00:00");
    const end = event.end_date
      ? new Date(event.end_date + "T00:00:00")
      : new Date(event.event_date + "T00:00:00");
    const current = new Date(start);
    while (current <= end) {
      eventDates.set(toLocalDateStr(current), event);
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

    // Today for future trip check
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Day cells
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = toLocalDateStr(date);
      const dayTrips = tripDates.get(dateStr) || [];
      const dateHolidays = holidayMap.get(dateStr) || [];
      const dayBirthdays = birthdayMap.get(dateStr);
      const czechHoliday = czechHolidayMap.get(dateStr);
      const dayEvent = eventDates.get(dateStr);
      const weekend = isWeekend(date);

      // Check if trip overlaps with destination country holiday (only for future trips)
      const trip = dayTrips.length > 0 ? dayTrips[0] : null;
      const isFuture =
        trip &&
        (trip.end_date ? new Date(trip.end_date) : new Date(trip.start_date)) >
          today;
      const matchingHolidays = trip
        ? getMatchingHolidays(trip, dateHolidays)
        : [];
      const hasTripOnHoliday = isFuture && matchingHolidays.length > 0;

      // Check if trip overlaps with a birthday (for all trips, not just future)
      const hasTripOnBirthday = trip && dayBirthdays && dayBirthdays.length > 0;

      // Check if trip overlaps with a personal event
      const hasTripOnEvent = trip && dayEvent;

      // Priority: trip > event > birthday > czech-holiday > weekend
      const classes = ["calendar-day"];
      let title = "";

      if (trip) {
        classes.push("trip", getTripClass(trip));
        if (hasTripOnEvent) classes.push("has-event");

        // Check if start/end for border radius
        const isStart = trip.start_date === dateStr;
        const isEnd = (trip.end_date || trip.start_date) === dateStr;
        if (isStart) classes.push("trip-start");
        if (isEnd) classes.push("trip-end");

        // Half-cell visualization for departure/arrival types
        if (isStart) {
          if (trip.departure_type === "midday") classes.push("vac-half-start");
          else if (trip.departure_type === "evening")
            classes.push("vac-light-start");
        }
        if (isEnd) {
          if (trip.arrival_type === "midday") classes.push("vac-half-end");
          else if (trip.arrival_type === "morning")
            classes.push("vac-light-end");
        }

        // Build tooltip with destinations, holidays, birthdays, and events
        const destNames = trip.destinations.map((d) => d.name).join(", ");
        const parts = [destNames || "Trip"];
        if (hasTripOnEvent) {
          parts.push(`${dayEvent!.category_emoji} ${dayEvent!.title}`);
        }
        if (hasTripOnHoliday) {
          parts.push(matchingHolidays.map((h) => h.name).join(", "));
        }
        if (hasTripOnBirthday) {
          parts.push(
            dayBirthdays!.map((b) => `${b.name}'s birthday`).join(", "),
          );
        }
        title = parts.join(" - ");
      } else if (dayEvent) {
        classes.push("event");
        const isEventStart = dayEvent.event_date === dateStr;
        const isEventEnd =
          (dayEvent.end_date || dayEvent.event_date) === dateStr;
        if (isEventStart) classes.push("event-start");
        if (isEventEnd) classes.push("event-end");
        title = `${dayEvent.category_emoji} ${dayEvent.title}`;
      } else if (dayBirthdays && dayBirthdays.length > 0) {
        classes.push("birthday");
        title = dayBirthdays.map((b) => `${b.name}'s birthday`).join(", ");
      } else if (czechHoliday) {
        classes.push("czech-holiday");
        title = czechHoliday;
      } else if (weekend) {
        classes.push("weekend");
      }

      const foreignCountries =
        trip && flightDates.has(dateStr)
          ? flightDates.get(dateStr)!.filter((cc) => cc !== "CZ")
          : null;

      days.push(
        <div
          key={day}
          className={classes.join(" ")}
          title={title}
          onClick={() =>
            onDateClick(
              dateStr,
              dayTrips.length > 0 ? dayTrips[0] : undefined,
              dayEvent,
            )
          }
        >
          {day}
          {dayEvent && (
            <span className="event-emoji">{dayEvent.category_emoji}</span>
          )}
          {hasTripOnBirthday && <BiCake className="day-icon day-icon-left" />}
          {hasTripOnHoliday && <BiParty className="day-icon day-icon-right" />}
          {foreignCountries && foreignCountries.length > 0 ? (
            <span className="day-icon day-icon-bottom">
              {foreignCountries.map((cc) => countryFlag(cc)).join("")}
            </span>
          ) : trip && flightDates.has(dateStr) ? (
            <BiPaperPlane className="day-icon day-icon-bottom" />
          ) : null}
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
