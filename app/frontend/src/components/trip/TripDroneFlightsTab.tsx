import { useEffect, useState } from "react";
import { BiTimeFive } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type { DroneFlightItem } from "../admin/types";
import { fmtDate } from "../admin/types";

function fmtDuration(sec: number | null): string {
  if (!sec) return "-";
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  if (m >= 60) {
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return `${h}h ${rm}m`;
  }
  return `${m}m ${s}s`;
}

function fmtDistance(km: number | null): string {
  if (!km) return "-";
  if (km < 1) return `${Math.round(km * 1000)}m`;
  return `${km.toFixed(1)} km`;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

interface TripDroneFlightsTabProps {
  tripId: string;
  readOnly: boolean;
}

export default function TripDroneFlightsTab({
  tripId,
}: TripDroneFlightsTabProps) {
  const [flights, setFlights] = useState<DroneFlightItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch(`/api/v1/travels/trips/${tripId}/drone-flights`)
      .then((r) => r.json())
      .then((data) => setFlights(data.flights || []))
      .catch((err) => console.error("Failed to load drone flights:", err))
      .finally(() => setLoading(false));
  }, [tripId]);

  if (loading) {
    return (
      <div className="trip-transport-tab">
        <p>Loading drone flights...</p>
      </div>
    );
  }

  return (
    <div className="trip-transport-tab">
      <div className="form-section">
        <h3 className="section-header-with-action">
          <span>
            <BiTimeFive style={{ verticalAlign: "middle", marginRight: 6 }} />
            Drone Flights ({flights.length})
          </span>
        </h3>
        {flights.length === 0 ? (
          <p className="flight-empty">No drone flights on this trip.</p>
        ) : (
          <div className="transport-booking-list">
            {flights.map((f) => (
              <div key={f.id} className="transport-booking-card">
                <div className="transport-booking-main">
                  <div className="transport-booking-header">
                    <span className="transport-booking-operator">
                      {fmtDate(f.flight_date)}
                      {f.takeoff_time ? ` ${fmtTime(f.takeoff_time)}` : ""}
                    </span>
                    {f.drone_model && (
                      <span className="flight-badge">{f.drone_model}</span>
                    )}
                  </div>
                  <div className="transport-booking-details">
                    {f.country && (
                      <span className="flight-badge">
                        <Flag code={f.country} />
                        {f.city || f.country}
                      </span>
                    )}
                    {f.duration_sec != null && f.duration_sec > 0 && (
                      <span className="flight-badge">
                        {fmtDuration(f.duration_sec)}
                      </span>
                    )}
                    {f.distance_km != null && f.distance_km > 0 && (
                      <span className="flight-badge">
                        {fmtDistance(f.distance_km)}
                      </span>
                    )}
                    {f.photos > 0 && (
                      <span className="flight-badge">
                        {f.photos} photo{f.photos !== 1 ? "s" : ""}
                      </span>
                    )}
                    {f.video_sec > 0 && (
                      <span className="flight-badge">
                        {Math.round(f.video_sec / 60)}m video
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
