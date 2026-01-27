import { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  CircleMarker,
  Tooltip,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { BiX } from "react-icons/bi";
import "leaflet/dist/leaflet.css";
import Flag from "./Flag";
import { useAuth } from "../hooks/useAuth";

// Fix for default marker icon in Leaflet + Vite
const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface CurrentLocation {
  city_id: number;
  city_name: string;
  country: string | null;
  country_code: string | null;
  lat: number;
  lng: number;
  recorded_at: string;
  admin_nickname: string | null;
  admin_picture: string | null;
}

interface NearbyCity {
  id: number;
  name: string;
  country: string | null;
  country_code: string | null;
  lat: number;
  lng: number;
  distance_km: number;
}

// Component to fit map bounds to all markers
function FitBounds({
  position,
  cities,
}: {
  position: { lat: number; lng: number };
  cities: NearbyCity[];
}) {
  const map = useMap();

  useEffect(() => {
    if (cities.length === 0) {
      map.setView([position.lat, position.lng], 13);
      return;
    }

    const bounds = L.latLngBounds([
      [position.lat, position.lng],
      ...cities.map((city) => [city.lat, city.lng] as [number, number]),
    ]);

    map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, position, cities]);

  return null;
}

interface ActiveTrip {
  id: number;
  start_date: string;
  end_date: string | null;
  description: string | null;
}

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (location: CurrentLocation) => void;
}

