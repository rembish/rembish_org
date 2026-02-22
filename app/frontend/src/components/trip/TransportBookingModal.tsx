import { useEffect, useRef, useState } from "react";
import { BiX } from "react-icons/bi";
import type {
  TransportBookingItem,
  ExtractedTransportBookingData,
} from "./types";
import { TRANSPORT_TYPE_LABELS } from "./helpers";
import { apiFetch } from "../../lib/api";

interface TransportBookingModalProps {
  tripId: string;
  editingBooking: TransportBookingItem | null;
  onChanged: (bookings: TransportBookingItem[]) => void;
  onClose: () => void;
}

export default function TransportBookingModal({
  tripId,
  editingBooking,
  onChanged,
  onClose,
}: TransportBookingModalProps) {
  const [transportForm, setTransportForm] = useState({
    type: "train",
    operator: "",
    service_number: "",
    departure_station: "",
    arrival_station: "",
    departure_datetime: "",
    arrival_datetime: "",
    carriage: "",
    seat: "",
    booking_reference: "",
    notes: "",
  });
  const [addingTransport, setAddingTransport] = useState(false);
  const [extractedTransport, setExtractedTransport] =
    useState<ExtractedTransportBookingData | null>(null);
  const [extractingTransport, setExtractingTransport] = useState(false);
  const [extractTransportError, setExtractTransportError] = useState<
    string | null
  >(null);
  const transportExtractInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (editingBooking) {
      setTransportForm({
        type: editingBooking.type,
        operator: editingBooking.operator || "",
        service_number: editingBooking.service_number || "",
        departure_station: editingBooking.departure_station || "",
        arrival_station: editingBooking.arrival_station || "",
        departure_datetime: editingBooking.departure_datetime || "",
        arrival_datetime: editingBooking.arrival_datetime || "",
        carriage: editingBooking.carriage || "",
        seat: editingBooking.seat || "",
        booking_reference: "",
        notes: editingBooking.notes || "",
      });
    }
  }, [editingBooking]);

  const handleTransportExtractUpload = async (file: File) => {
    setExtractingTransport(true);
    setExtractTransportError(null);
    setExtractedTransport(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/trips/${tripId}/transport-bookings/extract`,
        { method: "POST", body: form },
      );
      const data = await res.json();
      if (data.error) {
        setExtractTransportError(data.error);
        return;
      }
      if (data.booking) {
        setExtractedTransport(data.booking);
      }
    } catch {
      setExtractTransportError("Upload failed. Try again.");
    } finally {
      setExtractingTransport(false);
      if (transportExtractInputRef.current)
        transportExtractInputRef.current.value = "";
    }
  };

  const handleSave = async () => {
    if (!transportForm.type) return;
    setAddingTransport(true);
    try {
      const body = {
        type: transportForm.type,
        operator: transportForm.operator || null,
        service_number: transportForm.service_number || null,
        departure_station: transportForm.departure_station || null,
        arrival_station: transportForm.arrival_station || null,
        departure_datetime: transportForm.departure_datetime || null,
        arrival_datetime: transportForm.arrival_datetime || null,
        carriage: transportForm.carriage || null,
        seat: transportForm.seat || null,
        booking_reference: transportForm.booking_reference || null,
        notes: transportForm.notes || null,
      };
      if (editingBooking) {
        const res = await apiFetch(
          `/api/v1/travels/transport-bookings/${editingBooking.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to update transport booking");
      } else {
        const res = await apiFetch(
          `/api/v1/travels/trips/${tripId}/transport-bookings`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to add transport booking");
      }
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/transport-bookings`,
      );
      const data = await listRes.json();
      onChanged(data.transport_bookings || []);
      onClose();
    } catch (err) {
      console.error("Failed to save transport booking:", err);
    } finally {
      setAddingTransport(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {editingBooking
              ? "Edit Transport Booking"
              : "Add Transport Booking"}
          </h2>
          <button className="modal-close" onClick={onClose}>
            <BiX size={22} />
          </button>
        </div>
        <div className="modal-body" style={{ padding: "1.25rem" }}>
          {!editingBooking && (
            <>
              <div className="flight-extract-section">
                <input
                  ref={transportExtractInputRef}
                  type="file"
                  accept="image/*,.pdf"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleTransportExtractUpload(file);
                  }}
                />
                <button
                  className="btn-extract"
                  onClick={() => transportExtractInputRef.current?.click()}
                  disabled={extractingTransport}
                >
                  {extractingTransport
                    ? "Extracting..."
                    : "Upload booking confirmation"}
                </button>
                {extractTransportError && (
                  <div className="flight-extract-error">
                    {extractTransportError}
                  </div>
                )}
                {extractedTransport && (
                  <div className="flight-extracted-preview">
                    <div className="flight-extracted-leg">
                      <span className="flight-leg-route">
                        <strong>
                          {TRANSPORT_TYPE_LABELS[
                            extractedTransport.type || ""
                          ] || extractedTransport.type}
                        </strong>
                        {extractedTransport.operator &&
                          ` \u2014 ${extractedTransport.operator}`}
                        {extractedTransport.service_number &&
                          ` ${extractedTransport.service_number}`}
                        {extractedTransport.is_duplicate && (
                          <span className="flight-extracted-dup-label">
                            (already exists)
                          </span>
                        )}
                      </span>
                      <span className="flight-leg-details">
                        {[
                          extractedTransport.departure_station,
                          extractedTransport.departure_datetime,
                          extractedTransport.arrival_station,
                        ]
                          .filter(Boolean)
                          .join(" \u00b7 ")}
                      </span>
                    </div>
                    <button
                      className="btn-use-extracted"
                      disabled={
                        extractedTransport.is_duplicate ||
                        !extractedTransport.type
                      }
                      onClick={() => {
                        if (!extractedTransport) return;
                        setTransportForm({
                          type: extractedTransport.type || "train",
                          operator: extractedTransport.operator || "",
                          service_number:
                            extractedTransport.service_number || "",
                          departure_station:
                            extractedTransport.departure_station || "",
                          arrival_station:
                            extractedTransport.arrival_station || "",
                          departure_datetime:
                            extractedTransport.departure_datetime || "",
                          arrival_datetime:
                            extractedTransport.arrival_datetime || "",
                          carriage: extractedTransport.carriage || "",
                          seat: extractedTransport.seat || "",
                          booking_reference:
                            extractedTransport.booking_reference || "",
                          notes: extractedTransport.notes || "",
                        });
                      }}
                    >
                      Use extracted data
                    </button>
                  </div>
                )}
              </div>
              <div className="flight-extract-divider">or enter manually</div>
            </>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Type *</label>
              <select
                value={transportForm.type}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    type: e.target.value,
                  }))
                }
              >
                <option value="train">Train</option>
                <option value="bus">Bus</option>
                <option value="ferry">Ferry</option>
              </select>
            </div>
            <div className="form-group">
              <label>Operator</label>
              <input
                type="text"
                value={transportForm.operator}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    operator: e.target.value,
                  }))
                }
                placeholder="\u010Cesk\u00e9 dr\u00e1hy"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Service Number</label>
            <input
              type="text"
              value={transportForm.service_number}
              onChange={(e) =>
                setTransportForm((prev) => ({
                  ...prev,
                  service_number: e.target.value,
                }))
              }
              placeholder="EC 171"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Departure Station</label>
              <input
                type="text"
                value={transportForm.departure_station}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    departure_station: e.target.value,
                  }))
                }
                placeholder="Praha hlavn\u00ed n\u00e1dra\u017e\u00ed"
              />
            </div>
            <div className="form-group">
              <label>Arrival Station</label>
              <input
                type="text"
                value={transportForm.arrival_station}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    arrival_station: e.target.value,
                  }))
                }
                placeholder="Wien Hauptbahnhof"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Departure</label>
              <input
                type="datetime-local"
                value={
                  transportForm.departure_datetime
                    ? transportForm.departure_datetime.replace(" ", "T")
                    : ""
                }
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    departure_datetime: e.target.value
                      ? e.target.value.replace("T", " ")
                      : "",
                  }))
                }
              />
            </div>
            <div className="form-group">
              <label>Arrival</label>
              <input
                type="datetime-local"
                value={
                  transportForm.arrival_datetime
                    ? transportForm.arrival_datetime.replace(" ", "T")
                    : ""
                }
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    arrival_datetime: e.target.value
                      ? e.target.value.replace("T", " ")
                      : "",
                  }))
                }
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Carriage</label>
              <input
                type="text"
                value={transportForm.carriage}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    carriage: e.target.value,
                  }))
                }
                placeholder="26"
              />
            </div>
            <div className="form-group">
              <label>Seat</label>
              <input
                type="text"
                value={transportForm.seat}
                onChange={(e) =>
                  setTransportForm((prev) => ({
                    ...prev,
                    seat: e.target.value,
                  }))
                }
                placeholder="45"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Booking Reference</label>
            <input
              type="text"
              value={transportForm.booking_reference}
              onChange={(e) =>
                setTransportForm((prev) => ({
                  ...prev,
                  booking_reference: e.target.value,
                }))
              }
              placeholder="ABC123456"
            />
          </div>

          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={transportForm.notes}
              onChange={(e) =>
                setTransportForm((prev) => ({
                  ...prev,
                  notes: e.target.value,
                }))
              }
              placeholder="1st class, window seat"
              rows={2}
            />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn-save"
            onClick={handleSave}
            disabled={addingTransport || !transportForm.type}
          >
            {addingTransport
              ? "Saving..."
              : editingBooking
                ? "Update Booking"
                : "Add Booking"}
          </button>
        </div>
      </div>
    </div>
  );
}
