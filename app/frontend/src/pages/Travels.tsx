import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
  Marker,
} from "react-simple-maps";
import {
  BiWorld,
  BiMapAlt,
  BiGlobe,
  BiUpload,
  BiCheck,
  BiX,
  BiTrip,
  BiCalendar,
} from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import Flag from "../components/Flag";

// World map TopoJSON - Visionscarto version (local) includes disputed territories
const geoUrl = "/world-110m.json";

interface MicrostateData {
  name: string;
  longitude: number;
  latitude: number;
  map_region_code: string;
}

interface UNCountryData {
  name: string;
  continent: string;
  visit_date: string | null;
}

interface TCCDestinationData {
  name: string;
  region: string;
  visit_date: string | null;
}

interface TravelStats {
  un_visited: number;
  un_total: number;
  tcc_visited: number;
  tcc_total: number;
  nm_visited: number;
  nm_total: number;
}

interface MapData {
  stats: TravelStats;
  visited_map_regions: Record<string, string>;
  visit_counts: Record<string, number>;
  visited_countries: string[];
  microstates: MicrostateData[];
}

// Calculate color based on visit count (hue) and visit date (lightness)
// Hue: 1 visit = blue, many visits = warm colors (green -> yellow -> orange)
// Lightness: older visits = lighter, recent = darker
function getVisitColor(
  visitDate: string,
  _oldestDate: Date,
  newestDate: Date,
  visitCount: number = 1,
): string {
  const date = new Date(visitDate);
  const baselineDate = new Date("2010-01-01");

  // Hue based on visit count (210 = blue -> 120 = green -> 40 = orange)
  // 1 visit: 210 (blue)
  // 2-5: 180-150 (cyan/teal)
  // 6-15: 120-80 (green/yellow-green)
  // 16-30: 60-40 (yellow/orange)
  // 31+: 30-15 (orange/red-orange)
  let hue: number;
  if (visitCount <= 1) {
    hue = 210;
  } else if (visitCount <= 5) {
    hue = 210 - (visitCount - 1) * 15; // 195 -> 150
  } else if (visitCount <= 15) {
    hue = 150 - (visitCount - 5) * 7; // 143 -> 80
  } else if (visitCount <= 30) {
    hue = 80 - (visitCount - 15) * 2.5; // 77.5 -> 42.5
  } else {
    hue = Math.max(15, 42 - (visitCount - 30) * 0.5); // -> 15 min
  }

  // Saturation - keep high for vibrant colors
  const saturation = 70;

  // Lightness based on date (older = darker, recent = lighter)
  let lightness: number;
  if (date < baselineDate) {
    // Pre-2010 visits get darkest
    lightness = 35;
  } else {
    const totalRange = newestDate.getTime() - baselineDate.getTime();
    if (totalRange === 0) {
      lightness = 50;
    } else {
      // Ratio: 0 = 2010 (darker), 1 = newest (lighter)
      const ratio = (date.getTime() - baselineDate.getTime()) / totalRange;
      // Interpolate from 35% (dark) to 60% (light)
      lightness = 35 + ratio * 25;
    }
  }

  return `hsl(${Math.round(hue)}, ${saturation}%, ${Math.round(lightness)}%)`;
}

// Simple blue gradient for lists (doesn't have visit count context)
function getListVisitColor(
  visitDate: string,
  _oldestDate: Date,
  newestDate: Date,
): string {
  const date = new Date(visitDate);
  const baselineDate = new Date("2010-01-01");

  if (date < baselineDate) {
    return "hsl(210, 70%, 35%)";
  }

  const totalRange = newestDate.getTime() - baselineDate.getTime();
  if (totalRange === 0) return "hsl(210, 70%, 50%)";

  const ratio = (date.getTime() - baselineDate.getTime()) / totalRange;
  const lightness = 35 + ratio * 25;

  return `hsl(210, 70%, ${Math.round(lightness)}%)`;
}