export default function LocationModal({
  isOpen,
  onClose,
  onSave,
}: LocationModalProps) {
  const { user } = useAuth();
  const [position, setPosition] = useState<{ lat: number; lng: number } | null>(
    null,
  );
  const [nearbyCities, setNearbyCities] = useState<NearbyCity[]>([]);
  const [selectedCity, setSelectedCity] = useState<number | null>(null);
  const [activeTrip, setActiveTrip] = useState<ActiveTrip | null>(null);
  const [addToTrip, setAddToTrip] = useState(true);
  const [isPartial, setIsPartial] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Reset state when modal opens
    setPosition(null);
    setNearbyCities([]);
    setSelectedCity(null);
    setAddToTrip(true);
    setIsPartial(false);
    setError(null);
    setGpsError(null);
    setLoading(true);

    // Request GPS position
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setPosition({ lat: latitude, lng: longitude });

        // Fetch nearby cities and active trip in parallel
        try {
          const [citiesRes, tripRes] = await Promise.all([
            fetch(
              `/api/v1/travels/location/nearby?lat=${latitude}&lng=${longitude}`,
              { credentials: "include" },
            ),
            fetch("/api/v1/travels/location/active-trip", {
              credentials: "include",
            }),
          ]);

          if (citiesRes.ok) {
            const citiesData = await citiesRes.json();
            setNearbyCities(citiesData.cities);
            // Pre-select first city if available
            if (citiesData.cities.length > 0) {
              setSelectedCity(citiesData.cities[0].id);
            }
          }

          if (tripRes.ok) {
            const tripData = await tripRes.json();
            setActiveTrip(tripData.trip);
          }
        } catch (err) {
          console.error("Failed to fetch location data:", err);
          setError("Failed to fetch nearby cities");
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setLoading(false);
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setGpsError("Location permission denied");
            break;
          case err.POSITION_UNAVAILABLE:
            setGpsError("Location information unavailable");
            break;
          case err.TIMEOUT:
            setGpsError("Location request timed out");
            break;
          default:
            setGpsError("An unknown error occurred");
        }
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }, [isOpen]);

  const handleSave = async () => {
    if (!position || !selectedCity) return;

    setSaving(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/travels/location/check-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          city_id: selectedCity,
          lat: position.lat,
          lng: position.lng,
          add_to_trip: addToTrip && activeTrip !== null,
          is_partial: isPartial,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to save location");
      }

      const data = await response.json();
      const city = nearbyCities.find((c) => c.id === selectedCity);

      // Call onSave with the new location data
      onSave({
        city_id: selectedCity,
        city_name: data.city_name,
        country: city?.country || null,
        country_code: city?.country_code || null,
        lat: position.lat,
        lng: position.lng,
        recorded_at: data.recorded_at,
        admin_nickname: user?.nickname || user?.name || null,
        admin_picture: user?.picture || null,
      });

      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const formatTripDates = (trip: ActiveTrip) => {
    const start = new Date(trip.start_date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    if (!trip.end_date) return `${start} - ongoing`;
    const end = new Date(trip.end_date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    return `${start} - ${end}`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content location-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Check In Location</h2>
          <button className="modal-close" onClick={onClose}>
            <BiX />
          </button>
        </div>

        <div className="location-form">
          {error && <div className="form-error">{error}</div>}

          {gpsError ? (
            <div className="location-gps-error">
              <p>{gpsError}</p>
              <p className="location-gps-hint">
                Please enable location services and try again.
              </p>
            </div>
          ) : loading ? (
            <div className="location-loading">
              <div className="location-spinner" />
              <p>Getting your location...</p>
            </div>
          ) : (
            <>
              {position && (
                <div className="location-map">
                  <MapContainer
                    center={[position.lat, position.lng]}
                    zoom={10}
                    scrollWheelZoom={false}
                    style={{ height: "100%", width: "100%" }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <FitBounds position={position} cities={nearbyCities} />
                    <Marker
                      position={[position.lat, position.lng]}
                      icon={markerIcon}
                    />
                    <Circle
                      center={[position.lat, position.lng]}
                      radius={15000}
                      pathOptions={{
                        color: "#0563bb",
                        fillColor: "#0563bb",
                        fillOpacity: 0.1,
                      }}
                    />
                    {nearbyCities.map((city) => (
                      <CircleMarker
                        key={city.id}
                        center={[city.lat, city.lng]}
                        radius={selectedCity === city.id ? 12 : 8}
                        pathOptions={{
                          color: selectedCity === city.id ? "#0563bb" : "#666",
                          fillColor:
                            selectedCity === city.id ? "#0563bb" : "#999",
                          fillOpacity: 0.7,
                          weight: selectedCity === city.id ? 3 : 2,
                        }}
                        eventHandlers={{
                          click: () => setSelectedCity(city.id),
                        }}
                      >
                        <Tooltip permanent={selectedCity === city.id}>
                          {city.name}
                        </Tooltip>
                      </CircleMarker>
                    ))}
                  </MapContainer>
                </div>
              )}

              <div className="location-cities">
                <h3>Nearby Cities</h3>
                {nearbyCities.length === 0 ? (
                  <p className="location-no-cities">
                    No cities found within 15km radius
                  </p>
                ) : (
                  <div className="location-city-list">
                    {nearbyCities.map((city) => (
                      <label key={city.id} className="location-city-item">
                        <input
                          type="radio"
                          name="city"
                          checked={selectedCity === city.id}
                          onChange={() => setSelectedCity(city.id)}
                        />
                        <span className="location-city-info">
                          {city.country_code && (
                            <Flag code={city.country_code} />
                          )}
                          <span className="location-city-name">
                            {city.name}
                          </span>
                          {city.country && (
                            <span className="location-city-country">
                              {city.country}
                            </span>
                          )}
                        </span>
                        <span className="location-city-distance">
                          {city.distance_km.toFixed(1)} km
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {activeTrip && (
                <div className="location-trip-section">
                  <label className="location-trip-checkbox">
                    <input
                      type="checkbox"
                      checked={addToTrip}
                      onChange={(e) => setAddToTrip(e.target.checked)}
                    />
                    <span>
                      Add to trip: {formatTripDates(activeTrip)}
                      {activeTrip.description && (
                        <span className="location-trip-desc">
                          {" "}
                          ({activeTrip.description})
                        </span>
                      )}
                    </span>
                  </label>

                  <label
                    className={`location-partial-checkbox ${!addToTrip ? "disabled" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={isPartial}
                      onChange={(e) => setIsPartial(e.target.checked)}
                      disabled={!addToTrip}
                    />
                    <span>Mark as partial visit</span>
                  </label>
                </div>
              )}
            </>
          )}

          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="button"
              className="btn-save"
              onClick={handleSave}
              disabled={saving || !selectedCity || loading}
            >
              {saving ? "Saving..." : "Save Location"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
