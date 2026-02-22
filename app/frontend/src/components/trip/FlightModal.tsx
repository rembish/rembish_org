import { useEffect, useRef, useState } from "react";
import { BiX } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type {
  ExtractedFlightData,
  FlightDataItem,
  FlightLookupLeg,
} from "./types";

interface FlightModalProps {
  tripId: string;
  startDate: string;
  endDate: string | null;
  onChanged: (flights: FlightDataItem[]) => void;
  onClose: () => void;
}

export default function FlightModal({
  tripId,
  startDate,
  endDate,
  onChanged,
  onClose,
}: FlightModalProps) {
  const [lookupNumber, setLookupNumber] = useState("");
  const [lookupDate, setLookupDate] = useState("");
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupLegs, setLookupLegs] = useState<FlightLookupLeg[]>([]);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [selectedLegs, setSelectedLegs] = useState<Set<number>>(new Set());

  const [manualForm, setManualForm] = useState({
    flight_number: "",
    flight_date: "",
    departure_iata: "",
    arrival_iata: "",
    departure_time: "",
    arrival_time: "",
    airline_name: "",
    aircraft_type: "",
  });

  const [addingFlights, setAddingFlights] = useState(false);
  const [extractedFlights, setExtractedFlights] = useState<
    ExtractedFlightData[]
  >([]);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [selectedExtracted, setSelectedExtracted] = useState<Set<number>>(
    new Set(),
  );

  const extractInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLookupDate(startDate);
  }, [startDate]);

  const handleLookup = async () => {
    if (!lookupNumber || !lookupDate) return;
    setLookupLoading(true);
    setLookupLegs([]);
    setLookupError(null);
    setSelectedLegs(new Set());
    try {
      const params = new URLSearchParams({
        flight_number: lookupNumber,
        date: lookupDate,
      });
      const res = await apiFetch(`/api/v1/travels/flights/lookup?${params}`);
      if (res.status === 501) {
        setLookupError("Flight lookup not configured. Use manual entry.");
        return;
      }
      if (!res.ok) throw new Error("Lookup failed");
      const data = await res.json();
      if (data.error) setLookupError(data.error);
      setLookupLegs(data.legs || []);
      if ((data.legs || []).length === 0 && !data.error) {
        setLookupError("No flights found. Try manual entry.");
      }
    } catch {
      setLookupError("Lookup failed. Try manual entry.");
    } finally {
      setLookupLoading(false);
    }
  };

  const handleAddSelectedLegs = async () => {
    if (selectedLegs.size === 0 || !lookupDate) return;
    setAddingFlights(true);
    try {
      for (const idx of Array.from(selectedLegs).sort()) {
        const leg = lookupLegs[idx];
        await apiFetch(`/api/v1/travels/trips/${tripId}/flights`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            flight_date: leg.departure_date || lookupDate,
            flight_number: leg.flight_number,
            airline_name: leg.airline_name,
            departure_iata: leg.departure_iata,
            arrival_iata: leg.arrival_iata,
            departure_time: leg.departure_time,
            arrival_time: leg.arrival_time,
            arrival_date: leg.arrival_date,
            terminal: leg.terminal,
            arrival_terminal: leg.arrival_terminal,
            aircraft_type: leg.aircraft_type,
          }),
        });
      }
      const res = await apiFetch(`/api/v1/travels/trips/${tripId}/flights`);
      const data = await res.json();
      onChanged(data.flights || []);
      onClose();
    } catch (err) {
      console.error("Failed to add flights:", err);
    } finally {
      setAddingFlights(false);
    }
  };

  const handleExtractUpload = async (file: File) => {
    setExtracting(true);
    setExtractError(null);
    setExtractedFlights([]);
    setSelectedExtracted(new Set());
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/trips/${tripId}/flights/extract`,
        { method: "POST", body: form },
      );
      const data = await res.json();
      if (data.error) {
        setExtractError(data.error);
        return;
      }
      const flights: ExtractedFlightData[] = data.flights || [];
      setExtractedFlights(flights);
      const preSelected = new Set<number>();
      flights.forEach((f, i) => {
        if (!f.is_duplicate) preSelected.add(i);
      });
      setSelectedExtracted(preSelected);
    } catch {
      setExtractError("Upload failed. Try again.");
    } finally {
      setExtracting(false);
      if (extractInputRef.current) extractInputRef.current.value = "";
    }
  };

  const handleAddExtractedFlights = async () => {
    if (selectedExtracted.size === 0) return;
    setAddingFlights(true);
    try {
      for (const idx of Array.from(selectedExtracted).sort()) {
        const ef = extractedFlights[idx];
        if (!ef.flight_number || !ef.departure_iata || !ef.arrival_iata)
          continue;
        await apiFetch(`/api/v1/travels/trips/${tripId}/flights`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            flight_date: ef.flight_date,
            flight_number: ef.flight_number,
            airline_name: ef.airline_name,
            departure_iata: ef.departure_iata,
            arrival_iata: ef.arrival_iata,
            departure_time: ef.departure_time,
            arrival_time: ef.arrival_time,
            arrival_date: ef.arrival_date,
            terminal: ef.terminal,
            arrival_terminal: ef.arrival_terminal,
            aircraft_type: ef.aircraft_type,
            seat: ef.seat,
            booking_reference: ef.booking_reference,
          }),
        });
      }
      const res = await apiFetch(`/api/v1/travels/trips/${tripId}/flights`);
      const data = await res.json();
      onChanged(data.flights || []);
      onClose();
    } catch (err) {
      console.error("Failed to add extracted flights:", err);
    } finally {
      setAddingFlights(false);
    }
  };

  const handleManualAdd = async () => {
    if (
      !manualForm.flight_number ||
      !manualForm.departure_iata ||
      !manualForm.arrival_iata
    )
      return;
    setAddingFlights(true);
    try {
      const res = await apiFetch(`/api/v1/travels/trips/${tripId}/flights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          flight_date: manualForm.flight_date || lookupDate || startDate,
          flight_number: manualForm.flight_number,
          departure_iata: manualForm.departure_iata,
          arrival_iata: manualForm.arrival_iata,
          departure_time: manualForm.departure_time || null,
          arrival_time: manualForm.arrival_time || null,
          airline_name: manualForm.airline_name || null,
          aircraft_type: manualForm.aircraft_type || null,
        }),
      });
      if (!res.ok) throw new Error("Failed to add flight");
      const listRes = await apiFetch(`/api/v1/travels/trips/${tripId}/flights`);
      const data = await listRes.json();
      onChanged(data.flights || []);
      onClose();
    } catch (err) {
      console.error("Failed to add flight:", err);
    } finally {
      setAddingFlights(false);
    }
  };

  const toggleLeg = (idx: number) => {
    setSelectedLegs((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Flight</h2>
          <button className="btn-icon" onClick={onClose}>
            <BiX size={20} />
          </button>
        </div>
        <div style={{ padding: "1.25rem" }}>
          {/* Extraction section */}
          <div className="flight-extract-row">
            <label className="btn-save flight-extract-btn">
              {extracting ? "Extracting..." : "Upload ticket"}
              <input
                ref={extractInputRef}
                type="file"
                accept=".pdf,image/*"
                style={{ display: "none" }}
                disabled={extracting}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleExtractUpload(file);
                }}
              />
            </label>
            <span className="flight-extract-hint">
              PDF or photo — AI extracts flight data
            </span>
          </div>

          {extractError && (
            <p className="flight-lookup-error">{extractError}</p>
          )}

          {extractedFlights.length > 0 && (
            <div className="flight-lookup-results">
              {extractedFlights.map((ef, idx) => (
                <label
                  key={idx}
                  className={`flight-lookup-leg${ef.is_duplicate ? " flight-extracted-duplicate" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedExtracted.has(idx)}
                    disabled={ef.is_duplicate}
                    onChange={() => {
                      setSelectedExtracted((prev) => {
                        const next = new Set(prev);
                        if (next.has(idx)) next.delete(idx);
                        else next.add(idx);
                        return next;
                      });
                    }}
                  />
                  <div className="flight-leg-info">
                    <span className="flight-leg-route">
                      <strong>{ef.departure_iata}</strong>
                      {ef.departure_time && ` ${ef.departure_time}`}
                      {" → "}
                      <strong>{ef.arrival_iata}</strong>
                      {ef.arrival_time && ` ${ef.arrival_time}`}
                      {ef.arrival_date && (
                        <span className="flight-next-day">+1</span>
                      )}
                      {ef.is_duplicate && (
                        <span className="flight-extracted-dup-label">
                          (already exists)
                        </span>
                      )}
                    </span>
                    <span className="flight-leg-details">
                      {[
                        ef.flight_number,
                        ef.airline_name,
                        ef.aircraft_type,
                        ef.seat ? `Seat ${ef.seat}` : null,
                        ef.booking_reference
                          ? `PNR ${ef.booking_reference}`
                          : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    {ef.flight_date && (
                      <span className="flight-leg-details">
                        {ef.flight_date}
                      </span>
                    )}
                  </div>
                </label>
              ))}
              <button
                type="button"
                className="btn-save"
                onClick={handleAddExtractedFlights}
                disabled={selectedExtracted.size === 0 || addingFlights}
              >
                {addingFlights
                  ? "Adding..."
                  : `Add selected (${selectedExtracted.size})`}
              </button>
            </div>
          )}

          {/* Divider */}
          <div className="modal-section-divider">
            or lookup by flight number
          </div>

          {/* Date range notice */}
          {(() => {
            const today = new Date();
            const yearAgo = new Date(today);
            yearAgo.setFullYear(yearAgo.getFullYear() - 1);
            const weeksAhead = new Date(today);
            weeksAhead.setDate(weeksAhead.getDate() + 42);
            const tripStart = startDate ? new Date(startDate) : null;
            const tripEnd = endDate ? new Date(endDate) : tripStart;
            if (tripEnd && tripEnd < yearAgo) {
              return (
                <p className="flight-api-notice">
                  This trip is older than 1 year — flight lookup is unavailable.
                  Use manual entry below.
                </p>
              );
            }
            if (tripStart && tripStart > weeksAhead) {
              return (
                <p className="flight-api-notice">
                  This trip is more than 6 weeks away — airline schedules may
                  not be published yet. Lookup may return no results.
                </p>
              );
            }
            return null;
          })()}

          {/* AeroDataBox lookup */}
          <div className="flight-lookup-row">
            <div className="form-group">
              <label>Flight Number</label>
              <input
                type="text"
                value={lookupNumber}
                onChange={(e) => setLookupNumber(e.target.value.toUpperCase())}
                placeholder="TK1770"
                className="flight-input"
              />
            </div>
            <div className="form-group">
              <label>Date</label>
              <input
                type="date"
                value={lookupDate}
                onChange={(e) => setLookupDate(e.target.value)}
                min={startDate || undefined}
                max={endDate || undefined}
                className="flight-input"
              />
            </div>
            <button
              type="button"
              className="btn-save flight-lookup-btn"
              onClick={handleLookup}
              disabled={lookupLoading || !lookupNumber || !lookupDate}
            >
              {lookupLoading ? "Looking up..." : "Lookup"}
            </button>
          </div>

          {lookupError && <p className="flight-lookup-error">{lookupError}</p>}

          {lookupLegs.length > 0 && (
            <div className="flight-lookup-results">
              {lookupLegs.map((leg, idx) => (
                <label key={idx} className="flight-lookup-leg">
                  <input
                    type="checkbox"
                    checked={selectedLegs.has(idx)}
                    onChange={() => toggleLeg(idx)}
                  />
                  <div className="flight-leg-info">
                    <span className="flight-leg-route">
                      <strong>{leg.departure_iata}</strong>
                      {leg.departure_name && (
                        <span className="flight-leg-airport-name">
                          {leg.departure_name}
                        </span>
                      )}
                      {leg.departure_time && ` ${leg.departure_time}`}
                      {" → "}
                      <strong>{leg.arrival_iata}</strong>
                      {leg.arrival_name && (
                        <span className="flight-leg-airport-name">
                          {leg.arrival_name}
                        </span>
                      )}
                      {leg.arrival_time && ` ${leg.arrival_time}`}
                      {leg.arrival_date && (
                        <span className="flight-next-day">+1</span>
                      )}
                    </span>
                    <span className="flight-leg-details">
                      {[
                        leg.airline_name,
                        leg.aircraft_type,
                        leg.terminal ? `Terminal ${leg.terminal}` : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </div>
                </label>
              ))}
              <button
                type="button"
                className="btn-save"
                onClick={handleAddSelectedLegs}
                disabled={selectedLegs.size === 0 || addingFlights}
              >
                {addingFlights
                  ? "Adding..."
                  : `Add selected (${selectedLegs.size})`}
              </button>
            </div>
          )}

          {/* Divider */}
          <div className="modal-section-divider">or enter manually</div>

          {/* Manual form */}
          <div className="flight-manual-form">
            <div className="form-row">
              <div className="form-group">
                <label>Flight Number *</label>
                <input
                  type="text"
                  value={manualForm.flight_number}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      flight_number: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder="TK1770"
                />
              </div>
              <div className="form-group">
                <label>Date</label>
                <input
                  type="date"
                  value={manualForm.flight_date || lookupDate}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      flight_date: e.target.value,
                    }))
                  }
                  min={startDate || undefined}
                  max={endDate || undefined}
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>From IATA *</label>
                <input
                  type="text"
                  value={manualForm.departure_iata}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      departure_iata: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder="PRG"
                  maxLength={3}
                />
              </div>
              <div className="form-group">
                <label>To IATA *</label>
                <input
                  type="text"
                  value={manualForm.arrival_iata}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      arrival_iata: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder="IST"
                  maxLength={3}
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Departure Time</label>
                <input
                  type="time"
                  value={manualForm.departure_time}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      departure_time: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="form-group">
                <label>Arrival Time</label>
                <input
                  type="time"
                  value={manualForm.arrival_time}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      arrival_time: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Airline</label>
                <input
                  type="text"
                  value={manualForm.airline_name}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      airline_name: e.target.value,
                    }))
                  }
                  placeholder="Turkish Airlines"
                />
              </div>
              <div className="form-group">
                <label>Aircraft</label>
                <input
                  type="text"
                  value={manualForm.aircraft_type}
                  onChange={(e) =>
                    setManualForm((prev) => ({
                      ...prev,
                      aircraft_type: e.target.value,
                    }))
                  }
                  placeholder="Airbus A321"
                />
              </div>
            </div>
          </div>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-save"
            onClick={
              selectedExtracted.size > 0
                ? handleAddExtractedFlights
                : selectedLegs.size > 0
                  ? handleAddSelectedLegs
                  : handleManualAdd
            }
            disabled={
              addingFlights ||
              (selectedExtracted.size === 0 &&
                selectedLegs.size === 0 &&
                (!manualForm.flight_number ||
                  !manualForm.departure_iata ||
                  !manualForm.arrival_iata))
            }
          >
            {addingFlights
              ? "Adding..."
              : selectedExtracted.size > 0
                ? `Add ${selectedExtracted.size} extracted`
                : selectedLegs.size > 0
                  ? `Add ${selectedLegs.size} looked up`
                  : "Add Flight"}
          </button>
        </div>
      </div>
    </div>
  );
}
