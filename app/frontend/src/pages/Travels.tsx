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
  BiX,
  BiTrip,
  BiBuildings,
} from "react-icons/bi";
import { FaCar } from "react-icons/fa";
import { TbDrone } from "react-icons/tb";
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

interface CityMarkerData {
  name: string;
  lat: number;
  lng: number;
  is_partial: boolean;
}

interface UNCountryData {
  name: string;
  continent: string;
  visit_date: string | null;
  visit_count: number;
  planned_count: number;
  driving_type: string | null;
  drone_flown: boolean | null;
}

interface TCCDestinationData {
  name: string;
  region: string;
  visit_date: string | null;
  visit_count: number;
  planned_count: number;
}

interface TravelStats {
  un_visited: number;
  un_total: number;
  un_planned: number;
  tcc_visited: number;
  tcc_total: number;
  tcc_planned: number;
  nm_visited: number;
  nm_total: number;
}

interface MapData {
  stats: TravelStats;
  visited_map_regions: Record<string, string>;
  visit_counts: Record<string, number>;
  region_names: Record<string, string>;
  visited_countries: string[];
  microstates: MicrostateData[];
}

interface CurrentLocation {
  city_name: string;
  lat: number;
  lng: number;
  admin_picture: string | null;
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
  is_planned: boolean;
  has_planned_trips: boolean;
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
    planned_trips: number;
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
  const [cityMarkers, setCityMarkers] = useState<CityMarkerData[]>([]);
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
  const [showOnlyVisited, setShowOnlyVisited] = useState(() => {
    const stored = localStorage.getItem("travels-show-only-visited");
    return stored !== null ? stored === "true" : true;
  });
  const [showCities, setShowCities] = useState(() => {
    const stored = localStorage.getItem("travels-show-cities");
    return stored !== null ? stored === "true" : true;
  });
  const [currentLocation, setCurrentLocation] =
    useState<CurrentLocation | null>(null);
  const [activityModal, setActivityModal] = useState<UNCountryData | null>(
    null,
  );
  const [activitySaving, setActivitySaving] = useState(false);
  const [mapViewMode, setMapViewMode] = useState<
    "visits" | "driving" | "drone"
  >("visits");
  const [statCarouselIndex, setStatCarouselIndex] = useState(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);

  const handleCarouselSwipe = (direction: "left" | "right") => {
    const totalItems = 5;
    if (direction === "left") {
      setStatCarouselIndex((prev) => (prev + 1) % totalItems);
    } else {
      setStatCarouselIndex((prev) => (prev - 1 + totalItems) % totalItems);
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStart === null) return;
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStart - touchEnd;
    if (Math.abs(diff) > 50) {
      handleCarouselSwipe(diff > 0 ? "left" : "right");
    }
    setTouchStart(null);
  };

