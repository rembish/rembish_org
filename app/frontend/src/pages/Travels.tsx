import { useEffect, useRef, useState } from "react";
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
} from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";

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
  visited_countries: string[];
  microstates: MicrostateData[];
}

// Calculate color based on visit date (older = brighter/lighter blue)
// Uses 2010 as baseline - pre-2010 visits are lightest, 2010-now has full gradient
function getVisitColor(
  visitDate: string,
  _oldestDate: Date,
  newestDate: Date,
): string {
  const date = new Date(visitDate);
  const baselineDate = new Date("2010-01-01");

  // Pre-2010 visits get the lightest color
  if (date < baselineDate) {
    return "rgb(103, 169, 224)"; // lightest blue
  }

  const totalRange = newestDate.getTime() - baselineDate.getTime();
  if (totalRange === 0) return "#0563bb";

  // Linear ratio from 2010 to newest: 0 = 2010, 1 = newest
  const ratio = (date.getTime() - baselineDate.getTime()) / totalRange;

  // Interpolate from light blue (#67a9e0) to dark blue (#0563bb)
  const lightR = 103,
    lightG = 169,
    lightB = 224;
  const darkR = 5,
    darkG = 99,
    darkB = 187;

  const r = Math.round(lightR + (darkR - lightR) * ratio);
  const g = Math.round(lightG + (darkG - lightG) * ratio);
  const b = Math.round(lightB + (darkB - lightB) * ratio);

  return `rgb(${r}, ${g}, ${b})`;
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

type TabType = "map" | "un" | "tcc";

export default function Travels() {
  const { user } = useAuth();
  // Split state for progressive loading
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [unData, setUnData] = useState<UNCountryData[] | null>(null);
  const [tccData, setTccData] = useState<TCCDestinationData[] | null>(null);
  const [mapLoading, setMapLoading] = useState(true);
  const [unLoading, setUnLoading] = useState(true);
  const [tccLoading, setTccLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{
    name: string;
    x: number;
    y: number;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("map");
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

    try {
      // Fetch map data first (shows map immediately)
      const mapRes = await fetch("/api/v1/travels/map-data");
      if (!mapRes.ok) throw new Error("Failed to fetch map data");
      const mapDataResult: MapData = await mapRes.json();
      setMapData(mapDataResult);
      setMapLoading(false);

      // Fetch UN and TCC data in parallel
      const [unRes, tccRes] = await Promise.all([
        fetch("/api/v1/travels/un-countries"),
        fetch("/api/v1/travels/tcc-destinations"),
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setMapLoading(false);
      setUnLoading(false);
      setTccLoading(false);
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
                  const isVisited = !!visitDate;
                  const fillColor = isVisited
                    ? getVisitColor(visitDate, oldestDate, newestDate)
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
                          x: e.clientX,
                          y: e.clientY,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      onMouseMove={(e) => {
                        if (tooltip)
                          setTooltip({
                            name: countryName,
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
              const isVisited = !!visitDate;
              const fillColor = isVisited
                ? getVisitColor(visitDate, oldestDate, newestDate)
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
                      setTooltip({ name: m.name, x: e.clientX, y: e.clientY });
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
                  ? getVisitColor(country.visit_date, oldestDate, newestDate)
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
                  ? getVisitColor(dest.visit_date, oldestDate, newestDate)
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

  return (
    <section id="travels" className="travels">
      <div className="container">
        <div className="travel-stats">
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
              {Math.round((mapData.stats.un_visited / mapData.stats.un_total) * 100)}%
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
          {activeTab === "un" && (unLoading ? <p>Loading UN countries...</p> : renderUNList())}
          {activeTab === "tcc" && (tccLoading ? <p>Loading TCC destinations...</p> : renderTCCList())}
        </div>
      </div>
    </section>
  );
}
