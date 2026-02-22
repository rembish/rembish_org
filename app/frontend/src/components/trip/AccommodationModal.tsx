import { useEffect, useRef, useState } from "react";
import { BiX } from "react-icons/bi";
import type { AccommodationItem, ExtractedAccommodationData } from "./types";
import { PLATFORM_LABELS } from "./helpers";
import { apiFetch } from "../../lib/api";

interface AccommodationModalProps {
  tripId: string;
  editingAccommodation: AccommodationItem | null;
  onChanged: (accommodations: AccommodationItem[]) => void;
  onClose: () => void;
}

const emptyForm = {
  property_name: "",
  platform: "",
  checkin_date: "",
  checkout_date: "",
  address: "",
  total_amount: "",
  payment_status: "",
  payment_date: "",
  guests: "",
  rooms: "",
  confirmation_code: "",
  booking_url: "",
  notes: "",
};

export default function AccommodationModal({
  tripId,
  editingAccommodation,
  onChanged,
  onClose,
}: AccommodationModalProps) {
  const [accommodationForm, setAccommodationForm] = useState({ ...emptyForm });
  const [addingAccommodation, setAddingAccommodation] = useState(false);
  const [extractedAccommodation, setExtractedAccommodation] =
    useState<ExtractedAccommodationData | null>(null);
  const [extractingAccommodation, setExtractingAccommodation] = useState(false);
  const [extractAccommodationError, setExtractAccommodationError] = useState<
    string | null
  >(null);
  const accommodationExtractInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingAccommodation) {
      setAccommodationForm({
        property_name: editingAccommodation.property_name,
        platform: editingAccommodation.platform || "",
        checkin_date: editingAccommodation.checkin_date || "",
        checkout_date: editingAccommodation.checkout_date || "",
        address: editingAccommodation.address || "",
        total_amount: editingAccommodation.total_amount || "",
        payment_status: editingAccommodation.payment_status || "",
        payment_date: editingAccommodation.payment_date || "",
        guests: editingAccommodation.guests?.toString() || "",
        rooms: editingAccommodation.rooms?.toString() || "",
        confirmation_code: "",
        booking_url: editingAccommodation.booking_url || "",
        notes: editingAccommodation.notes || "",
      });
    }
  }, [editingAccommodation]);

  const handleAccommodationExtractUpload = async (file: File) => {
    setExtractingAccommodation(true);
    setExtractAccommodationError(null);
    setExtractedAccommodation(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/trips/${tripId}/accommodations/extract`,
        { method: "POST", body: form },
      );
      const data = await res.json();
      if (data.error) {
        setExtractAccommodationError(data.error);
        return;
      }
      if (data.accommodation) {
        setExtractedAccommodation(data.accommodation);
      }
    } catch {
      setExtractAccommodationError("Upload failed. Try again.");
    } finally {
      setExtractingAccommodation(false);
      if (accommodationExtractInputRef.current)
        accommodationExtractInputRef.current.value = "";
    }
  };

  const handleSave = async () => {
    if (!accommodationForm.property_name) return;
    setAddingAccommodation(true);
    try {
      const body = {
        property_name: accommodationForm.property_name,
        platform: accommodationForm.platform || null,
        checkin_date: accommodationForm.checkin_date || null,
        checkout_date: accommodationForm.checkout_date || null,
        address: accommodationForm.address || null,
        total_amount: accommodationForm.total_amount || null,
        payment_status: accommodationForm.payment_status || null,
        payment_date: accommodationForm.payment_date || null,
        guests: accommodationForm.guests
          ? parseInt(accommodationForm.guests)
          : null,
        rooms: accommodationForm.rooms
          ? parseInt(accommodationForm.rooms)
          : null,
        confirmation_code: accommodationForm.confirmation_code || null,
        booking_url: accommodationForm.booking_url || null,
        notes: accommodationForm.notes || null,
      };
      if (editingAccommodation) {
        const res = await apiFetch(
          `/api/v1/travels/accommodations/${editingAccommodation.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to update accommodation");
      } else {
        const res = await apiFetch(
          `/api/v1/travels/trips/${tripId}/accommodations`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to add accommodation");
      }
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/accommodations`,
      );
      const data = await listRes.json();
      onChanged(data.accommodations || []);
      onClose();
    } catch (err) {
      console.error("Failed to save accommodation:", err);
    } finally {
      setAddingAccommodation(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {editingAccommodation ? "Edit Accommodation" : "Add Accommodation"}
          </h2>
          <button className="btn-icon" onClick={onClose}>
            <BiX size={20} />
          </button>
        </div>
        <div style={{ padding: "1.25rem" }}>
          {/* Extraction section (add mode only) */}
          {!editingAccommodation && (
            <>
              <div className="flight-extract-row">
                <label className="btn-save flight-extract-btn">
                  {extractingAccommodation
                    ? "Extracting..."
                    : "Upload booking PDF"}
                  <input
                    ref={accommodationExtractInputRef}
                    type="file"
                    accept=".pdf,image/*"
                    style={{ display: "none" }}
                    disabled={extractingAccommodation}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleAccommodationExtractUpload(file);
                    }}
                  />
                </label>
                <span className="flight-extract-hint">
                  PDF or photo — AI extracts booking details
                </span>
              </div>

              {extractAccommodationError && (
                <p className="flight-lookup-error">
                  {extractAccommodationError}
                </p>
              )}

              {extractedAccommodation && (
                <div className="flight-lookup-results">
                  <div
                    className={`flight-lookup-leg${extractedAccommodation.is_duplicate ? " flight-extracted-duplicate" : ""}`}
                  >
                    <div className="flight-leg-info">
                      <span className="flight-leg-route">
                        <strong>{extractedAccommodation.property_name}</strong>
                        {extractedAccommodation.platform &&
                          ` — ${PLATFORM_LABELS[extractedAccommodation.platform] || extractedAccommodation.platform}`}
                        {extractedAccommodation.is_duplicate && (
                          <span className="flight-extracted-dup-label">
                            (already exists)
                          </span>
                        )}
                      </span>
                      <span className="flight-leg-details">
                        {[
                          extractedAccommodation.checkin_date,
                          extractedAccommodation.checkout_date
                            ? `– ${extractedAccommodation.checkout_date}`
                            : null,
                          extractedAccommodation.address,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn-save"
                    onClick={() => {
                      setAccommodationForm({
                        property_name:
                          extractedAccommodation.property_name || "",
                        platform: extractedAccommodation.platform || "",
                        checkin_date: extractedAccommodation.checkin_date || "",
                        checkout_date:
                          extractedAccommodation.checkout_date || "",
                        address: extractedAccommodation.address || "",
                        total_amount: extractedAccommodation.total_amount || "",
                        payment_status:
                          extractedAccommodation.payment_status || "",
                        payment_date: extractedAccommodation.payment_date || "",
                        guests: extractedAccommodation.guests?.toString() || "",
                        rooms: extractedAccommodation.rooms?.toString() || "",
                        confirmation_code:
                          extractedAccommodation.confirmation_code || "",
                        booking_url: "",
                        notes: extractedAccommodation.notes || "",
                      });
                    }}
                    disabled={
                      extractedAccommodation.is_duplicate ||
                      !extractedAccommodation.property_name
                    }
                  >
                    Use extracted data
                  </button>
                </div>
              )}

              <div className="modal-section-divider">or enter manually</div>
            </>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Property Name *</label>
              <input
                type="text"
                value={accommodationForm.property_name}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    property_name: e.target.value,
                  }))
                }
                placeholder="Hotel Marrakech"
              />
            </div>
            <div className="form-group">
              <label>Platform</label>
              <select
                value={accommodationForm.platform}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    platform: e.target.value,
                  }))
                }
              >
                <option value="">—</option>
                <option value="booking">Booking.com</option>
                <option value="agoda">Agoda</option>
                <option value="airbnb">Airbnb</option>
                <option value="direct">Direct</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Check-in</label>
              <input
                type="date"
                value={accommodationForm.checkin_date}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    checkin_date: e.target.value,
                  }))
                }
              />
            </div>
            <div className="form-group">
              <label>Check-out</label>
              <input
                type="date"
                value={accommodationForm.checkout_date}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    checkout_date: e.target.value,
                  }))
                }
              />
            </div>
          </div>
          <div className="form-group">
            <label>Address</label>
            <input
              type="text"
              value={accommodationForm.address}
              onChange={(e) =>
                setAccommodationForm((prev) => ({
                  ...prev,
                  address: e.target.value,
                }))
              }
              placeholder="123 Main Street, City"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Total Amount</label>
              <input
                type="text"
                value={accommodationForm.total_amount}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    total_amount: e.target.value,
                  }))
                }
                placeholder="€245.00"
              />
            </div>
            <div className="form-group">
              <label>Payment Status</label>
              <select
                value={accommodationForm.payment_status}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    payment_status: e.target.value,
                  }))
                }
              >
                <option value="">—</option>
                <option value="paid">Paid</option>
                <option value="pay_at_property">Pay at property</option>
                <option value="pay_by_date">Pay by date</option>
              </select>
            </div>
          </div>
          {accommodationForm.payment_status === "pay_by_date" && (
            <div className="form-group">
              <label>Payment Deadline</label>
              <input
                type="date"
                value={accommodationForm.payment_date}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    payment_date: e.target.value,
                  }))
                }
              />
            </div>
          )}
          <div className="form-row">
            <div className="form-group">
              <label>Guests</label>
              <input
                type="number"
                min="1"
                value={accommodationForm.guests}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    guests: e.target.value,
                  }))
                }
                placeholder="2"
              />
            </div>
            <div className="form-group">
              <label>Rooms</label>
              <input
                type="number"
                min="1"
                value={accommodationForm.rooms}
                onChange={(e) =>
                  setAccommodationForm((prev) => ({
                    ...prev,
                    rooms: e.target.value,
                  }))
                }
                placeholder="1"
              />
            </div>
          </div>
          <div className="form-group">
            <label>Confirmation Code</label>
            <input
              type="text"
              value={accommodationForm.confirmation_code}
              onChange={(e) =>
                setAccommodationForm((prev) => ({
                  ...prev,
                  confirmation_code: e.target.value,
                }))
              }
              placeholder="123456789"
            />
          </div>
          <div className="form-group">
            <label>Booking URL</label>
            <input
              type="text"
              value={accommodationForm.booking_url}
              onChange={(e) =>
                setAccommodationForm((prev) => ({
                  ...prev,
                  booking_url: e.target.value,
                }))
              }
              placeholder="https://www.booking.com/..."
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={accommodationForm.notes}
              onChange={(e) =>
                setAccommodationForm((prev) => ({
                  ...prev,
                  notes: e.target.value,
                }))
              }
              placeholder="Room type, breakfast, cancellation policy..."
              rows={2}
            />
          </div>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-save"
            onClick={handleSave}
            disabled={addingAccommodation || !accommodationForm.property_name}
          >
            {addingAccommodation
              ? "Saving..."
              : editingAccommodation
                ? "Update Accommodation"
                : "Add Accommodation"}
          </button>
        </div>
      </div>
    </div>
  );
}
