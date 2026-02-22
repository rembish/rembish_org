import { useEffect, useRef, useState } from "react";
import { BiX } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type { CarRentalItem, ExtractedCarRentalData } from "./types";

interface CarRentalModalProps {
  tripId: string;
  editingRental: CarRentalItem | null;
  onChanged: (rentals: CarRentalItem[]) => void;
  onClose: () => void;
}

export default function CarRentalModal({
  tripId,
  editingRental,
  onChanged,
  onClose,
}: CarRentalModalProps) {
  const [manualRentalForm, setManualRentalForm] = useState({
    rental_company: "",
    car_class: "",
    actual_car: "",
    transmission: "",
    pickup_location: "",
    dropoff_location: "",
    pickup_datetime: "",
    dropoff_datetime: "",
    is_paid: false as boolean,
    total_amount: "",
    confirmation_number: "",
    notes: "",
  });
  const [addingRental, setAddingRental] = useState(false);
  const [extractedRental, setExtractedRental] =
    useState<ExtractedCarRentalData | null>(null);
  const [extractingRental, setExtractingRental] = useState(false);
  const [extractRentalError, setExtractRentalError] = useState<string | null>(
    null,
  );
  const rentalExtractInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingRental) {
      setManualRentalForm({
        rental_company: editingRental.rental_company,
        car_class: editingRental.car_class || "",
        actual_car: editingRental.actual_car || "",
        transmission: editingRental.transmission || "",
        pickup_location: editingRental.pickup_location || "",
        dropoff_location: editingRental.dropoff_location || "",
        pickup_datetime: editingRental.pickup_datetime || "",
        dropoff_datetime: editingRental.dropoff_datetime || "",
        is_paid: editingRental.is_paid || false,
        total_amount: editingRental.total_amount || "",
        confirmation_number: "",
        notes: editingRental.notes || "",
      });
    }
  }, [editingRental]);

  const handleRentalExtractUpload = async (file: File) => {
    setExtractingRental(true);
    setExtractRentalError(null);
    setExtractedRental(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/trips/${tripId}/car-rentals/extract`,
        { method: "POST", body: form },
      );
      const data = await res.json();
      if (data.error) {
        setExtractRentalError(data.error);
        return;
      }
      if (data.rental) {
        setExtractedRental(data.rental);
      }
    } catch {
      setExtractRentalError("Upload failed. Try again.");
    } finally {
      setExtractingRental(false);
      if (rentalExtractInputRef.current)
        rentalExtractInputRef.current.value = "";
    }
  };

  const handleSave = async () => {
    if (!manualRentalForm.rental_company) return;
    setAddingRental(true);
    try {
      const body = {
        rental_company: manualRentalForm.rental_company,
        car_class: manualRentalForm.car_class || null,
        actual_car: manualRentalForm.actual_car || null,
        transmission: manualRentalForm.transmission || null,
        pickup_location: manualRentalForm.pickup_location || null,
        dropoff_location: manualRentalForm.dropoff_location || null,
        pickup_datetime: manualRentalForm.pickup_datetime || null,
        dropoff_datetime: manualRentalForm.dropoff_datetime || null,
        is_paid: manualRentalForm.is_paid,
        total_amount: manualRentalForm.total_amount || null,
        confirmation_number: manualRentalForm.confirmation_number || null,
        notes: manualRentalForm.notes || null,
      };

      if (editingRental) {
        const res = await apiFetch(
          `/api/v1/travels/car-rentals/${editingRental.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to update rental");
      } else {
        const res = await apiFetch(
          `/api/v1/travels/trips/${tripId}/car-rentals`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) throw new Error("Failed to add rental");
      }
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/car-rentals`,
      );
      const data = await listRes.json();
      onChanged(data.car_rentals || []);
      onClose();
    } catch (err) {
      console.error("Failed to save rental:", err);
    } finally {
      setAddingRental(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{editingRental ? "Edit Car Rental" : "Add Car Rental"}</h2>
          <button className="btn-icon" onClick={onClose}>
            <BiX size={20} />
          </button>
        </div>
        <div style={{ padding: "1.25rem" }}>
          {/* Extraction section (add mode only) */}
          {!editingRental && (
            <>
              <div className="flight-extract-row">
                <label className="btn-save flight-extract-btn">
                  {extractingRental
                    ? "Extracting..."
                    : "Upload reservation PDF"}
                  <input
                    ref={rentalExtractInputRef}
                    type="file"
                    accept=".pdf,image/*"
                    style={{ display: "none" }}
                    disabled={extractingRental}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleRentalExtractUpload(file);
                    }}
                  />
                </label>
                <span className="flight-extract-hint">
                  PDF or photo — AI extracts rental details
                </span>
              </div>

              {extractRentalError && (
                <p className="flight-lookup-error">{extractRentalError}</p>
              )}

              {extractedRental && (
                <div className="flight-lookup-results">
                  <div
                    className={`flight-lookup-leg${extractedRental.is_duplicate ? " flight-extracted-duplicate" : ""}`}
                  >
                    <div className="flight-leg-info">
                      <span className="flight-leg-route">
                        <strong>{extractedRental.rental_company}</strong>
                        {extractedRental.car_class &&
                          ` — ${extractedRental.car_class}`}
                        {extractedRental.is_duplicate && (
                          <span className="flight-extracted-dup-label">
                            (already exists)
                          </span>
                        )}
                      </span>
                      <span className="flight-leg-details">
                        {[
                          extractedRental.pickup_location,
                          extractedRental.pickup_datetime,
                          extractedRental.transmission,
                          extractedRental.total_amount,
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
                      setManualRentalForm({
                        rental_company: extractedRental.rental_company || "",
                        car_class: extractedRental.car_class || "",
                        actual_car: "",
                        transmission: extractedRental.transmission || "",
                        pickup_location: extractedRental.pickup_location || "",
                        dropoff_location:
                          extractedRental.dropoff_location || "",
                        pickup_datetime: extractedRental.pickup_datetime || "",
                        dropoff_datetime:
                          extractedRental.dropoff_datetime || "",
                        is_paid: extractedRental.is_paid || false,
                        total_amount: extractedRental.total_amount || "",
                        confirmation_number:
                          extractedRental.confirmation_number || "",
                        notes: extractedRental.notes || "",
                      });
                    }}
                    disabled={
                      extractedRental.is_duplicate ||
                      !extractedRental.rental_company
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
              <label>Rental Company *</label>
              <input
                type="text"
                value={manualRentalForm.rental_company}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    rental_company: e.target.value,
                  }))
                }
                placeholder="Hertz"
              />
            </div>
            <div className="form-group">
              <label>Car Class</label>
              <input
                type="text"
                value={manualRentalForm.car_class}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    car_class: e.target.value,
                  }))
                }
                placeholder="Compact SUV"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Actual Car</label>
              <input
                type="text"
                value={manualRentalForm.actual_car}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    actual_car: e.target.value,
                  }))
                }
                placeholder="Toyota Corolla"
              />
            </div>
            <div className="form-group">
              <label>Transmission</label>
              <select
                value={manualRentalForm.transmission}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    transmission: e.target.value,
                  }))
                }
              >
                <option value="">—</option>
                <option value="automatic">Automatic</option>
                <option value="manual">Manual</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Pickup Location</label>
              <input
                type="text"
                value={manualRentalForm.pickup_location}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    pickup_location: e.target.value,
                  }))
                }
                placeholder="Keflavik Airport"
              />
            </div>
            <div className="form-group">
              <label>Dropoff Location</label>
              <input
                type="text"
                value={manualRentalForm.dropoff_location}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    dropoff_location: e.target.value,
                  }))
                }
                placeholder="Keflavik Airport"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Pickup Date/Time</label>
              <input
                type="datetime-local"
                value={manualRentalForm.pickup_datetime}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    pickup_datetime: e.target.value
                      ? e.target.value.replace("T", " ")
                      : "",
                  }))
                }
              />
            </div>
            <div className="form-group">
              <label>Dropoff Date/Time</label>
              <input
                type="datetime-local"
                value={manualRentalForm.dropoff_datetime}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    dropoff_datetime: e.target.value
                      ? e.target.value.replace("T", " ")
                      : "",
                  }))
                }
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Total Amount</label>
              <input
                type="text"
                value={manualRentalForm.total_amount}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    total_amount: e.target.value,
                  }))
                }
                placeholder="€245.00"
              />
            </div>
            <div className="form-group">
              <label>Confirmation #</label>
              <input
                type="text"
                value={manualRentalForm.confirmation_number}
                onChange={(e) =>
                  setManualRentalForm((prev) => ({
                    ...prev,
                    confirmation_number: e.target.value,
                  }))
                }
                placeholder="L2912369773"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={manualRentalForm.is_paid}
                  onChange={(e) =>
                    setManualRentalForm((prev) => ({
                      ...prev,
                      is_paid: e.target.checked,
                    }))
                  }
                />
                Prepaid
              </label>
            </div>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={manualRentalForm.notes}
              onChange={(e) =>
                setManualRentalForm((prev) => ({
                  ...prev,
                  notes: e.target.value,
                }))
              }
              placeholder="Free cancellation until 48h before pickup"
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
            disabled={addingRental || !manualRentalForm.rental_company}
          >
            {addingRental
              ? "Saving..."
              : editingRental
                ? "Update Rental"
                : "Add Rental"}
          </button>
        </div>
      </div>
    </div>
  );
}
