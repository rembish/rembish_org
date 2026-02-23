import { useCallback, useEffect, useState } from "react";
import { BiHide, BiLink, BiShow, BiTimeFive } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type { DroneFlightItem, DroneItem } from "./types";
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

export default function DroneFlightsList({ readOnly }: { readOnly?: boolean }) {
  const [flights, setFlights] = useState<DroneFlightItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [drones, setDrones] = useState<DroneItem[]>([]);

  // Filters
  const [filterDrone, setFilterDrone] = useState<string>("");
  const [filterYear, setFilterYear] = useState<string>("");
  const [filterCountry, setFilterCountry] = useState<string>("");

  const fetchFlights = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterDrone) params.set("drone_id", filterDrone);
    if (filterYear) params.set("year", filterYear);
    if (filterCountry) params.set("country", filterCountry);
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
  }, [filterDrone, filterYear, filterCountry]);

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

  useEffect(() => {
    fetchDrones();
  }, [fetchDrones]);

  useEffect(() => {
    fetchFlights();
  }, [fetchFlights]);

  const toggleHide = async (id: number) => {
    const res = await apiFetch(`/api/v1/travels/drone-flights/${id}/hide`, {
      method: "PUT",
    });
    if (res.ok) fetchFlights();
  };

  // Build year options from flight dates
  const years = [
    ...new Set(flights.map((f) => f.flight_date.slice(0, 4))),
  ].sort();
  const countries = [
    ...new Set(flights.map((f) => f.country).filter(Boolean)),
  ].sort();

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
              {c}
            </option>
          ))}
        </select>
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
                <th>Time</th>
                <th>Drone</th>
                <th>Location</th>
                <th>Duration</th>
                <th>Distance</th>
                {!readOnly && <th>Trip</th>}
                {!readOnly && <th></th>}
              </tr>
            </thead>
            <tbody>
              {flights.map((f) => (
                <tr
                  key={f.id}
                  className={`drone-flight-row${f.is_hidden ? " drone-flight-hidden" : ""}`}
                >
                  <td>{fmtDate(f.flight_date)}</td>
                  <td className="drone-flight-time">
                    {fmtTime(f.takeoff_time)}
                  </td>
                  <td>
                    <span className="drone-badge">{f.drone_model || "?"}</span>
                  </td>
                  <td className="drone-flight-location">
                    <span>
                      {f.country && (
                        <Flag code={f.country.toLowerCase()} size={16} />
                      )}
                      {f.city || f.country || "-"}
                    </span>
                  </td>
                  <td>
                    <BiTimeFive className="drone-icon-muted" />{" "}
                    {fmtDuration(f.duration_sec)}
                  </td>
                  <td>{fmtDistance(f.distance_km)}</td>
                  {!readOnly && (
                    <td>
                      {f.trip_id ? (
                        <a
                          href={`/admin/trips/${f.trip_id}/drone-flights`}
                          className="drone-trip-link"
                        >
                          <BiLink /> #{f.trip_id}
                        </a>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                  )}
                  {!readOnly && (
                    <td>
                      <button
                        className="btn-icon"
                        onClick={() => toggleHide(f.id)}
                        title={f.is_hidden ? "Unhide" : "Hide"}
                      >
                        {f.is_hidden ? <BiHide /> : <BiShow />}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
