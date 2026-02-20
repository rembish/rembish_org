import { useState, useEffect } from "react";
import { BiCurrentLocation } from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import { apiFetch } from "../lib/api";
import LocationModal from "./LocationModal";

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

function countryCodeToFlag(code: string | null): string {
  if (!code || code.length !== 2) return "";
  const codePoints = code
    .toUpperCase()
    .split("")
    .map((char) => 0x1f1e6 - 65 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default function LocationButton() {
  const { user, loading } = useAuth();
  const [currentLocation, setCurrentLocation] =
    useState<CurrentLocation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);

  useEffect(() => {
    if (!user) return;

    const fetchCurrentLocation = async () => {
      setLoadingLocation(true);
      try {
        const response = await apiFetch("/api/v1/travels/location/current");
        if (response.ok) {
          const data = await response.json();
          setCurrentLocation(data);
        }
      } catch (err) {
        console.error("Failed to fetch current location:", err);
      } finally {
        setLoadingLocation(false);
      }
    };

    fetchCurrentLocation();
  }, [user]);

  // Don't show if not logged in or still loading
  if (loading || !user) return null;

  const handleClick = () => {
    // Only admins can open the modal
    if (user.is_admin) {
      setIsModalOpen(true);
    }
  };

  const handleLocationSaved = (location: CurrentLocation) => {
    setCurrentLocation(location);
  };

  // Admin view: icon button with modal
  if (user.is_admin) {
    return (
      <>
        <button
          className="location-fab"
          onClick={handleClick}
          title="Update location"
          style={{ cursor: "pointer" }}
        >
          <BiCurrentLocation className="location-fab-icon" />
          {!loadingLocation && currentLocation && (
            <span className="location-fab-badge">
              {currentLocation.city_name}{" "}
              {countryCodeToFlag(currentLocation.country_code)}
            </span>
          )}
        </button>

        <LocationModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleLocationSaved}
        />
      </>
    );
  }

  // Non-admin view: avatar with location text
  if (!currentLocation || loadingLocation) return null;

  const flag = countryCodeToFlag(currentLocation.country_code);
  const hoverText = `${currentLocation.admin_nickname || "Admin"} has been seen in ${currentLocation.city_name} on ${formatDate(currentLocation.recorded_at)}`;

  return (
    <div className="location-widget" title={hoverText}>
      {currentLocation.admin_picture && (
        <img
          src={currentLocation.admin_picture}
          alt={currentLocation.admin_nickname || "Admin"}
          className="location-widget-avatar"
        />
      )}
      <span className="location-widget-text">
        in {currentLocation.city_name} {flag}
      </span>
    </div>
  );
}
