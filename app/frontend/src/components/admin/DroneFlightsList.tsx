import { useCallback, useEffect, useState } from "react";
import { BiHide, BiLink, BiShow, BiTrash, BiX } from "react-icons/bi";
import { MapContainer, TileLayer, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type { BatteryItem, DroneFlightItem, DroneItem } from "./types";
import { fmtDate } from "./types";

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

// Fit map bounds to the flight path polyline
function FitPath({ path }: { path: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (path.length > 0) {
      const bounds = L.latLngBounds(path);
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [map, path]);
  return null;
}

export default function DroneFlightsList({ readOnly }: { readOnly?: boolean }) {
  const [flights, setFlights] = useState<DroneFlightItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [drones, setDrones] = useState<DroneItem[]>([]);
  const [batteries, setBatteries] = useState<BatteryItem[]>([]);
  const [mapFlight, setMapFlight] = useState<DroneFlightItem | null>(null);

  // Filters
  const [filterDrone, setFilterDrone] = useState<string>("");
  const [filterYear, setFilterYear] = useState<string>("");
  const [filterCountry, setFilterCountry] = useState<string>("");
  const [filterBattery, setFilterBattery] = useState<string>("");

  const fetchFlights = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterDrone) params.set("drone_id", filterDrone);
    if (filterYear) params.set("year", filterYear);
    if (filterCountry) params.set("country", filterCountry);
    if (filterBattery) params.set("battery_id", filterBattery);
    const qs = params.toString();
    try {
      const res = await apiFetch(
        `/api/v1/travels/drone-flights${qs ? `?${qs}` : ""}`,
      );
      if (res.ok) {
        const data = await res.json();
        setFlights(data.flights);
        setTotal(data.total);
      }
    } finally {
      setLoading(false);
    }
  }, [filterDrone, filterYear, filterCountry, filterBattery]);

  const fetchDrones = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/travels/drones");
      if (res.ok) {
        const data = await res.json();
        setDrones(data.drones);
      }
    } catch {
      // ignore
    }
  }, []);

  const fetchBatteries = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/travels/batteries");
      if (res.ok) {
        const data = await res.json();
        setBatteries(data.batteries);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchDrones();
    fetchBatteries();
  }, [fetchDrones, fetchBatteries]);

  useEffect(() => {
    fetchFlights();
  }, [fetchFlights]);

  const toggleHide = async (id: number) => {
    const res = await apiFetch(`/api/v1/travels/drone-flights/${id}/hide`, {
      method: "PUT",
    });
    if (res.ok) fetchFlights();
  };

  const deleteFlight = async (f: DroneFlightItem) => {
    const label = `${fmtDate(f.flight_date)}${f.city ? ` — ${f.city}` : ""}`;
    if (!confirm(`Delete flight ${label}? This cannot be undone.`)) return;
    const res = await apiFetch(`/api/v1/travels/drone-flights/${f.id}`, {
      method: "DELETE",
    });
    if (res.ok) fetchFlights();
  };

  // Build year options from flight dates
  const years = [
    ...new Set(flights.map((f) => f.flight_date.slice(0, 4))),
  ].sort((a, b) => b.localeCompare(a));
  const regionNames = new Intl.DisplayNames(["en"], { type: "region" });
  const countries = [
    ...new Set(flights.map((f) => f.country).filter(Boolean)),
  ].sort((a, b) => {
    const na = regionNames.of(a!) ?? a!;
    const nb = regionNames.of(b!) ?? b!;
    return na.localeCompare(nb);
  });

  const openMap = (f: DroneFlightItem) => {
    if (f.flight_path && f.flight_path.length >= 2) setMapFlight(f);
  };

  // Convert flight_path [[lng, lat], ...] to leaflet [[lat, lng], ...]
  const mapPath: [number, number][] =
    mapFlight?.flight_path?.map(([lng, lat]) => [lat, lng]) ?? [];

  return (
    <div className="drone-flights-list">
      <div className="drone-flights-filters">
        <select
          value={filterDrone}
          onChange={(e) => setFilterDrone(e.target.value)}
        >
          <option value="">All drones</option>
          {drones.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={filterYear}
          onChange={(e) => setFilterYear(e.target.value)}
        >
          <option value="">All years</option>
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          value={filterCountry}
          onChange={(e) => setFilterCountry(e.target.value)}
        >
          <option value="">All countries</option>
          {countries.map((c) => (
            <option key={c} value={c!}>
              {regionNames.of(c!) ?? c}
            </option>
          ))}
        </select>
        {batteries.length > 0 && (
          <select
            value={filterBattery}
            onChange={(e) => setFilterBattery(e.target.value)}
          >
            <option value="">All batteries</option>
            {batteries.map((b) => (
              <option key={b.id} value={b.id}>
                {b.serial_number}
              </option>
            ))}
          </select>
        )}
        <span className="drone-flights-count">{total} flights</span>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : flights.length === 0 ? (
        <p className="empty-state">No drone flights found.</p>
      ) : (
        <div className="drone-flights-table-wrap">
          <table className="drone-flights-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Flight</th>
                <th className="drone-col-location">Location</th>
                {!readOnly && <th></th>}
              </tr>
            </thead>
            <tbody>
              {flights.map((f) => (
                <tr
                  key={f.id}
                  className={`drone-flight-row${f.is_hidden ? " drone-flight-hidden" : ""}${f.flight_path && f.flight_path.length >= 2 ? " drone-flight-clickable" : ""}`}
                  onClick={() => openMap(f)}
                >
                  <td className="drone-flight-date-cell">
                    <div>
                      <span>{fmtDate(f.flight_date)}</span>
                      {f.takeoff_time && (
                        <span className="drone-flight-time">
                          {fmtTime(f.takeoff_time)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="drone-flight-stats-cell">
                    <div>
                      <span>{fmtDuration(f.duration_sec)}</span>
                      <span className="drone-flight-time">
                        {fmtDistance(f.distance_km)}
                      </span>
                    </div>
                  </td>
                  <td className="drone-flight-location">
                    <div>
                      <span>
                        {f.country && (
                          <Flag code={f.country.toLowerCase()} size={16} />
                        )}
                        {f.city || f.country || "-"}
                      </span>
                      <span>
                        <span
                          className="drone-badge"
                          style={
                            f.battery_color
                              ? {
                                  background: `${f.battery_color}25`,
                                  color: f.battery_color,
                                }
                              : undefined
                          }
                        >
                          {f.drone_model || "?"}
                        </span>
                        {f.photos > 0 && (
                          <span className="drone-badge drone-badge-media">
                            {f.photos} photo{f.photos !== 1 ? "s" : ""}
                          </span>
                        )}
                        {f.video_sec > 0 && (
                          <span className="drone-badge drone-badge-media">
                            {fmtDuration(f.video_sec)}
                          </span>
                        )}
                        {f.anomaly_severity && (
                          <span
                            className={`drone-badge drone-badge-anomaly anomaly-${f.anomaly_severity.toLowerCase()}`}
                            title={f.anomaly_actions || undefined}
                          >
                            {f.anomaly_severity}
                          </span>
                        )}
                      </span>
                    </div>
                  </td>
                  {!readOnly && (
                    <td
                      className="drone-flight-actions"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div>
                        {f.trip_id && (
                          <a
                            className="btn-icon"
                            href={`/admin/trips/${f.trip_id}/drone-flights`}
                            title={`Trip #${f.trip_id}`}
                          >
                            <BiLink />
                          </a>
                        )}
                        <button
                          className="btn-icon"
                          onClick={() => toggleHide(f.id)}
                          title={f.is_hidden ? "Unhide" : "Hide"}
                        >
                          {f.is_hidden ? <BiHide /> : <BiShow />}
                        </button>
                        <button
                          className="btn-icon btn-icon-danger"
                          onClick={() => deleteFlight(f)}
                          title="Delete"
                        >
                          <BiTrash />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Flight path map modal */}
      {mapFlight && mapPath.length >= 2 && (
        <div className="modal-overlay" onClick={() => setMapFlight(null)}>
          <div
            className="modal-content drone-map-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>
                {fmtDate(mapFlight.flight_date)}
                {mapFlight.takeoff_time
                  ? ` ${fmtTime(mapFlight.takeoff_time)}`
                  : ""}
                {mapFlight.city
                  ? ` — ${mapFlight.city}`
                  : mapFlight.country
                    ? ` — ${mapFlight.country}`
                    : ""}
              </h2>
              <button
                className="modal-close"
                onClick={() => setMapFlight(null)}
              >
                <BiX />
              </button>
            </div>
            <div className="drone-map-container">
              <MapContainer
                center={mapPath[0]}
                zoom={15}
                scrollWheelZoom={true}
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <FitPath path={mapPath} />
                <Polyline
                  positions={mapPath}
                  pathOptions={{
                    color: "#0563bb",
                    weight: 3,
                    opacity: 0.8,
                  }}
                />
              </MapContainer>
            </div>
            <div className="drone-map-details">
              {mapFlight.drone_model && (
                <span className="flight-badge">{mapFlight.drone_model}</span>
              )}
              {mapFlight.duration_sec != null && mapFlight.duration_sec > 0 && (
                <span className="flight-badge">
                  {fmtDuration(mapFlight.duration_sec)}
                </span>
              )}
              {mapFlight.distance_km != null && mapFlight.distance_km > 0 && (
                <span className="flight-badge">
                  {fmtDistance(mapFlight.distance_km)}
                </span>
              )}
              {mapFlight.photos > 0 && (
                <span className="flight-badge">
                  {mapFlight.photos} photo{mapFlight.photos !== 1 ? "s" : ""}
                </span>
              )}
              {mapFlight.video_sec > 0 && (
                <span className="flight-badge">
                  {Math.round(mapFlight.video_sec / 60)}m video
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
