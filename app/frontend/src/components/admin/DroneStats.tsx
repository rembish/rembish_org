import { useCallback, useEffect, useState } from "react";
import { BiGlobe, BiMapPin, BiRocket, BiTimeFive } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type { DroneStatsData } from "./types";
import { fmtDate } from "./types";

function fmtHours(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.round((sec % 3600) / 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export default function DroneStats() {
  const [stats, setStats] = useState<DroneStatsData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/travels/drone-stats");
      if (res.ok) {
        setStats(await res.json());
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) return <p>Loading...</p>;
  if (!stats || stats.total_flights === 0)
    return <p className="empty-state">No drone flight data yet.</p>;

  const yearMax = Math.max(...stats.by_year.map((y) => y.flights_count), 1);

  // Outlier detection for year chart
  const secondMaxYear =
    stats.by_year.length > 1
      ? Math.max(
          ...stats.by_year
            .slice()
            .sort((a, b) => b.flights_count - a.flights_count)
            .slice(1)
            .map((y) => y.flights_count),
          1,
        )
      : yearMax;
  const hasYearOutlier =
    stats.by_year.length > 1 &&
    stats.by_year.reduce(
      (max, y) => (y.flights_count > max ? y.flights_count : max),
      0,
    ) >
      secondMaxYear * 1.5;
  const yearScale = hasYearOutlier ? secondMaxYear * 1.4 : yearMax;

  return (
    <div className="drone-stats">
      {/* Summary cards */}
      <div className="drone-stats-summary">
        <div className="drone-stats-card">
          <BiRocket className="drone-stats-icon" />
          <div className="drone-stats-card-value">{stats.total_flights}</div>
          <div className="drone-stats-card-label">Flights</div>
        </div>
        <div className="drone-stats-card">
          <BiTimeFive className="drone-stats-icon" />
          <div className="drone-stats-card-value">
            {fmtHours(stats.total_duration_sec)}
          </div>
          <div className="drone-stats-card-label">Flight Time</div>
        </div>
        <div className="drone-stats-card">
          <BiMapPin className="drone-stats-icon" />
          <div className="drone-stats-card-value">
            {stats.total_distance_km.toFixed(0)} km
          </div>
          <div className="drone-stats-card-label">Distance</div>
        </div>
        <div className="drone-stats-card">
          <BiGlobe className="drone-stats-icon" />
          <div className="drone-stats-card-value">{stats.total_countries}</div>
          <div className="drone-stats-card-label">Countries</div>
        </div>
      </div>

      {stats.first_flight_date && stats.last_flight_date && (
        <p className="drone-stats-date-range">
          {fmtDate(stats.first_flight_date)} &mdash;{" "}
          {fmtDate(stats.last_flight_date)}
        </p>
      )}

      {/* Flights by year */}
      <div className="flight-stats-section">
        <h3 className="flight-stats-title">Flights by Year</h3>
        {stats.by_year.map((y) => {
          const sorted = stats.by_year
            .slice()
            .sort((a, b) => b.flights_count - a.flights_count);
          const isOutlier =
            hasYearOutlier && y.flights_count === sorted[0].flights_count;
          return (
            <div
              key={y.year}
              className="flight-stats-bar-row"
              title={`${y.flights_count} flights, ${y.total_distance_km.toFixed(0)} km, ${y.countries.length} countries`}
            >
              <span className="flight-stats-label">{y.year}</span>
              {isOutlier ? (
                <div
                  className="flight-stats-bar flight-stats-bar-outlier"
                  style={{
                    background:
                      "linear-gradient(to right, #0563bb, #e74c3c 50%, #e67e22)",
                  }}
                >
                  <span className="flight-stats-bar-value">
                    {y.flights_count}
                  </span>
                </div>
              ) : (
                <div
                  className="flight-stats-bar"
                  style={{
                    width: `${Math.max((y.flights_count / yearScale) * 100, 2)}%`,
                    background: "#0563bb",
                  }}
                >
                  <span className="flight-stats-bar-value">
                    {y.flights_count}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Per-drone breakdown */}
      {stats.by_drone.length > 0 && (
        <div className="flight-stats-section">
          <h3 className="flight-stats-title">By Drone</h3>
          {stats.by_drone.map((d) => {
            const droneMax = Math.max(
              ...stats.by_drone.map((x) => x.flights_count),
              1,
            );
            return (
              <div key={d.drone_id} className="flight-stats-bar-row">
                <span className="flight-stats-label">
                  {d.drone_name}
                  <br />
                  <small>{d.drone_model}</small>
                </span>
                <div
                  className="flight-stats-bar"
                  style={{
                    width: `${Math.max((d.flights_count / droneMax) * 100, 2)}%`,
                    background: "#27ae60",
                  }}
                >
                  <span className="flight-stats-bar-value">
                    {d.flights_count}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