// Format date as "Mon YYYY"
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  return `${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Group items by a key
function groupBy<T>(
  items: T[],
  keyFn: (item: T) => string,
): Record<string, T[]> {
  return items.reduce(
    (acc, item) => {
      const key = keyFn(item);
      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    },
    {} as Record<string, T[]>,
  );
}

interface MonthCountry {
  name: string;
  iso_code: string | null;
  is_new: boolean;
}

interface MonthStats {
  month: number;
  trips_count: number;
  days: number;
  new_countries: number;
  countries: MonthCountry[];
  event: "birthday" | "relocation" | null;
}

interface YearStats {
  year: number;
  trips_count: number;
  days: number;
  countries_visited: number;
  new_countries: number;
  work_trips: number;
  flights: number;
  months: MonthStats[];
}

interface TravelStatsData {
  years: YearStats[];
  totals: {
    trips: number;
    days: number;
    countries: number;
    years: number;
  };
}

type TabType = "map" | "un" | "tcc" | "stats";

export default function Travels() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { tab } = useParams<{ tab?: string }>();
  const activeTab: TabType = (tab as TabType) || "map";

  const setActiveTab = (newTab: TabType) => {
    navigate(`/travels/${newTab}`);
  };

  // Split state for progressive loading
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [unData, setUnData] = useState<UNCountryData[] | null>(null);
  const [tccData, setTccData] = useState<TCCDestinationData[] | null>(null);
  const [statsData, setStatsData] = useState<TravelStatsData | null>(null);
  const [mapLoading, setMapLoading] = useState(true);
  const [unLoading, setUnLoading] = useState(true);
  const [tccLoading, setTccLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{
    name: string;
    visitCount?: number;
    x: number;
    y: number;
  } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"success" | "error" | null>(
    null,
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch all data (used for initial load and after upload)
  const fetchAllData = async () => {
    setMapLoading(true);
    setUnLoading(true);
    setTccLoading(true);
    setStatsLoading(true);

    try {
      // Fetch map data first (shows map immediately)
      const mapRes = await fetch("/api/v1/travels/map-data");
      if (!mapRes.ok) throw new Error("Failed to fetch map data");
      const mapDataResult: MapData = await mapRes.json();
      setMapData(mapDataResult);
      setMapLoading(false);

      // Fetch UN, TCC, and stats data in parallel
      const [unRes, tccRes, statsRes] = await Promise.all([
        fetch("/api/v1/travels/un-countries"),
        fetch("/api/v1/travels/tcc-destinations"),
        fetch("/api/v1/travels/stats"),
      ]);

      if (unRes.ok) {
        const unResult = await unRes.json();
        setUnData(unResult.countries);
      }
      setUnLoading(false);

      if (tccRes.ok) {
        const tccResult = await tccRes.json();
        setTccData(tccResult.destinations);
      }
      setTccLoading(false);

      if (statsRes.ok) {
        const statsResult = await statsRes.json();
        setStatsData(statsResult);
      }
      setStatsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setMapLoading(false);
      setUnLoading(false);
      setTccLoading(false);
      setStatsLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/travels/upload-nm", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      // Refresh all data
      await fetchAllData();
      setUploadStatus("success");
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err) {
      setUploadStatus("error");
      setTimeout(() => setUploadStatus(null), 3000);
      console.error(
        "Upload failed:",
        err instanceof Error ? err.message : "Unknown error",
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  if (mapLoading) {
    return (
      <section id="travels" className="travels">
        <div className="container">
          <p>Loading...</p>
        </div>
      </section>
    );
  }

  if (error || !mapData) {
    return (
      <section id="travels" className="travels">
        <div className="container">
          <p>Failed to load travel data</p>
        </div>
      </section>
    );
  }

  // Calculate date range for color gradient
  const visitDates = Object.values(mapData.visited_map_regions).map(
    (d) => new Date(d),
  );
  const oldestDate = new Date(Math.min(...visitDates.map((d) => d.getTime())));
  const newestDate = new Date(Math.max(...visitDates.map((d) => d.getTime())));

  // Group data by region (only when data is available)
  const unByContinent = unData ? groupBy(unData, (c) => c.continent) : {};
  const tccByRegion = tccData ? groupBy(tccData, (d) => d.region) : {};

  const renderMap = () => (
    <>
      <div
        className="travel-map-container travel-map-tall"
        onMouseLeave={() => setTooltip(null)}
      >
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 140,
          }}
        >
          <ZoomableGroup center={[20, 20]} zoom={1}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const geoId = String(geo.id);
                  const visitDate = mapData.visited_map_regions[geoId];
                  const visitCount = mapData.visit_counts[geoId] || 0;
                  const isVisited = !!visitDate;
                  const fillColor = isVisited
                    ? getVisitColor(
                        visitDate,
                        oldestDate,
                        newestDate,
                        visitCount,
                      )
                    : "#e6e9ec";
                  const countryName = geo.properties?.name || "";
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fillColor}
                      stroke="#ffffff"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: "none", cursor: "pointer" },
                        hover: {
                          outline: "none",
                          fill: isVisited ? "#067ded" : "#d0d4d9",
                        },
                        pressed: { outline: "none" },
                      }}
                      onMouseEnter={(e) => {
                        setTooltip({
                          name: countryName,
                          visitCount: isVisited ? visitCount : undefined,
                          x: e.clientX,
                          y: e.clientY,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      onMouseMove={(e) => {
                        if (tooltip)
                          setTooltip({
                            name: countryName,
                            visitCount: isVisited ? visitCount : undefined,
                            x: e.clientX,
                            y: e.clientY,
                          });
                      }}
                    />
                  );
                })
              }
            </Geographies>
            {mapData.microstates.map((m) => {
              const visitDate = mapData.visited_map_regions[m.map_region_code];
              const visitCount = mapData.visit_counts[m.map_region_code] || 0;
              const isVisited = !!visitDate;
              const fillColor = isVisited
                ? getVisitColor(visitDate, oldestDate, newestDate, visitCount)
                : "#c0c4c8";
              return (
                <Marker key={m.name} coordinates={[m.longitude, m.latitude]}>
                  <circle
                    r={1.5}
                    fill={fillColor}
                    stroke="#ffffff"
                    strokeWidth={0.3}
                    style={{ cursor: "pointer" }}
                    onMouseEnter={(e) => {
                      setTooltip({
                        name: m.name,
                        visitCount: isVisited ? visitCount : undefined,
                        x: e.clientX,
                        y: e.clientY,
                      });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  />
                </Marker>
              );
            })}
            {/* Special location markers */}
            <Marker coordinates={[82.9357, 55.0084]}>
              <circle
                r={1.5}
                fill="#ffffff"
                stroke="#333333"
                strokeWidth={0.3}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setTooltip({
                    name: "Birthplace",
                    x: e.clientX,
                    y: e.clientY,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
              />
            </Marker>
            <Marker coordinates={[14.4378, 50.0755]}>
              <circle
                r={1.5}
                fill="#ffffff"
                stroke="#333333"
                strokeWidth={0.3}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setTooltip({ name: "Home", x: e.clientX, y: e.clientY });
                }}
                onMouseLeave={() => setTooltip(null)}
              />
            </Marker>
          </ZoomableGroup>
        </ComposableMap>
        {tooltip && (
          <div
            className="map-tooltip"
            style={{
              left: tooltip.x + 10,
              top: tooltip.y - 30,
            }}
          >
            {tooltip.name}
            {tooltip.visitCount !== undefined && tooltip.visitCount > 0 && (
              <span className="tooltip-visits">
                {" "}
                ({tooltip.visitCount}{" "}
                {tooltip.visitCount === 1 ? "trip" : "trips"})
              </span>
            )}
          </div>
        )}
      </div>
    </>
  );

  const renderUNList = () => (
    <div className="travel-list">
      {Object.entries(unByContinent)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([continent, countries]) => (
          <div key={continent} className="travel-list-group">
            <h3 className="travel-list-group-title">{continent}</h3>
            <ul className="travel-list-items">
              {countries.map((country) => {
                const color = country.visit_date
                  ? getListVisitColor(
                      country.visit_date,
                      oldestDate,
                      newestDate,
                    )
                  : undefined;
                return (
                  <li
                    key={country.name}
                    className={country.visit_date ? "visited" : ""}
                    style={color ? { backgroundColor: color } : undefined}
                  >
                    <span className="country-name">{country.name}</span>
                    {country.visit_date && (
                      <span className="visit-date">
                        {formatDate(country.visit_date)}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
    </div>
  );

  const renderTCCList = () => (
    <div className="travel-list">
      {Object.entries(tccByRegion)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([region, destinations]) => (
          <div key={region} className="travel-list-group">
            <h3 className="travel-list-group-title">{region}</h3>
            <ul className="travel-list-items">
              {destinations.map((dest) => {
                const color = dest.visit_date
                  ? getListVisitColor(dest.visit_date, oldestDate, newestDate)
                  : undefined;
                return (
                  <li
                    key={dest.name}
                    className={dest.visit_date ? "visited" : ""}
                    style={color ? { backgroundColor: color } : undefined}
                  >
                    <span className="country-name">{dest.name}</span>
                    {dest.visit_date && (
                      <span className="visit-date">
                        {formatDate(dest.visit_date)}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
    </div>
  );

  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  const renderStats = () => {
    if (!statsData) return null;

    return (
      <div className="travel-stats-page">
        <div className="stats-years">
          {statsData.years.map((year) => (
            <div key={year.year} className="stats-year-card">
              <div className="stats-year-header">
                <h3 className="stats-year-title">{year.year}</h3>
                <div className="stats-year-summary">
                  <span className="stats-badge">{year.trips_count} trips</span>
                  <span className="stats-badge">{year.days} days</span>
                  {year.flights > 0 && (
                    <span className="stats-badge">{year.flights} flights</span>
                  )}
                  {year.new_countries > 0 && (
                    <span className="stats-badge stats-badge-new">
                      +{year.new_countries} new
                    </span>
                  )}
                  {year.work_trips > 0 && (
                    <span className="stats-badge stats-badge-work">
                      {year.work_trips} work
                    </span>
                  )}
                </div>
              </div>
              <div className="stats-months">
                {year.months
                  .slice()
                  .reverse()
                  .map((month) => (
                    <div
                      key={month.month}
                      className={`stats-month ${month.event ? `stats-month-${month.event}` : ""}`}
                    >
                      <span className="stats-month-name">
                        {monthNames[month.month - 1]}
                      </span>
                      {month.days > 0 ? (
                        <div
                          className="stats-month-bar"
                          style={{
                            width: `${Math.min(month.days * 1.6, 50)}%`,
                          }}
                        >
                          <span className="stats-month-days">
                            {month.days}d
                          </span>
                        </div>
                      ) : (
                        <div className="stats-month-bar stats-month-bar-empty" />
                      )}
                      <div className="stats-month-flags">
                        {/* Dedupe by ISO code, keep is_new if any */}
                        {Array.from(
                          month.countries.reduce((map, country) => {
                            const code = country.iso_code || country.name;
                            const existing = map.get(code);
                            if (
                              !existing ||
                              (!existing.is_new && country.is_new)
                            ) {
                              map.set(code, country);
                            }
                            return map;
                          }, new Map<string, MonthCountry>()),
                        ).map(([code, country]) => (
                          <span
                            key={code}
                            className={`stats-flag ${country.is_new ? "stats-flag-new" : ""}`}
                          >
                            <Flag
                              code={country.iso_code}
                              size={20}
                              title={
                                country.name + (country.is_new ? " (new)" : "")
                              }
                            />
                          </span>
                        ))}
                        {month.event === "birthday" && (
                          <span className="stats-event" title="Birthday">
                            🎂
                          </span>
                        )}
                        {month.event === "relocation" && (
                          <span className="stats-event" title="Relocation">
                            📦
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <section id="travels" className="travels">
      <div className="container">
        <div className="travel-stats">
          <div className="stat-card">
            <BiTrip className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {statsData?.totals.trips ?? "..."}
              </span>
              <span className="stat-label">Total Trips</span>
            </div>
          </div>
          <div className="stat-card">
            <BiCalendar className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {statsData?.totals.days ?? "..."}
                <span className="stat-total"> days</span>
              </span>
              <span className="stat-label">
                {statsData?.totals.years ?? "..."} years traveling
              </span>
            </div>
          </div>
          <div className="stat-card">
            <BiWorld className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {mapData.stats.un_visited}
                <span className="stat-total">/{mapData.stats.un_total}</span>
              </span>
              <span className="stat-label">UN Countries</span>
            </div>
            <div className="stat-percent">
              {Math.round(
                (mapData.stats.un_visited / mapData.stats.un_total) * 100,
              )}
              %
            </div>
          </div>
          <a
            href="https://travelerscenturyclub.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="stat-card stat-card-link"
          >
            <BiMapAlt className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {mapData.stats.tcc_visited}
                <span className="stat-total">/{mapData.stats.tcc_total}</span>
              </span>
              <span className="stat-label">TCC Destinations</span>
            </div>
            <div className="stat-percent">
              {Math.round(
                (mapData.stats.tcc_visited / mapData.stats.tcc_total) * 100,
              )}
              %
            </div>
          </a>
          <div className="stat-card-wrapper">
            <a
              href="https://nomadmania.com/profile/11183/"
              target="_blank"
              rel="noopener noreferrer"
              className="stat-card stat-card-link"
            >
              <BiGlobe className="stat-icon" />
              <div className="stat-content">
                <span className="stat-number">
                  {uploading ? "???" : mapData.stats.nm_visited}
                  <span className="stat-total">
                    /{uploading ? "???" : mapData.stats.nm_total}
                  </span>
                </span>
                <span className="stat-label">NM Regions</span>
              </div>
              <div className="stat-percent">
                {uploading ? (
                  <span className="upload-spinner" />
                ) : (
                  `${Math.round((mapData.stats.nm_visited / mapData.stats.nm_total) * 100)}%`
                )}
              </div>
            </a>
            {user?.is_admin && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx"
                  onChange={handleUpload}
                  style={{ display: "none" }}
                />
                <button
                  className={`stat-upload-btn ${uploadStatus === "success" ? "success" : ""} ${uploadStatus === "error" ? "error" : ""}`}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  title="Upload NM regions XLSX"
                >
                  {uploading ? (
                    <span className="upload-spinner" />
                  ) : uploadStatus === "success" ? (
                    <BiCheck />
                  ) : uploadStatus === "error" ? (
                    <BiX />
                  ) : (
                    <BiUpload />
                  )}
                </button>
              </>
            )}
          </div>
        </div>

        <div className="travel-tabs">
          <button
            className={`travel-tab ${activeTab === "map" ? "active" : ""}`}
            onClick={() => setActiveTab("map")}
          >
            Map
          </button>
          <button
            className={`travel-tab ${activeTab === "stats" ? "active" : ""}`}
            onClick={() => setActiveTab("stats")}
          >
            Stats
          </button>
          <button
            className={`travel-tab ${activeTab === "un" ? "active" : ""}`}
            onClick={() => setActiveTab("un")}
          >
            UN Countries
          </button>
          <button
            className={`travel-tab ${activeTab === "tcc" ? "active" : ""}`}
            onClick={() => setActiveTab("tcc")}
          >
            TCC Destinations
          </button>
        </div>

        <div className="travel-tab-content">
          {activeTab === "map" && renderMap()}
          {activeTab === "stats" &&
            (statsLoading ? <p>Loading stats...</p> : renderStats())}
          {activeTab === "un" &&
            (unLoading ? <p>Loading UN countries...</p> : renderUNList())}
          {activeTab === "tcc" &&
            (tccLoading ? <p>Loading TCC destinations...</p> : renderTCCList())}
        </div>
      </div>
    </section>
  );
}
