import { useEffect, useRef, useState } from "react";
import {
  BiSolidPlane,
  BiTrash,
  BiCopy,
  BiCar,
  BiPencil,
  BiTrain,
  BiFile,
  BiCloudUpload,
  BiX,
} from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type {
  TripFormData,
  TCCDestinationOption,
  FlightDataItem,
  CarRentalItem,
  TransportBookingItem,
} from "./types";
import {
  formatRentalDatetime,
  TRANSPORT_TYPE_ICONS,
  TRANSPORT_TYPE_LABELS,
} from "./helpers";
import FlightModal from "./FlightModal";
import CarRentalModal from "./CarRentalModal";
import TransportBookingModal from "./TransportBookingModal";

interface TransportTabProps {
  tripId: string;
  formData: TripFormData;
  tccOptions: TCCDestinationOption[];
  tripCitiesDisplay: { name: string; country_code: string | null }[];
  readOnly: boolean;
  onFlightsCountChange: (count: number) => void;
}

export default function TransportTab({
  tripId,
  formData,
  tccOptions,
  tripCitiesDisplay,
  readOnly,
  onFlightsCountChange,
}: TransportTabProps) {
  const [flights, setFlights] = useState<FlightDataItem[]>([]);
  const [carRentals, setCarRentals] = useState<CarRentalItem[]>([]);
  const [transportBookings, setTransportBookings] = useState<
    TransportBookingItem[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [vaultUnlocked, setVaultUnlocked] = useState(false);
  const [showFlightModal, setShowFlightModal] = useState(false);
  const [showCarRentalModal, setShowCarRentalModal] = useState(false);
  const [editingRental, setEditingRental] = useState<CarRentalItem | null>(
    null,
  );
  const [showTransportModal, setShowTransportModal] = useState(false);
  const [editingTransport, setEditingTransport] =
    useState<TransportBookingItem | null>(null);
  const [uploadingTransportDoc, setUploadingTransportDoc] = useState<
    number | null
  >(null);
  const transportDocInputRef = useRef<HTMLInputElement>(null);

  // Fetch transport data on mount
  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiFetch(`/api/v1/travels/trips/${tripId}/flights`).then((r) => r.json()),
      apiFetch(`/api/v1/travels/trips/${tripId}/car-rentals`).then((r) =>
        r.json(),
      ),
      apiFetch(`/api/v1/travels/trips/${tripId}/transport-bookings`).then((r) =>
        r.json(),
      ),
    ])
      .then(([flightsData, rentalsData, transportData]) => {
        setFlights(flightsData.flights || []);
        setCarRentals(rentalsData.car_rentals || []);
        setTransportBookings(transportData.transport_bookings || []);
      })
      .catch((err) => console.error("Failed to load transport data:", err))
      .finally(() => setLoading(false));

    apiFetch("/api/auth/vault/status")
      .then((r) => r.json())
      .then((data) => setVaultUnlocked(data.unlocked === true))
      .catch(() => setVaultUnlocked(false));
  }, [tripId]);

  // Listen for vault status changes
  useEffect(() => {
    const onVaultChange = () => {
      apiFetch("/api/auth/vault/status")
        .then((r) => r.json())
        .then((data) => setVaultUnlocked(data.unlocked === true))
        .catch(() => setVaultUnlocked(false));
    };
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, []);

  // Sync flights count to parent
  useEffect(() => {
    if (flights.length > 0) {
      onFlightsCountChange(flights.length);
    }
  }, [flights, onFlightsCountChange]);

  const handleDeleteFlight = async (flightId: number) => {
    if (!confirm("Delete this flight?")) return;
    try {
      await apiFetch(`/api/v1/travels/flights/${flightId}`, {
        method: "DELETE",
      });
      setFlights((prev) => prev.filter((f) => f.id !== flightId));
    } catch (err) {
      console.error("Failed to delete flight:", err);
    }
  };

  const handleDeleteRental = async (rentalId: number) => {
    if (!confirm("Delete this car rental?")) return;
    try {
      await apiFetch(`/api/v1/travels/car-rentals/${rentalId}`, {
        method: "DELETE",
      });
      setCarRentals((prev) => prev.filter((r) => r.id !== rentalId));
    } catch (err) {
      console.error("Failed to delete rental:", err);
    }
  };

  const handleDeleteTransport = async (bookingId: number) => {
    if (!confirm("Delete this transport booking?")) return;
    try {
      await apiFetch(`/api/v1/travels/transport-bookings/${bookingId}`, {
        method: "DELETE",
      });
      setTransportBookings((prev) => prev.filter((b) => b.id !== bookingId));
    } catch (err) {
      console.error("Failed to delete transport booking:", err);
    }
  };

  const handleTransportDocUpload = async (bookingId: number, file: File) => {
    setUploadingTransportDoc(bookingId);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/transport-bookings/${bookingId}/document`,
        { method: "POST", body: form },
      );
      if (!res.ok) throw new Error("Upload failed");
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/transport-bookings`,
      );
      const data = await listRes.json();
      setTransportBookings(data.transport_bookings || []);
    } catch (err) {
      console.error("Failed to upload document:", err);
    } finally {
      setUploadingTransportDoc(null);
      if (transportDocInputRef.current) transportDocInputRef.current.value = "";
    }
  };

  const handleViewTransportDoc = async (bookingId: number) => {
    try {
      const res = await apiFetch(
        `/api/v1/travels/transport-bookings/${bookingId}/document`,
      );
      const data = await res.json();
      if (data.url) window.open(data.url, "_blank");
    } catch (err) {
      console.error("Failed to get document URL:", err);
    }
  };

  const handleDeleteTransportDoc = async (bookingId: number) => {
    if (!confirm("Delete the attached document?")) return;
    try {
      await apiFetch(
        `/api/v1/travels/transport-bookings/${bookingId}/document`,
        { method: "DELETE" },
      );
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/transport-bookings`,
      );
      const data = await listRes.json();
      setTransportBookings(data.transport_bookings || []);
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  if (loading) {
    return (
      <div className="trip-transport-tab">
        <p>Loading flights...</p>
      </div>
    );
  }

  const tripDests = formData.destinations
    .map((d) => tccOptions.find((o) => o.id === d.tcc_destination_id)?.name)
    .filter(Boolean);
  const dateFrom = formData.start_date
    ? new Date(formData.start_date + "T00:00:00").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "";
  const dateTo = formData.end_date
    ? new Date(formData.end_date + "T00:00:00").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "";

  return (
    <div className="trip-transport-tab">
      {/* Trip context for email search */}
      {!readOnly && (
        <div className="transport-trip-context">
          <span className="transport-dates">
            {dateFrom}
            {dateTo && ` – ${dateTo}`}
          </span>
          {tripDests.length > 0 && (
            <span className="transport-destinations">
              {tripDests.join(", ")}
            </span>
          )}
          {tripCitiesDisplay.length > 0 && (
            <div className="transport-cities">
              {tripCitiesDisplay.map((c, i) => (
                <span key={i} className="transport-city">
                  {c.country_code && <Flag code={c.country_code} size={14} />}
                  {c.name}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Flight list */}
      <div className="form-section">
        <h3 className="section-header-with-action">
          Flights ({flights.length})
          {!readOnly && (
            <button
              type="button"
              className="btn-add-inline"
              onClick={() => setShowFlightModal(true)}
            >
              + Add
            </button>
          )}
        </h3>
        {flights.length === 0 ? (
          <p className="flight-empty">No flights added yet.</p>
        ) : (
          <div className="flight-list">
            {flights.map((f) => (
              <div key={f.id} className="flight-card">
                <div className="flight-card-main">
                  <div className="flight-card-header">
                    <span className="flight-number">{f.flight_number}</span>
                    {f.airline_name && (
                      <span className="flight-airline">{f.airline_name}</span>
                    )}
                    {f.aircraft_type && (
                      <span className="flight-aircraft">{f.aircraft_type}</span>
                    )}
                  </div>
                  <div className="flight-route">
                    <span className="flight-airport">
                      <strong>{f.departure_airport.iata_code}</strong>
                      {f.departure_time && (
                        <span className="flight-time">{f.departure_time}</span>
                      )}
                      <span className="flight-date">
                        {new Date(
                          f.flight_date + "T00:00:00",
                        ).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                      {f.terminal && (
                        <span className="flight-terminal">T{f.terminal}</span>
                      )}
                    </span>
                    <span className="flight-arrow">
                      <BiSolidPlane />
                    </span>
                    <span className="flight-airport">
                      <strong>{f.arrival_airport.iata_code}</strong>
                      {f.arrival_time && (
                        <span className="flight-time">{f.arrival_time}</span>
                      )}
                      <span className="flight-date">
                        {new Date(
                          (f.arrival_date || f.flight_date) + "T00:00:00",
                        ).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                      {f.arrival_terminal && (
                        <span className="flight-terminal">
                          T{f.arrival_terminal}
                        </span>
                      )}
                    </span>
                  </div>
                  {(f.seat || f.booking_reference) && (
                    <div className="flight-details">
                      {f.seat && (
                        <span className="flight-badge">Seat {f.seat}</span>
                      )}
                      {f.booking_reference && (
                        <span className="flight-badge">
                          {vaultUnlocked ? (
                            <>
                              {f.booking_reference}
                              <button
                                className="btn-icon-inline"
                                title="Copy PNR"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigator.clipboard.writeText(
                                    f.booking_reference!,
                                  );
                                }}
                              >
                                <BiCopy />
                              </button>
                            </>
                          ) : (
                            "PNR ••••••"
                          )}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                {!readOnly && (
                  <button
                    className="flight-delete-btn"
                    onClick={() => handleDeleteFlight(f.id)}
                    title="Delete flight"
                  >
                    <BiTrash />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Flight Modal */}
      {showFlightModal && (
        <FlightModal
          tripId={tripId}
          startDate={formData.start_date}
          endDate={formData.end_date}
          onChanged={(updatedFlights) => setFlights(updatedFlights)}
          onClose={() => setShowFlightModal(false)}
        />
      )}

      {/* Car Rentals section */}
      <div className="form-section">
        <h3 className="section-header-with-action">
          <span>
            <BiCar style={{ verticalAlign: "middle", marginRight: 6 }} />
            Car Rentals ({carRentals.length})
          </span>
          {!readOnly && (
            <button
              type="button"
              className="btn-add-inline"
              onClick={() => {
                setEditingRental(null);
                setShowCarRentalModal(true);
              }}
            >
              + Add
            </button>
          )}
        </h3>
        {carRentals.length === 0 ? (
          <p className="flight-empty">No car rentals added yet.</p>
        ) : (
          <div className="car-rental-list">
            {carRentals.map((r) => (
              <div key={r.id} className="car-rental-card">
                <div className="car-rental-main">
                  <div className="car-rental-header">
                    <span className="car-rental-company">
                      {r.rental_company}
                    </span>
                    {r.car_class && (
                      <span className="car-rental-class">{r.car_class}</span>
                    )}
                  </div>
                  {(r.pickup_location ||
                    r.dropoff_location ||
                    r.pickup_datetime ||
                    r.dropoff_datetime) && (
                    <div className="car-rental-route">
                      {(r.pickup_location || r.pickup_datetime) && (
                        <div className="car-rental-route-row">
                          <span className="car-rental-route-label">Pickup</span>
                          {r.pickup_location && (
                            <a
                              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.pickup_location)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="car-rental-location-link"
                            >
                              {r.pickup_location}
                            </a>
                          )}
                          {r.pickup_datetime && (
                            <span className="car-rental-datetime">
                              {formatRentalDatetime(r.pickup_datetime)}
                            </span>
                          )}
                        </div>
                      )}
                      {(r.dropoff_location || r.dropoff_datetime) && (
                        <div className="car-rental-route-row">
                          <span className="car-rental-route-label">Return</span>
                          {r.dropoff_location && (
                            <a
                              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.dropoff_location)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="car-rental-location-link"
                            >
                              {r.dropoff_location}
                            </a>
                          )}
                          {r.dropoff_datetime && (
                            <span className="car-rental-datetime">
                              {formatRentalDatetime(r.dropoff_datetime)}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="car-rental-details">
                    {r.actual_car && (
                      <span className="flight-badge">{r.actual_car}</span>
                    )}
                    {r.transmission && (
                      <span className="flight-badge">
                        {r.transmission === "automatic"
                          ? "Automatic"
                          : "Manual"}
                      </span>
                    )}
                    {r.total_amount && (
                      <span className="flight-badge">{r.total_amount}</span>
                    )}
                    {r.is_paid !== null && (
                      <span className="flight-badge">
                        {r.is_paid ? "Prepaid" : "Pay on pickup"}
                      </span>
                    )}
                    {r.confirmation_number && vaultUnlocked && (
                      <span className="flight-badge">
                        {r.confirmation_number}
                        <button
                          className="btn-icon-inline"
                          title="Copy"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(
                              r.confirmation_number!,
                            );
                          }}
                        >
                          <BiCopy />
                        </button>
                      </span>
                    )}
                  </div>
                </div>
                {!readOnly && (
                  <div className="car-rental-actions">
                    <button
                      className="flight-delete-btn"
                      onClick={() => {
                        setEditingRental(r);
                        setShowCarRentalModal(true);
                      }}
                      title="Edit rental"
                    >
                      <BiPencil />
                    </button>
                    <button
                      className="flight-delete-btn"
                      onClick={() => handleDeleteRental(r.id)}
                      title="Delete rental"
                    >
                      <BiTrash />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {carRentals.length > 0 && (
          <p className="transport-hint-box">
            Remember to update <a href="/travels">driving flags</a> for
            countries on this trip.
          </p>
        )}
      </div>

      {/* Car Rental Modal */}
      {showCarRentalModal && (
        <CarRentalModal
          tripId={tripId}
          editingRental={editingRental}
          onChanged={(updatedRentals) => {
            setCarRentals(updatedRentals);
            setEditingRental(null);
          }}
          onClose={() => {
            setShowCarRentalModal(false);
            setEditingRental(null);
          }}
        />
      )}

      {/* Transport Bookings section */}
      <div className="form-section">
        <h3 className="section-header-with-action">
          <span>
            <BiTrain style={{ verticalAlign: "middle", marginRight: 6 }} />
            Trains, Buses & Ferries ({transportBookings.length})
          </span>
          {!readOnly && (
            <button
              type="button"
              className="btn-add-inline"
              onClick={() => {
                setEditingTransport(null);
                setShowTransportModal(true);
              }}
            >
              + Add
            </button>
          )}
        </h3>
        {transportBookings.length === 0 ? (
          <p className="flight-empty">No transport bookings added yet.</p>
        ) : (
          <div className="transport-booking-list">
            {transportBookings.map((b) => {
              const TypeIcon = TRANSPORT_TYPE_ICONS[b.type] || BiTrain;
              return (
                <div key={b.id} className="transport-booking-card">
                  <div className="transport-booking-main">
                    <div className="transport-booking-header">
                      <span
                        className="transport-booking-type-icon"
                        title={TRANSPORT_TYPE_LABELS[b.type] || b.type}
                      >
                        <TypeIcon size={18} />
                      </span>
                      {b.operator && (
                        <span className="transport-booking-operator">
                          {b.operator}
                        </span>
                      )}
                      {b.service_number && (
                        <span className="transport-booking-number">
                          {b.service_number}
                        </span>
                      )}
                    </div>
                    {(b.departure_station ||
                      b.arrival_station ||
                      b.departure_datetime ||
                      b.arrival_datetime) && (
                      <div className="transport-booking-route">
                        {(b.departure_station || b.departure_datetime) && (
                          <div className="transport-booking-route-row">
                            <span className="transport-booking-route-label">
                              From
                            </span>
                            {b.departure_station && (
                              <a
                                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(b.departure_station)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="transport-booking-station-link"
                              >
                                {b.departure_station}
                              </a>
                            )}
                            {b.departure_datetime && (
                              <span className="transport-booking-datetime">
                                {formatRentalDatetime(b.departure_datetime)}
                              </span>
                            )}
                          </div>
                        )}
                        {(b.arrival_station || b.arrival_datetime) && (
                          <div className="transport-booking-route-row">
                            <span className="transport-booking-route-label">
                              To
                            </span>
                            {b.arrival_station && (
                              <a
                                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(b.arrival_station)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="transport-booking-station-link"
                              >
                                {b.arrival_station}
                              </a>
                            )}
                            {b.arrival_datetime && (
                              <span className="transport-booking-datetime">
                                {formatRentalDatetime(b.arrival_datetime)}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                    <div className="transport-booking-details">
                      {b.carriage && (
                        <span className="flight-badge">Car {b.carriage}</span>
                      )}
                      {b.seat && (
                        <span className="flight-badge">Seat {b.seat}</span>
                      )}
                      {b.booking_reference && vaultUnlocked && (
                        <span className="flight-badge">
                          {b.booking_reference}
                          <button
                            className="btn-icon-inline"
                            title="Copy"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigator.clipboard.writeText(
                                b.booking_reference!,
                              );
                            }}
                          >
                            <BiCopy />
                          </button>
                        </span>
                      )}
                      {b.notes && (
                        <span className="flight-badge">{b.notes}</span>
                      )}
                    </div>
                  </div>
                  <div className="transport-booking-actions">
                    {b.has_document && (
                      <button
                        className="transport-booking-doc-btn"
                        onClick={() => handleViewTransportDoc(b.id)}
                        title={`View ${b.document_name || "document"}`}
                      >
                        <BiFile size={16} />
                      </button>
                    )}
                    {!readOnly && (
                      <>
                        <label
                          className="transport-booking-doc-btn"
                          title="Attach document"
                          style={{ cursor: "pointer" }}
                        >
                          <BiCloudUpload size={16} />
                          <input
                            type="file"
                            accept=".pdf,image/*"
                            style={{ display: "none" }}
                            disabled={uploadingTransportDoc === b.id}
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleTransportDocUpload(b.id, file);
                            }}
                          />
                        </label>
                        {b.has_document && (
                          <button
                            className="transport-booking-doc-btn"
                            onClick={() => handleDeleteTransportDoc(b.id)}
                            title="Remove document"
                          >
                            <BiX size={16} />
                          </button>
                        )}
                        <button
                          className="flight-delete-btn"
                          onClick={() => {
                            setEditingTransport(b);
                            setShowTransportModal(true);
                          }}
                          title="Edit booking"
                        >
                          <BiPencil />
                        </button>
                        <button
                          className="flight-delete-btn"
                          onClick={() => handleDeleteTransport(b.id)}
                          title="Delete booking"
                        >
                          <BiTrash />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Transport Booking Modal */}
      {showTransportModal && (
        <TransportBookingModal
          tripId={tripId}
          editingBooking={editingTransport}
          onChanged={(updatedBookings) => {
            setTransportBookings(updatedBookings);
            setEditingTransport(null);
          }}
          onClose={() => {
            setShowTransportModal(false);
            setEditingTransport(null);
          }}
        />
      )}
    </div>
  );
}
