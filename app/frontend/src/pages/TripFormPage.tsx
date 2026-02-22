import { useEffect, useState } from "react";
import {
  Navigate,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { BiArrowBack } from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import { useViewAs } from "../hooks/useViewAs";
import { apiFetch } from "../lib/api";
import type {
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

export default function TripFormPage() {
  const { user, loading: authLoading } = useAuth();
  const { viewAsUser } = useViewAs();
  const navigate = useNavigate();
  const location = useLocation();
  const { tripId } = useParams();
  const [searchParams] = useSearchParams();

  const isEdit = !!tripId;
  const preselectedDate = searchParams.get("date");

  // Tab from URL: /info, /edit, /transport, or /stays
  const activeTab: TripTab = location.pathname.endsWith("/transport")
    ? "transport"
    : location.pathname.endsWith("/stays")
      ? "stays"
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
