import { useEffect, useState } from "react";
import {
  Navigate,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { BiArrowBack, BiCheck, BiCopy } from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import { useViewAs } from "../hooks/useViewAs";
import { apiFetch } from "../lib/api";
import type {
  AccommodationItem,
  CarRentalItem,
  FlightDataItem,
  TransportBookingItem,
  TripDocumentsTabData,
  TripFormData,
  TripTab,
  TCCDestinationOption,
  UserOption,
} from "../components/trip/types";
import { emptyFormData } from "../components/trip/helpers";
import EditTab from "../components/trip/EditTab";
import InfoTab from "../components/trip/InfoTab";
import TransportTab from "../components/trip/TransportTab";
import StaysTab from "../components/trip/StaysTab";
import DocumentsTab from "../components/trip/DocumentsTab";
import TripDroneFlightsTab from "../components/trip/TripDroneFlightsTab";

function fmtDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default function TripFormPage() {
  const { user, loading: authLoading } = useAuth();
  const { viewAsUser } = useViewAs();
  const navigate = useNavigate();
  const location = useLocation();
  const { tripId } = useParams();
  const [searchParams] = useSearchParams();

  const isEdit = !!tripId;
  const preselectedDate = searchParams.get("date");

  // Tab from URL: /info, /edit, /transport, /stays, /documents, or /drone-flights
  const activeTab: TripTab = location.pathname.endsWith("/transport")
    ? "transport"
    : location.pathname.endsWith("/stays")
      ? "stays"
      : location.pathname.endsWith("/documents")
        ? "documents"
        : location.pathname.endsWith("/drone-flights")
          ? "drone-flights"
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
  const [allEvents, setAllEvents] = useState<
    {
      id: number;
      event_date: string;
      end_date: string | null;
      title: string;
      category_emoji: string;
    }[]
  >([]);
  const [saving, setSaving] = useState(false);
  const [copying, setCopying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingTrip, setLoadingTrip] = useState(isEdit);
  const [tripCitiesDisplay, setTripCitiesDisplay] = useState<
    { name: string; country_code: string | null }[]
  >([]);

  // Load TCC options, user options, and personal events on mount
  useEffect(() => {
    Promise.all([
      apiFetch("/api/v1/travels/tcc-options").then((r) => r.json()),
      apiFetch("/api/v1/travels/users-options").then((r) => r.json()),
      apiFetch("/api/v1/travels/events").then((r) => r.json()),
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

    apiFetch(`/api/v1/travels/trips/${tripId}`)
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

  const copyTrelloText = async () => {
    if (!tripId) return;
    setCopying(true);
    try {
      const [flightsData, staysData, rentalsData, transportData, docsData] =
        await Promise.all([
          apiFetch(`/api/v1/travels/trips/${tripId}/flights`).then((r) =>
            r.json(),
          ),
          apiFetch(`/api/v1/travels/trips/${tripId}/accommodations`).then((r) =>
            r.json(),
          ),
          apiFetch(`/api/v1/travels/trips/${tripId}/car-rentals`).then((r) =>
            r.json(),
          ),
          apiFetch(`/api/v1/travels/trips/${tripId}/transport-bookings`).then(
            (r) => r.json(),
          ),
          apiFetch(`/api/v1/travels/trips/${tripId}/documents-tab`).then((r) =>
            r.json(),
          ),
        ]);

      const flights: FlightDataItem[] = (flightsData.flights || []).sort(
        (a: FlightDataItem, b: FlightDataItem) =>
          a.flight_date.localeCompare(b.flight_date) ||
          (a.departure_time ?? "").localeCompare(b.departure_time ?? ""),
      );
      const stays: AccommodationItem[] = (staysData.accommodations || []).sort(
        (a: AccommodationItem, b: AccommodationItem) =>
          (a.checkin_date ?? "").localeCompare(b.checkin_date ?? ""),
      );
      const rentals: CarRentalItem[] = (rentalsData.car_rentals || []).sort(
        (a: CarRentalItem, b: CarRentalItem) =>
          (a.pickup_datetime ?? "").localeCompare(b.pickup_datetime ?? ""),
      );
      const transports: TransportBookingItem[] = (
        transportData.transport_bookings || []
      ).sort((a: TransportBookingItem, b: TransportBookingItem) =>
        (a.departure_datetime ?? "").localeCompare(b.departure_datetime ?? ""),
      );
      const docs: TripDocumentsTabData = docsData;

      const lines: string[] = [];

      const destNames = formData.destinations
        .map((d) => tccOptions.find((o) => o.id === d.tcc_destination_id)?.name)
        .filter(Boolean)
        .join(", ");
      if (destNames) lines.push(destNames);

      const cityNames = formData.cities.map((c) => c.name).join(", ");
      if (cityNames) lines.push(`Cities: ${cityNames}`);

      const startFmt = fmtDate(formData.start_date);
      const endFmt = formData.end_date ? fmtDate(formData.end_date) : "?";
      lines.push(`${startFmt} → ${endFmt}`);

      if (flights.length > 0) {
        lines.push("");
        lines.push(`FLIGHTS (${flights.length})`);
        for (const f of flights) {
          const dep = f.departure_airport.iata_code;
          const arr = f.arrival_airport.iata_code;
          const depTime = f.departure_time?.slice(0, 5);
          const arrTime = f.arrival_time?.slice(0, 5);
          const times =
            depTime && arrTime
              ? `  ${depTime}–${arrTime}`
              : depTime
                ? `  ${depTime}`
                : "";
          const airline = f.airline_name ? ` ${f.airline_name}` : "";
          let line = `• ${fmtDate(f.flight_date)}  ${f.flight_number}${airline}  ${dep} → ${arr}${times}`;
          const extras: string[] = [];
          if (f.seat) extras.push(`Seat: ${f.seat}`);
          if (f.booking_reference) extras.push(`PNR: ${f.booking_reference}`);
          if (extras.length) line += `  [${extras.join(" | ")}]`;
          lines.push(line);
        }
      }

      if (stays.length > 0) {
        lines.push("");
        lines.push(`STAYS (${stays.length})`);
        for (const s of stays) {
          const checkin = s.checkin_date ? fmtDate(s.checkin_date) : "?";
          const checkout = s.checkout_date ? fmtDate(s.checkout_date) : "?";
          const platform = s.platform ? ` (${s.platform})` : "";
          let line = `• ${checkin}–${checkout}  ${s.property_name}${platform}`;
          if (s.confirmation_code) line += `  [Conf: ${s.confirmation_code}]`;
          lines.push(line);
          if (s.address) lines.push(`  ${s.address}`);
        }
      }

      if (rentals.length > 0) {
        lines.push("");
        lines.push(`CAR RENTAL (${rentals.length})`);
        for (const r of rentals) {
          const pickup = r.pickup_datetime
            ? fmtDate(r.pickup_datetime.slice(0, 10))
            : "?";
          const dropoff = r.dropoff_datetime
            ? fmtDate(r.dropoff_datetime.slice(0, 10))
            : "?";
          const car =
            [r.car_class, r.actual_car].filter(Boolean).join(" / ") || "?";
          const trans = r.transmission ? ` (${r.transmission})` : "";
          let line = `• ${pickup}–${dropoff}  ${r.rental_company} — ${car}${trans}`;
          if (r.confirmation_number)
            line += `  [Conf: ${r.confirmation_number}]`;
          lines.push(line);
          if (r.pickup_location) lines.push(`  Pickup: ${r.pickup_location}`);
          if (r.dropoff_location && r.dropoff_location !== r.pickup_location)
            lines.push(`  Dropoff: ${r.dropoff_location}`);
        }
      }

      if (transports.length > 0) {
        lines.push("");
        lines.push(`TRANSPORT (${transports.length})`);
        for (const t of transports) {
          const date = t.departure_datetime
            ? fmtDate(t.departure_datetime.slice(0, 10))
            : "?";
          const depTime = t.departure_datetime?.slice(11, 16);
          const arrTime = t.arrival_datetime?.slice(11, 16);
          const times =
            depTime && arrTime
              ? `  ${depTime}–${arrTime}`
              : depTime
                ? `  ${depTime}`
                : "";
          const type =
            t.type.charAt(0).toUpperCase() + t.type.slice(1).toLowerCase();
          const service = [t.operator, t.service_number]
            .filter(Boolean)
            .join(" ");
          const route = [t.departure_station, t.arrival_station]
            .filter(Boolean)
            .join(" → ");
          let line = `• ${date}  ${type}${service ? ` ${service}` : ""}  ${route}${times}`;
          const seatParts: string[] = [];
          if (t.carriage) seatParts.push(`Car ${t.carriage}`);
          if (t.seat) seatParts.push(`Seat ${t.seat}`);
          if (t.booking_reference)
            seatParts.push(`Ref: ${t.booking_reference}`);
          if (seatParts.length) line += `  [${seatParts.join(" | ")}]`;
          lines.push(line);
        }
      }

      if (docs.travel_docs?.length > 0) {
        lines.push("");
        lines.push("VISA / TRAVEL DOCS");
        for (const v of docs.travel_docs) {
          const status = v.has_files ? "issued" : "not yet issued";
          const passport = v.passport_label ? ` [${v.passport_label}]` : "";
          const entry = v.entry_type ? ` (${v.entry_type})` : "";
          lines.push(`• ${v.label}${entry}: ${status}${passport}`);
        }
      }

      await navigator.clipboard.writeText(lines.join("\n"));
      setTimeout(() => setCopying(false), 2000);
    } catch {
      setCopying(false);
    }
  };

  const goBack = () => {
    const year = formData.start_date
      ? new Date(formData.start_date).getFullYear()
      : new Date().getFullYear();
    navigate(`/admin/trips/${year}`);
  };

  const readOnly = user?.role === "viewer" || !!viewAsUser;

  // Auth guard
  if (authLoading) return null;
  if (!user?.role) return <Navigate to="/" replace />;

  // Viewers cannot create new trips or access the edit tab
  if (readOnly && !isEdit) return <Navigate to="/admin/trips" replace />;
  if (readOnly && activeTab === "edit")
    return <Navigate to={`/admin/trips/${tripId}/info`} replace />;

  if (loadingTrip) {
    return (
      <div className="trip-form-page">
        <p>Loading trip...</p>
      </div>
    );
  }

  const handleSave = async () => {
    setError(null);
    if (!formData.start_date) {
      setError("Start date is required");
      return;
    }

    const tripType =
      formData.working_days && formData.working_days > 0 ? "work" : "regular";
    const dataToSave: TripFormData = { ...formData, trip_type: tripType };
    const url = isEdit
      ? `/api/v1/travels/trips/${tripId}`
      : "/api/v1/travels/trips";
    const method = isEdit ? "PUT" : "POST";

    setSaving(true);
    try {
      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
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
      const res = await apiFetch(`/api/v1/travels/trips/${tripId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete trip");
      goBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete trip");
    }
  };

  return (
    <div className="trip-form-page">
      <div className="trip-form-page-header">
        <button type="button" className="trip-form-back-btn" onClick={goBack}>
          <BiArrowBack />
        </button>
        <h2>{isEdit ? "Edit Trip" : "Add Trip"}</h2>
        {isEdit && (
          <button
            type="button"
            className="trip-copy-trello-btn"
            onClick={copyTrelloText}
            disabled={copying}
            title="Copy trip summary for Trello"
          >
            {copying ? <BiCheck /> : <BiCopy />}
            {copying ? "Copied!" : "Trello"}
          </button>
        )}
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
          {!readOnly && (
            <button
              className={`trip-form-tab ${activeTab === "edit" ? "active" : ""}`}
              onClick={() =>
                navigate(`/admin/trips/${tripId}/edit`, { replace: true })
              }
            >
              Edit
            </button>
          )}
          <button
            className={`trip-form-tab ${activeTab === "transport" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/transport`, { replace: true })
            }
          >
            Transport
          </button>
          <button
            className={`trip-form-tab ${activeTab === "stays" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/stays`, { replace: true })
            }
          >
            Stays
          </button>
          <button
            className={`trip-form-tab ${activeTab === "documents" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/documents`, { replace: true })
            }
          >
            Docs
          </button>
          <button
            className={`trip-form-tab ${activeTab === "drone-flights" ? "active" : ""}`}
            onClick={() =>
              navigate(`/admin/trips/${tripId}/drone-flights`, {
                replace: true,
              })
            }
          >
            Drone Flights
          </button>
        </div>
      )}

      {activeTab === "transport" && isEdit ? (
        <TransportTab
          tripId={tripId!}
          formData={formData}
          tccOptions={tccOptions}
          tripCitiesDisplay={tripCitiesDisplay}
          readOnly={readOnly}
          onFlightsCountChange={(count) =>
            setFormData((prev) => ({ ...prev, flights_count: count }))
          }
        />
      ) : activeTab === "stays" && isEdit ? (
        <StaysTab
          tripId={tripId!}
          formData={formData}
          tccOptions={tccOptions}
          readOnly={readOnly}
        />
      ) : activeTab === "documents" && isEdit ? (
        <DocumentsTab tripId={tripId!} readOnly={readOnly} />
      ) : activeTab === "drone-flights" && isEdit ? (
        <TripDroneFlightsTab tripId={tripId!} readOnly={readOnly} />
      ) : activeTab === "info" && isEdit ? (
        <InfoTab tripId={tripId!} readOnly={readOnly} />
      ) : (
        <EditTab
          formData={formData}
          setFormData={setFormData}
          tccOptions={tccOptions}
          userOptions={userOptions}
          allEvents={allEvents}
          isEdit={isEdit}
          onSave={handleSave}
          onDelete={handleDelete}
          onCancel={goBack}
          saving={saving}
          error={error}
        />
      )}
    </div>
  );
}
