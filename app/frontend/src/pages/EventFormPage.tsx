import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { BiArrowBack, BiTrash } from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";

const EVENT_CATEGORIES: Record<string, string> = {
  medical: "\u{1F3E5}",
  car: "\u{1F697}",
  event: "\u{1F389}",
  admin: "\u{1F4CB}",
  social: "\u{1F465}",
  home: "\u{1F527}",
  pet: "\u{1F431}",
  photo: "\u{1F4F7}",
  boardgames: "\u{1F3B2}",
  other: "\u{1F4CC}",
};

function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

interface EventFormData {
  event_date: string;
  end_date: string | null;
  title: string;
  note: string;
  category: string;
}

export default function EventFormPage() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { eventId } = useParams();
  const isEdit = !!eventId;

  const [formData, setFormData] = useState<EventFormData>({
    event_date: "",
    end_date: null,
    title: "",
    note: "",
    category: "other",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingEvent, setLoadingEvent] = useState(isEdit);

  useEffect(() => {
    if (!isEdit) return;

    fetch(`/api/v1/travels/events/${eventId}`, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Event not found");
        return r.json();
      })
      .then((event) => {
        setFormData({
          event_date: event.event_date,
          end_date: event.end_date,
          title: event.title,
          note: event.note || "",
          category: event.category,
        });
        setLoadingEvent(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingEvent(false);
      });
  }, [isEdit, eventId]);

  const goBack = () => {
    const year = formData.event_date
      ? new Date(formData.event_date).getFullYear()
      : new Date().getFullYear();
    navigate(`/admin/trips/${year}`);
  };

  if (authLoading) return null;
  if (!user?.is_admin) return <Navigate to="/" replace />;

  if (loadingEvent) {
    return (
      <div className="trip-form-page">
        <p>Loading event...</p>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.event_date) {
      setError("Date is required");
      return;
    }
    if (!formData.title.trim()) {
      setError("Title is required");
      return;
    }

    const payload = {
      event_date: formData.event_date,
      end_date: formData.end_date,
      title: formData.title.trim(),
      note: formData.note.trim() || null,
      category: formData.category,
    };

    const url = isEdit
      ? `/api/v1/travels/events/${eventId}`
      : "/api/v1/travels/events";
    const method = isEdit ? "PUT" : "POST";

    setSaving(true);
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save event");
      }
      goBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save event");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!isEdit) return;
    if (!confirm("Are you sure you want to delete this event?")) return;

    try {
      const res = await fetch(`/api/v1/travels/events/${eventId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete event");
      goBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete event");
    }
  };

  return (
    <div className="trip-form-page">
      <div className="trip-form-page-header">
        <button type="button" className="trip-form-back-btn" onClick={goBack}>
          <BiArrowBack />
        </button>
        <h2>{isEdit ? "Edit Event" : "Add Event"}</h2>
      </div>

      <form onSubmit={handleSubmit} className="trip-form">
        {error && <div className="form-error">{error}</div>}

        <div className="form-section">
          <h3>Date</h3>
          <DatePicker
            selectsRange
            startDate={
              formData.event_date ? parseLocalDate(formData.event_date) : null
            }
            endDate={
              formData.end_date ? parseLocalDate(formData.end_date) : null
            }
            onChange={(dates) => {
              const [start, end] = dates as [Date | null, Date | null];
              setFormData((prev) => ({
                ...prev,
                event_date: start ? formatLocalDate(start) : "",
                end_date: end ? formatLocalDate(end) : null,
              }));
            }}
            dateFormat="d MMM yyyy"
            placeholderText="Select date or range"
            className="date-range-input"
            isClearable
            calendarStartDay={1}
            popperPlacement="bottom-start"
          />
        </div>

        <div className="form-section">
          <h3>Title</h3>
          <input
            type="text"
            value={formData.title}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, title: e.target.value }))
            }
            placeholder="e.g., Doctor appointment"
            maxLength={255}
          />
        </div>

        <div className="form-section">
          <h3>Category</h3>
          <div className="category-grid">
            {Object.entries(EVENT_CATEGORIES).map(([key, emoji]) => (
              <button
                key={key}
                type="button"
                className={`category-btn ${formData.category === key ? "selected" : ""}`}
                onClick={() =>
                  setFormData((prev) => ({ ...prev, category: key }))
                }
                title={key}
              >
                <span className="category-emoji">{emoji}</span>
                <span className="category-label">{key}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h3>Note</h3>
          <textarea
            value={formData.note}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, note: e.target.value }))
            }
            placeholder="Optional notes..."
            rows={3}
          />
        </div>

        <div className="modal-actions">
          {isEdit && (
            <button
              type="button"
              className="btn-delete"
              onClick={handleDelete}
              title="Delete event"
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
    </div>
  );
}