  // Auto-advance carousel every 5 seconds on mobile
  useEffect(() => {
    const isMobile = window.innerWidth <= 600;
    if (!isMobile) return;

    const interval = setInterval(() => {
      setStatCarouselIndex((prev) => (prev + 1) % 5);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleShowOnlyVisitedChange = (checked: boolean) => {
    setShowOnlyVisited(checked);
    localStorage.setItem("travels-show-only-visited", String(checked));
  };
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

      // Fetch UN, TCC, stats, and city data in parallel
      const [unRes, tccRes, statsRes, citiesRes] = await Promise.all([
        fetch("/api/v1/travels/un-countries"),
        fetch("/api/v1/travels/tcc-destinations"),
        fetch("/api/v1/travels/stats"),
        fetch("/api/v1/travels/map-cities"),
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

      if (citiesRes.ok) {
        const citiesResult = await citiesRes.json();
        setCityMarkers(citiesResult.cities || []);
      }
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
    } catch (err) {
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

  // Fetch current location for logged-in users
  useEffect(() => {
    if (!user) {
      setCurrentLocation(null);
      return;
    }

    fetch("/api/v1/travels/location/current", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setCurrentLocation({
            city_name: data.city_name,
            lat: data.lat,
            lng: data.lng,
            admin_picture: data.admin_picture,
          });
        }
      })
      .catch(() => setCurrentLocation(null));
  }, [user]);

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

  // Lookup UN country by name for map coloring
  const unByName: Record<string, UNCountryData> = {};
  if (unData) {
    for (const c of unData) {
      unByName[c.name] = c;
    }
  }

  const getMapFillColor = (geoId: string, countryName: string): string => {
    const visitDate = mapData.visited_map_regions[geoId];
    const visitCount = mapData.visit_counts[geoId] || 0;
    const unCountry = unByName[countryName];

    if (mapViewMode === "visits") {
      return visitDate
        ? getVisitColor(visitDate, oldestDate, newestDate, visitCount)
        : "#e6e9ec";
    } else if (mapViewMode === "driving") {
      if (!unCountry?.driving_type) return "#e6e9ec";
      return unCountry.driving_type === "own" ? "#e74c3c" : "#3498db";
    } else {
      // drone
      return unCountry?.drone_flown ? "#9b59b6" : "#e6e9ec";
    }
  };

  const renderMapLegend = () => {
    if (mapViewMode === "driving") {
      return (
        <div className="map-legend">
          <div className="map-legend-item">
            <span
              className="map-legend-swatch"
              style={{ background: "#3498db" }}
            />
            <span className="map-legend-label">Rental car</span>
          </div>
          <div className="map-legend-item">
            <span
              className="map-legend-swatch"
              style={{ background: "#e74c3c" }}
            />
            <span className="map-legend-label">Own car</span>
          </div>
        </div>
      );
    }

    if (mapViewMode === "drone") {
      return (
        <div className="map-legend">
          <div className="map-legend-item">
            <span
              className="map-legend-swatch"
              style={{ background: "#9b59b6" }}
            />
            <span className="map-legend-label">Flew drone</span>
          </div>
        </div>
      );
    }

    return (
      <div className="map-legend">
        <div className="map-legend-row">
          <span className="map-legend-label">Visited once</span>
          <div
            className="map-legend-gradient"
            style={{
              background:
                "linear-gradient(to right, hsl(210, 70%, 47%), hsl(172, 70%, 47%), hsl(111, 70%, 47%), hsl(60, 70%, 47%), hsl(15, 70%, 47%))",
            }}
          />
          <span className="map-legend-label">Many visits</span>
        </div>
        <div className="map-legend-row">
          <span className="map-legend-label">Older</span>
          <div
            className="map-legend-gradient"
            style={{
              background:
                "linear-gradient(to right, hsl(210, 70%, 35%), hsl(210, 70%, 60%))",
            }}
          />
          <span className="map-legend-label">Recent</span>
        </div>
        <label className="map-legend-toggle" title="Show cities">
          <input
            type="checkbox"
            checked={showCities}
            onChange={(e) => {
              setShowCities(e.target.checked);
              localStorage.setItem(
                "travels-show-cities",
                String(e.target.checked),
              );
            }}
          />
          <span className="map-legend-toggle-label">Show cities</span>
          <BiBuildings className="map-legend-toggle-icon" />
        </label>
      </div>
    );
  };

  const renderMap = () => (
    <>
      <div
        className="travel-map-container travel-map-tall"
        onMouseLeave={() => setTooltip(null)}
      >
        <div className="map-view-toggle">
          <button
            className={`map-view-btn ${mapViewMode === "visits" ? "active" : ""}`}
            onClick={() => setMapViewMode("visits")}
          >
            Visits
          </button>
          <button
            className={`map-view-btn ${mapViewMode === "driving" ? "active" : ""}`}
            onClick={() => setMapViewMode("driving")}
          >
            Driving
          </button>
          <button
            className={`map-view-btn ${mapViewMode === "drone" ? "active" : ""}`}
            onClick={() => setMapViewMode("drone")}
          >
            Drone
          </button>
        </div>
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
                  const visitCount = mapData.visit_counts[geoId] || 0;
                  const countryName =
                    mapData.region_names[geoId] || geo.properties?.name || "";
                  const fillColor = getMapFillColor(geoId, countryName);
                  const isHighlighted = fillColor !== "#e6e9ec";
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
                          fill: isHighlighted ? "#e0c080" : "#d0d4d9",
                        },
                        pressed: { outline: "none" },
                      }}
                      onMouseEnter={(e) => {
                        setTooltip({
                          name: countryName,
                          visitCount: isHighlighted ? visitCount : undefined,
                          x: e.clientX,
                          y: e.clientY,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      onMouseMove={(e) => {
                        if (tooltip)
                          setTooltip({
                            name: countryName,
                            visitCount: isHighlighted ? visitCount : undefined,
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
              const visitCount = mapData.visit_counts[m.map_region_code] || 0;
              const fillColor = getMapFillColor(m.map_region_code, m.name);
              const isHighlighted =
                fillColor !== "#e6e9ec" && fillColor !== "#c0c4c8";
              const actualFill =
                fillColor === "#e6e9ec" ? "#c0c4c8" : fillColor;
              return (
                <Marker key={m.name} coordinates={[m.longitude, m.latitude]}>
                  <circle
                    r={1.5}
                    fill={actualFill}
                    stroke="#ffffff"
                    strokeWidth={0.3}
                    className={`microstate-marker ${isHighlighted ? "highlighted" : ""}`}
                    onMouseEnter={(e) => {
                      setTooltip({
                        name: m.name,
                        visitCount: isHighlighted ? visitCount : undefined,
                        x: e.clientX,
                        y: e.clientY,
                      });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  />
                </Marker>
              );
            })}
            {/* City markers - small dots for visited cities */}
            {mapViewMode === "visits" &&
              showCities &&
              cityMarkers.map((city, idx) => (
                <Marker key={`city-${idx}`} coordinates={[city.lng, city.lat]}>
                  <circle
                    r={0.5}
                    fill={city.is_partial ? "#999999" : "#ffffff"}
                    stroke="#333333"
                    strokeWidth={0.15}
                    style={{ cursor: "pointer" }}
                    onMouseEnter={(e) => {
                      setTooltip({
                        name: city.is_partial
                          ? `${city.name} (partial)`
                          : city.name,
                        x: e.clientX,
                        y: e.clientY,
                      });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  />
                </Marker>
              ))}
            {/* Special location markers - stars for birthplace and home */}
            <Marker coordinates={[82.9357, 55.0084]}>
              <polygon
                points="0,-2 0.59,-0.81 1.9,-0.62 0.95,0.31 1.18,1.62 0,1.05 -1.18,1.62 -0.95,0.31 -1.9,-0.62 -0.59,-0.81"
                fill="#ffd700"
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
              <polygon
                points="0,-2 0.59,-0.81 1.9,-0.62 0.95,0.31 1.18,1.62 0,1.05 -1.18,1.62 -0.95,0.31 -1.9,-0.62 -0.59,-0.81"
                fill="#ffd700"
                stroke="#333333"
                strokeWidth={0.3}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setTooltip({ name: "Home", x: e.clientX, y: e.clientY });
                }}
                onMouseLeave={() => setTooltip(null)}
              />
            </Marker>
            {/* Current location marker - only for logged-in users */}
            {user && currentLocation && (
              <Marker coordinates={[currentLocation.lng, currentLocation.lat]}>
                <g
                  style={{ cursor: "pointer" }}
                  onMouseEnter={(e) => {
                    setTooltip({
                      name: `Now: ${currentLocation.city_name}`,
                      x: e.clientX,
                      y: e.clientY,
                    });
                  }}
                  onMouseLeave={() => setTooltip(null)}
                >
                  <defs>
                    <clipPath id="avatar-clip">
                      <circle cx={0} cy={0} r={5} />
                    </clipPath>
                  </defs>
                  <circle
                    cx={0}
                    cy={0}
                    r={5.5}
                    fill="#ffffff"
                    stroke="#ffffff"
                    strokeWidth={1}
                  />
                  {currentLocation.admin_picture ? (
                    <image
                      href={currentLocation.admin_picture}
                      x={-5}
                      y={-5}
                      width={10}
                      height={10}
                      clipPath="url(#avatar-clip)"
                      preserveAspectRatio="xMidYMid slice"
                    />
                  ) : (
                    <circle cx={0} cy={0} r={5} fill="#0563bb" />
                  )}
                </g>
              </Marker>
            )}
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
        {renderMapLegend()}
      </div>
    </>
  );

  const updateCountryActivity = async (
    countryName: string,
    drivingType: string | null,
    droneFlown: boolean | null,
  ) => {
    setActivitySaving(true);
    try {
      const res = await fetch(
        `/api/v1/travels/un-countries/${encodeURIComponent(countryName)}/activities`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            driving_type: drivingType,
            drone_flown: droneFlown,
          }),
        },
      );
      if (!res.ok) throw new Error("Failed to update");

      // Update local state
      if (unData) {
        setUnData(
          unData.map((c) =>
            c.name === countryName
              ? { ...c, driving_type: drivingType, drone_flown: droneFlown }
              : c,
          ),
        );
      }
      // Update modal state too
      if (activityModal?.name === countryName) {
        setActivityModal({
          ...activityModal,
          driving_type: drivingType,
          drone_flown: droneFlown,
        });
      }
    } catch (err) {
      console.error("Failed to update country activity:", err);
    } finally {
      setActivitySaving(false);
    }
  };

  const renderActivityModal = () => {
    if (!activityModal) return null;

    return (
      <div className="modal-overlay" onClick={() => setActivityModal(null)}>
        <div
          className="modal-content modal-small"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <h2>{activityModal.name}</h2>
            <button
              className="modal-close"
              onClick={() => setActivityModal(null)}
            >
              <BiX />
            </button>
          </div>
          <div className="activity-modal-body">
            <div className="activity-option">
              <label>Driving</label>
              <div className="activity-buttons">
                <button
                  className={`activity-btn ${activityModal.driving_type === null ? "active" : ""}`}
                  disabled={activitySaving}
                  onClick={() =>
                    updateCountryActivity(
                      activityModal.name,
                      null,
                      activityModal.drone_flown,
                    )
                  }
                >
                  None
                </button>
                <button
                  className={`activity-btn rental ${activityModal.driving_type === "rental" ? "active" : ""}`}
                  disabled={activitySaving}
                  onClick={() =>
                    updateCountryActivity(
                      activityModal.name,
                      "rental",
                      activityModal.drone_flown,
                    )
                  }
                >
                  <FaCar /> Rental
                </button>
                <button
                  className={`activity-btn own ${activityModal.driving_type === "own" ? "active" : ""}`}
                  disabled={activitySaving}
                  onClick={() =>
                    updateCountryActivity(
                      activityModal.name,
                      "own",
                      activityModal.drone_flown,
                    )
                  }
                >
                  <FaCar /> Own
                </button>
              </div>
            </div>
            <div className="activity-option">
              <label>Drone</label>
              <div className="activity-buttons">
                <button
                  className={`activity-btn ${!activityModal.drone_flown ? "active" : ""}`}
                  disabled={activitySaving}
                  onClick={() =>
                    updateCountryActivity(
                      activityModal.name,
                      activityModal.driving_type,
                      null,
                    )
                  }
                >
                  No
                </button>
                <button
                  className={`activity-btn drone ${activityModal.drone_flown ? "active" : ""}`}
                  disabled={activitySaving}
                  onClick={() =>
                    updateCountryActivity(
                      activityModal.name,
                      activityModal.driving_type,
                      true,
                    )
                  }
                >
                  <TbDrone /> Yes
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderUNList = () => {
    const filteredByContinent = Object.entries(unByContinent)
      .map(
        ([continent, countries]) =>
          [
            continent,
            showOnlyVisited ? countries.filter((c) => c.visit_date) : countries,
          ] as [string, UNCountryData[]],
      )
      .filter(([, countries]) => countries.length > 0);

    return (
      <div className="travel-list">
        <div className="list-header">
          <label className="list-toggle">
            <input
              type="checkbox"
              checked={showOnlyVisited}
              onChange={(e) => handleShowOnlyVisitedChange(e.target.checked)}
            />
            <span>Visited only</span>
          </label>
          <div className="list-legend">
            <div className="list-legend-row">
              <span className="list-legend-label">Visited once</span>
              <div
                className="list-legend-gradient"
                style={{
                  background:
                    "linear-gradient(to right, hsl(210, 70%, 47%), hsl(172, 70%, 47%), hsl(111, 70%, 47%), hsl(60, 70%, 47%), hsl(15, 70%, 47%))",
                }}
              />
              <span className="list-legend-label">Many visits</span>
            </div>
            <div className="list-legend-row">
              <span className="list-legend-label">Older</span>
              <div
                className="list-legend-gradient"
                style={{
                  background:
                    "linear-gradient(to right, hsl(210, 70%, 35%), hsl(210, 70%, 60%))",
                }}
              />
              <span className="list-legend-label">Recent</span>
            </div>
            <span className="list-legend-note">Date: last visit</span>
          </div>
        </div>
        {filteredByContinent
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([continent, countries]) => {
            const allInContinent = unByContinent[continent] || [];
            const visitedCount = allInContinent.filter(
              (c) => c.visit_date,
            ).length;
            const totalCount = allInContinent.length;
            const percentage = Math.round((visitedCount / totalCount) * 100);
            return (
              <div key={continent} className="travel-list-group">
                <h3 className="travel-list-group-title">
                  {continent}
                  <span className="travel-list-group-stats">
                    {visitedCount}/{totalCount} ({percentage}%)
                  </span>
                </h3>
                <ul className="travel-list-items">
                  {countries.map((country) => {
                    const color = country.visit_date
                      ? getVisitColor(
                          country.visit_date,
                          oldestDate,
                          newestDate,
                          country.visit_count,
                        )
                      : undefined;
                    const isVisited = !!country.visit_date;
                    const isClickable = user?.is_admin && isVisited;
                    return (
                      <li
                        key={country.name}
                        className={`${isVisited ? "visited" : ""} ${isClickable ? "clickable" : ""}`}
                        style={color ? { backgroundColor: color } : undefined}
                        onClick={
                          isClickable
                            ? () => setActivityModal(country)
                            : undefined
                        }
                      >
                        <span className="country-name">
                          {country.name}
                          {country.visit_count > 0 && (
                            <span className="visit-count-badge">
                              {country.visit_count}
                            </span>
                          )}
                          {country.planned_count > 0 && (
                            <span
                              className="planned-count-badge"
                              title="In plans"
                            >
                              +{country.planned_count}
                            </span>
                          )}
                        </span>
                        <span className="country-right">
                          {/* Activity badges for visited countries */}
                          {isVisited &&
                            (country.driving_type || country.drone_flown) && (
                              <span className="activity-badges">
                                {country.driving_type && (
                                  <span
                                    className={`activity-badge driving-${country.driving_type}`}
                                    title={
                                      country.driving_type === "rental"
                                        ? "Rental car"
                                        : "Own car"
                                    }
                                  >
                                    <FaCar />
                                  </span>
                                )}
                                {country.drone_flown && (
                                  <span
                                    className="activity-badge drone"
                                    title="Flew drone"
                                  >
                                    <TbDrone />
                                  </span>
                                )}
                              </span>
                            )}
                          {country.visit_date && (
                            <span className="visit-date">
                              {formatDate(country.visit_date)}
                            </span>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
      </div>
    );
  };

  const renderTCCList = () => {
    const filteredByRegion = Object.entries(tccByRegion)
      .map(
        ([region, destinations]) =>
          [
            region,
            showOnlyVisited
              ? destinations.filter((d) => d.visit_date)
              : destinations,
          ] as [string, TCCDestinationData[]],
      )
      .filter(([, destinations]) => destinations.length > 0);

    return (
      <div className="travel-list">
        <div className="list-header">
          <label className="list-toggle">
            <input
              type="checkbox"
              checked={showOnlyVisited}
              onChange={(e) => handleShowOnlyVisitedChange(e.target.checked)}
            />
            <span>Visited only</span>
          </label>
          <div className="list-legend">
            <div className="list-legend-row">
              <span className="list-legend-label">Visited once</span>
              <div
                className="list-legend-gradient"
                style={{
                  background:
                    "linear-gradient(to right, hsl(210, 70%, 47%), hsl(172, 70%, 47%), hsl(111, 70%, 47%), hsl(60, 70%, 47%), hsl(15, 70%, 47%))",
                }}
              />
              <span className="list-legend-label">Many visits</span>
            </div>
            <div className="list-legend-row">
              <span className="list-legend-label">Older</span>
              <div
                className="list-legend-gradient"
                style={{
                  background:
                    "linear-gradient(to right, hsl(210, 70%, 35%), hsl(210, 70%, 60%))",
                }}
              />
              <span className="list-legend-label">Recent</span>
            </div>
            <span className="list-legend-note">Date: first visit</span>
          </div>
        </div>
        {filteredByRegion
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([region, destinations]) => {
            const allInRegion = tccByRegion[region] || [];
            const visitedCount = allInRegion.filter((d) => d.visit_date).length;
            const totalCount = allInRegion.length;
            const percentage = Math.round((visitedCount / totalCount) * 100);
            return (
              <div key={region} className="travel-list-group">
                <h3 className="travel-list-group-title">
                  {region}
                  <span className="travel-list-group-stats">
                    {visitedCount}/{totalCount} ({percentage}%)
                  </span>
                </h3>
                <ul className="travel-list-items">
                  {destinations.map((dest) => {
                    const color = dest.visit_date
                      ? getVisitColor(
                          dest.visit_date,
                          oldestDate,
                          newestDate,
                          dest.visit_count,
                        )
                      : undefined;
                    return (
                      <li
                        key={dest.name}
                        className={dest.visit_date ? "visited" : ""}
                        style={color ? { backgroundColor: color } : undefined}
                      >
                        <span className="country-name">
                          {dest.name}
                          {dest.visit_count > 0 && (
                            <span className="visit-count-badge">
                              {dest.visit_count}
                            </span>
                          )}
                          {dest.planned_count > 0 && (
                            <span
                              className="planned-count-badge"
                              title="In plans"
                            >
                              +{dest.planned_count}
                            </span>
                          )}
                        </span>
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
            );
          })}
      </div>
    );
  };

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
                          className={`stats-month-bar ${month.is_planned ? "stats-month-bar-planned" : month.has_planned_trips ? "stats-month-bar-mixed" : ""}`}
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
                                country.name +
                                (country.is_new ? " (first visit)" : "")
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
        <div
          className="travel-stats"
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {/* UN Countries - first in carousel */}
          <div
            className={`stat-card stat-carousel-item ${statCarouselIndex === 0 ? "active" : ""}`}
            data-index={0}
          >
            <BiWorld className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {mapData.stats.un_visited}
                {mapData.stats.un_planned > 0 && (
                  <span className="stat-planned" title="In plans">
                    +{mapData.stats.un_planned}
                  </span>
                )}
                <span className="stat-total"> of {mapData.stats.un_total}</span>
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
          {/* TCC Destinations */}
          <a
            href="https://travelerscenturyclub.org/"
            target="_blank"
            rel="noopener noreferrer"
            className={`stat-card stat-card-link stat-carousel-item ${statCarouselIndex === 1 ? "active" : ""}`}
            data-index={1}
          >
            <BiMapAlt className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {mapData.stats.tcc_visited}
                {mapData.stats.tcc_planned > 0 && (
                  <span className="stat-planned" title="In plans">
                    +{mapData.stats.tcc_planned}
                  </span>
                )}
                <span className="stat-total">
                  {" "}
                  of {mapData.stats.tcc_total}
                </span>
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
          {/* NM Regions */}
          {user?.is_admin && (
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx"
              onChange={handleUpload}
              className="nm-upload-input"
            />
          )}
          <div
            className={`stat-card stat-card-link stat-carousel-item ${statCarouselIndex === 2 ? "active" : ""} ${user?.is_admin ? "stat-card-admin" : ""}`}
            data-index={2}
            onClick={() => {
              if (user?.is_admin && window.innerWidth > 600) {
                fileInputRef.current?.click();
              } else {
                window.open("https://nomadmania.com/profile/11183/", "_blank");
              }
            }}
            title={
              user?.is_admin
                ? "Click to upload NM regions XLSX"
                : "View NomadMania profile"
            }
          >
            <BiGlobe className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {uploading ? "???" : mapData.stats.nm_visited}
                <span className="stat-total">
                  {" "}
                  of {uploading ? "???" : mapData.stats.nm_total}
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
          </div>
          {/* Trips */}
          <div
            className={`stat-card stat-carousel-item ${statCarouselIndex === 3 ? "active" : ""}`}
            data-index={3}
          >
            <BiTrip className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {statsData?.totals.trips ?? "..."}
                {(statsData?.totals.planned_trips ?? 0) > 0 && (
                  <span className="stat-planned" title="In plans">
                    +{statsData?.totals.planned_trips}
                  </span>
                )}
                <span className="stat-total"> trips</span>
              </span>
              <span className="stat-label">
                {statsData?.totals.years ?? "..."} years traveling
              </span>
            </div>
          </div>
          {/* Driving/Drone */}
          <div
            className={`stat-card stat-carousel-item ${statCarouselIndex === 4 ? "active" : ""}`}
            data-index={4}
          >
            <FaCar className="stat-icon" />
            <div className="stat-content">
              <span className="stat-number">
                {unData?.filter((c) => c.driving_type).length ?? "..."}
                <span className="stat-total"> countries driven</span>
              </span>
              <span className="stat-label">
                {unData?.filter((c) => c.drone_flown).length ?? "..."} countries
                droned
              </span>
            </div>
          </div>
          {/* Carousel dots for mobile */}
          <div className="stat-carousel-dots">
            {[0, 1, 2, 3, 4].map((i) => (
              <button
                key={i}
                className={`stat-carousel-dot ${statCarouselIndex === i ? "active" : ""}`}
                onClick={() => setStatCarouselIndex(i)}
                aria-label={`Show stat ${i + 1}`}
              />
            ))}
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
      {renderActivityModal()}
    </section>
  );
}
