import { useEffect, useState, useCallback } from "react";
import {
  useParams,
  useNavigate,
  useSearchParams,
  useLocation,
} from "react-router-dom";
import {
  BiArrowBack,
  BiX,
  BiChevronLeft,
  BiChevronRight,
  BiStar,
  BiSolidStar,
  BiHide,
  BiShow,
  BiLogoInstagram,
} from "react-icons/bi";
import { TbDrone } from "react-icons/tb";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
  Marker,
} from "react-simple-maps";
import { useAuth } from "../hooks/useAuth";
import { apiFetch } from "../lib/api";

const geoUrl = "/world-110m.json";

/** Clean caption: merge solo flag emoji with next line, strip hashtags */
function cleanCaption(caption: string): string {
  let lines = caption.split("\n");

  // If first line is just emoji(s), merge with next line
  // Flag emojis are regional indicator pairs (U+1F1E6-1F1FF)
  const firstLine = lines[0].trim();
  const emojiOnlyPattern =
    /^[\u{1F1E6}-\u{1F1FF}\u{1F3F4}\u{E0061}-\u{E007A}\u{E007F}\s]+$/u;
  if (
    lines.length > 1 &&
    firstLine.length <= 8 &&
    emojiOnlyPattern.test(firstLine)
  ) {
    lines = [firstLine + " " + lines[1].trim(), ...lines.slice(2)];
  }

  return lines
    .filter((line) => !line.trim().match(/^#\S+(\s+#\S+)*$/))
    .join("\n")
    .replace(/#\S+/g, "")
    .trim();
}

interface PhotoTripSummary {
  trip_id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
  photo_count: number;
  thumbnail_media_id: number;
  is_hidden: boolean;
}

interface PhotosYearGroup {
  year: number;
  trips: PhotoTripSummary[];
}

interface PhotosIndexResponse {
  years: PhotosYearGroup[];
  total_photos: number;
  total_trips: number;
}

interface PhotoData {
  ig_id: string;
  media_id: number;
  caption: string | null;
  posted_at: string;
  is_aerial: boolean;
  is_cover: boolean;
  destination: string | null;
  permalink: string | null;
}

interface TripPhotosResponse {
  trip_id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
  photos: PhotoData[];
}

interface PhotoMapCountry {
  un_country_id: number;
  country_name: string;
  iso_alpha2: string;
  iso_numeric: string;
  map_region_codes: string;
  latitude: number;
  longitude: number;
  photo_count: number;
  thumbnail_media_id: number;
}

interface PhotoMapMicrostate {
  name: string;
  latitude: number;
  longitude: number;
  map_region_code: string;
}

interface PhotoMapResponse {
  countries: PhotoMapCountry[];
  microstates: PhotoMapMicrostate[];
  total_photos: number;
}

interface CountryTripGroup {
  trip_id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
  photos: PhotoData[];
}

interface CountryPhotosResponse {
  un_country_id: number;
  country_name: string;
  iso_alpha2: string;
  photo_count: number;
  trips: CountryTripGroup[];
}

/** Generate URL-friendly slug from country data */
function countrySlug(country: {
  un_country_id: number;
  country_name: string;
}): string {
  const name = country.country_name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  return `${country.un_country_id}-${name}`;
}

/** Generate URL-friendly slug from trip data */
function tripSlug(trip: PhotoTripSummary): string {
  const year = new Date(trip.start_date).getFullYear();
  const destinations = trip.destinations
    .join("-and-")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  return `${trip.trip_id}-${destinations}-${year}`;
}

/** Extract trip ID from URL param (handles both "218" and "218-spain-2026") */
function parseTripId(param: string | undefined): string | undefined {
  if (!param) return undefined;
  const match = param.match(/^(\d+)/);
  return match ? match[1] : undefined;
}

/** Check if param is a year (4-digit 2020-2099) */
function isYearParam(param: string | undefined): boolean {
  if (!param) return false;
  return /^(20[2-9]\d)$/.test(param);
}

function formatDateRange(startDate: string, endDate: string | null): string {
  const start = new Date(startDate);
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

  if (!endDate) {
    return `${months[start.getMonth()]} ${start.getDate()}, ${start.getFullYear()}`;
  }

  const end = new Date(endDate);

  if (start.getFullYear() === end.getFullYear()) {
    if (start.getMonth() === end.getMonth()) {
      return `${months[start.getMonth()]} ${start.getDate()}-${end.getDate()}, ${start.getFullYear()}`;
    }
    return `${months[start.getMonth()]} ${start.getDate()} - ${months[end.getMonth()]} ${end.getDate()}, ${start.getFullYear()}`;
  }

  return `${months[start.getMonth()]} ${start.getDate()}, ${start.getFullYear()} - ${months[end.getMonth()]} ${end.getDate()}, ${end.getFullYear()}`;
}

/** Check if a trip is currently active (today between start and end dates) */
function isTripCurrent(startDate: string, endDate: string | null): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const start = new Date(startDate);
  start.setHours(0, 0, 0, 0);
  if (today < start) return false;
  if (!endDate) return today.getTime() === start.getTime();
  const end = new Date(endDate);
  end.setHours(0, 0, 0, 0);
  return today <= end;
}

/** Get flag emoji from ISO alpha2 code */
function countryFlag(iso: string): string {
  return iso
    .toUpperCase()
    .split("")
    .map((c) => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
    .join("");
}

export default function Photos() {
  const { param, countryId: countryIdParam } = useParams<{
    param?: string;
    countryId?: string;
  }>();
  const location = useLocation();
  // Extract numeric ID from country slug (e.g. "42-spain" -> "42")
  const countryId = countryIdParam?.match(/^(\d+)/)?.[1];
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  // Determine active tab from URL
  const isMapTab = location.pathname.startsWith("/photos/map");

  // Parse param: is it a year or a trip slug?
  const selectedYear = param && isYearParam(param) ? parseInt(param, 10) : null;
  const tripId = param && !isYearParam(param) ? parseTripId(param) : undefined;

  const [indexData, setIndexData] = useState<PhotosIndexResponse | null>(null);
  const [tripData, setTripData] = useState<TripPhotosResponse | null>(null);
  const [allTrips, setAllTrips] = useState<PhotoTripSummary[]>([]);
  const [mapData, setMapData] = useState<PhotoMapResponse | null>(null);
  const [countryData, setCountryData] = useState<CountryPhotosResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [lightboxPhotos, setLightboxPhotos] = useState<PhotoData[]>([]);
  const [showHidden, setShowHidden] = useState(() => {
    return localStorage.getItem("photos-show-hidden") === "true";
  });
  const [showCaption, setShowCaption] = useState(() => {
    return localStorage.getItem("photos-show-caption") !== "false";
  });

  // Persist showHidden to localStorage
  useEffect(() => {
    localStorage.setItem("photos-show-hidden", String(showHidden));
  }, [showHidden]);

  // Persist showCaption to localStorage
  useEffect(() => {
    localStorage.setItem("photos-show-caption", String(showCaption));
  }, [showCaption]);

  const [peekTrip, setPeekTrip] = useState<{
    trip: PhotoTripSummary;
    direction: "next" | "prev";
  } | null>(null);

  // Fetch data based on route
  useEffect(() => {
    setLoading(true);
    setError(null);
    setPeekTrip(null);

    if (isMapTab && countryId) {
      // Country album view
      apiFetch(`/api/v1/travels/photos/country/${countryId}`)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load country photos");
          return res.json();
        })
        .then((data: CountryPhotosResponse) => {
          setCountryData(data);
          setTripData(null);
          setMapData(null);
          setIndexData(null);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    } else if (isMapTab) {
      // Map view
      apiFetch("/api/v1/travels/photos/map")
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load photo map");
          return res.json();
        })
        .then((data: PhotoMapResponse) => {
          setMapData(data);
          setTripData(null);
          setCountryData(null);
          setIndexData(null);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    } else if (tripId) {
      // Trip album view
      Promise.all([
        apiFetch(`/api/v1/travels/photos/${tripId}`).then((res) => {
          if (!res.ok) throw new Error("Failed to load photos");
          return res.json();
        }),
        allTrips.length === 0
          ? apiFetch("/api/v1/travels/photos")
              .then((res) => res.json())
              .then((data: PhotosIndexResponse) =>
                data.years.flatMap((y) => y.trips),
              )
          : Promise.resolve(allTrips),
      ])
        .then(([tripDataResult, trips]) => {
          setTripData(tripDataResult);
          setIndexData(null);
          setMapData(null);
          setCountryData(null);
          if (trips !== allTrips) setAllTrips(trips);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    } else {
      // Albums index
      apiFetch(`/api/v1/travels/photos${showHidden ? "?show_hidden=true" : ""}`)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load photos");
          return res.json();
        })
        .then((data: PhotosIndexResponse) => {
          setIndexData(data);
          setTripData(null);
          setMapData(null);
          setCountryData(null);
          setAllTrips(data.years.flatMap((y) => y.trips));
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId, showHidden, isMapTab, countryId]);

  // Open lightbox from URL param (for cross-trip navigation)
  useEffect(() => {
    const photoParam = searchParams.get("photo");
    if (tripData && photoParam !== null) {
      const photos = tripData.photos;
      if (photos.length > 0) {
        if (photoParam === "last") {
          setLightboxIndex(photos.length - 1);
        } else {
          const idx = parseInt(photoParam, 10);
          setLightboxIndex(isNaN(idx) ? 0 : Math.min(idx, photos.length - 1));
        }
        setLightboxPhotos(photos);
      }
      setPeekTrip(null);
      // Clear the URL param
      setSearchParams({}, { replace: true });
    }
  }, [tripData, searchParams, setSearchParams]);

  // Toggle trip hidden status
  const toggleHidden = async (tripIdToToggle: number) => {
    try {
      const res = await apiFetch(
        `/api/v1/travels/photos/${tripIdToToggle}/toggle-hidden`,
        { method: "POST" },
      );

      if (!res.ok) throw new Error("Failed to toggle hidden");

      const data = await res.json();

      // Update local state to show visual feedback
      if (indexData) {
        setIndexData({
          ...indexData,
          years: indexData.years.map((yearGroup) => ({
            ...yearGroup,
            trips: yearGroup.trips.map((trip) =>
              trip.trip_id === tripIdToToggle
                ? { ...trip, is_hidden: data.is_hidden }
                : trip,
            ),
          })),
        });

        // If hiding and not showing hidden, remove from list after delay
        if (data.is_hidden && !showHidden) {
          setTimeout(() => {
            setIndexData((prev) =>
              prev
                ? {
                    ...prev,
                    years: prev.years
                      .map((yearGroup) => ({
                        ...yearGroup,
                        trips: yearGroup.trips.filter(
                          (trip) => trip.trip_id !== tripIdToToggle,
                        ),
                      }))
                      .filter((yearGroup) => yearGroup.trips.length > 0),
                  }
                : null,
            );
          }, 500);
        }
      }
    } catch (err) {
      console.error("Failed to toggle hidden:", err);
    }
  };

  // Set cover photo
  const setCover = async (mediaId: number, coverTripId: number) => {
    try {
      const res = await apiFetch(
        `/api/v1/travels/photos/${coverTripId}/cover/${mediaId}`,
        { method: "POST" },
      );

      if (!res.ok) throw new Error("Failed to set cover");

      // Update local state - clear all is_cover flags and set new one
      if (tripData && tripData.trip_id === coverTripId) {
        setTripData({
          ...tripData,
          photos: tripData.photos.map((p) => ({
            ...p,
            is_cover: p.media_id === mediaId,
          })),
        });
      }
    } catch (err) {
      console.error("Failed to set cover:", err);
    }
  };

  // Lightbox keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (lightboxIndex === null) return;

      const photos = lightboxPhotos;

      // Find prev/next trips for cross-trip navigation (only for trip view)
      const currentIndex = tripData
        ? allTrips.findIndex((t) => t.trip_id === tripData.trip_id)
        : -1;
      const prevTrip =
        tripData && currentIndex > 0 ? allTrips[currentIndex - 1] : null;
      const nextTrip =
        tripData && currentIndex < allTrips.length - 1
          ? allTrips[currentIndex + 1]
          : null;

      if (e.key === "Escape") {
        if (peekTrip) {
          setPeekTrip(null);
        } else {
          setLightboxIndex(null);
        }
      } else if (e.key === "ArrowLeft") {
        if (peekTrip?.direction === "prev") {
          navigate(`/photos/albums/${tripSlug(peekTrip.trip)}?photo=last`);
        } else if (peekTrip?.direction === "next") {
          setPeekTrip(null);
        } else if (lightboxIndex === 0 && prevTrip) {
          setPeekTrip({ trip: prevTrip, direction: "prev" });
        } else {
          setLightboxIndex((prev) =>
            prev !== null ? (prev - 1 + photos.length) % photos.length : null,
          );
        }
      } else if (e.key === "ArrowRight") {
        if (peekTrip?.direction === "next") {
          navigate(`/photos/albums/${tripSlug(peekTrip.trip)}?photo=0`);
        } else if (peekTrip?.direction === "prev") {
          setPeekTrip(null);
        } else if (lightboxIndex === photos.length - 1 && nextTrip) {
          setPeekTrip({ trip: nextTrip, direction: "next" });
        } else {
          setLightboxIndex((prev) =>
            prev !== null ? (prev + 1) % photos.length : null,
          );
        }
      }
    },
    [lightboxIndex, lightboxPhotos, tripData, allTrips, navigate, peekTrip],
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Prevent body scroll when lightbox is open
  useEffect(() => {
    if (lightboxIndex !== null) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [lightboxIndex]);

  // Lightbox renderer (shared between trip and country views)
  const renderLightbox = (
    photos: PhotoData[],
    prevTrip: PhotoTripSummary | null,
    nextTrip: PhotoTripSummary | null,
  ) => {
    if (lightboxIndex === null || !photos[lightboxIndex]) return null;
    return (
      <div className="photo-lightbox" onClick={() => setLightboxIndex(null)}>
        <button
          className="lightbox-close"
          onClick={() => setLightboxIndex(null)}
        >
          <BiX />
        </button>
        {photos[lightboxIndex].permalink && (
          <a
            href={photos[lightboxIndex].permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="lightbox-ig-link"
            onClick={(e) => e.stopPropagation()}
            title="View on Instagram"
          >
            <BiLogoInstagram />
          </a>
        )}
        {photos[lightboxIndex].caption && (
          <button
            className="lightbox-caption-toggle"
            onClick={(e) => {
              e.stopPropagation();
              setShowCaption(!showCaption);
            }}
            title={showCaption ? "Hide caption" : "Show caption"}
          >
            {showCaption ? <BiHide /> : <BiShow />}
          </button>
        )}
        <button
          className="lightbox-nav lightbox-prev"
          onClick={(e) => {
            e.stopPropagation();
            if (peekTrip?.direction === "prev") {
              navigate(`/photos/albums/${tripSlug(peekTrip.trip)}?photo=last`);
            } else if (peekTrip?.direction === "next") {
              setPeekTrip(null);
            } else if (lightboxIndex === 0 && prevTrip) {
              setPeekTrip({ trip: prevTrip, direction: "prev" });
            } else {
              setLightboxIndex(
                (lightboxIndex - 1 + photos.length) % photos.length,
              );
            }
          }}
        >
          <BiChevronLeft />
        </button>
        <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
          <img
            src={`/api/v1/travels/photos/media/${photos[lightboxIndex].media_id}`}
            alt={photos[lightboxIndex].caption || "Trip photo"}
          />
          {photos[lightboxIndex].caption && showCaption && (
            <p className="lightbox-caption">
              {cleanCaption(photos[lightboxIndex].caption)}
            </p>
          )}
        </div>
        <button
          className="lightbox-nav lightbox-next"
          onClick={(e) => {
            e.stopPropagation();
            if (peekTrip?.direction === "next") {
              navigate(`/photos/albums/${tripSlug(peekTrip.trip)}?photo=0`);
            } else if (peekTrip?.direction === "prev") {
              setPeekTrip(null);
            } else if (lightboxIndex === photos.length - 1 && nextTrip) {
              setPeekTrip({ trip: nextTrip, direction: "next" });
            } else {
              setLightboxIndex((lightboxIndex + 1) % photos.length);
            }
          }}
        >
          <BiChevronRight />
        </button>
        <div className="lightbox-counter">
          {peekTrip
            ? `${peekTrip.direction === "next" ? "\u2192" : "\u2190"} ${peekTrip.trip.destinations.join(", ")}`
            : `${lightboxIndex + 1} / ${photos.length}`}
        </div>
        {peekTrip && (
          <div
            className="lightbox-peek"
            onClick={(e) => {
              e.stopPropagation();
              setPeekTrip(null);
            }}
          >
            <button
              className="lightbox-nav lightbox-prev"
              onClick={(e) => {
                e.stopPropagation();
                if (peekTrip.direction === "prev") {
                  navigate(
                    `/photos/albums/${tripSlug(peekTrip.trip)}?photo=last`,
                  );
                } else {
                  setPeekTrip(null);
                }
              }}
            >
              <BiChevronLeft />
            </button>
            <div className="peek-content">
              <div className="peek-info">
                <div className="peek-title">
                  {peekTrip.trip.destinations.join(", ")},{" "}
                  {new Date(peekTrip.trip.start_date).getFullYear()}
                </div>
                <div className="peek-count">
                  {peekTrip.trip.photo_count} photos
                </div>
              </div>
            </div>
            <button
              className="lightbox-nav lightbox-next"
              onClick={(e) => {
                e.stopPropagation();
                if (peekTrip.direction === "next") {
                  navigate(`/photos/albums/${tripSlug(peekTrip.trip)}?photo=0`);
                } else {
                  setPeekTrip(null);
                }
              }}
            >
              <BiChevronRight />
            </button>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <section className="photos">
        <div className="container">
          <p>Loading photos...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="photos">
        <div className="container">
          <p>Failed to load photos: {error}</p>
        </div>
      </section>
    );
  }

  // Trip detail view (from albums tab)
  if (tripData) {
    const photos = tripData.photos;

    // Find prev/next trips for navigation
    const currentIndex = allTrips.findIndex(
      (t) => t.trip_id === tripData.trip_id,
    );
    const prevTrip = currentIndex > 0 ? allTrips[currentIndex - 1] : null;
    const nextTrip =
      currentIndex < allTrips.length - 1 ? allTrips[currentIndex + 1] : null;

    return (
      <section className="photos">
        <div className="container">
          <div className="photos-trip-header">
            <div className="photos-trip-nav">
              <button
                className="photos-back-btn"
                onClick={() => {
                  const year = new Date(tripData.start_date).getFullYear();
                  navigate(`/photos/albums/${year}`);
                }}
              >
                <BiArrowBack /> Back
              </button>
              <div className="photos-trip-nav-arrows">
                <button
                  className="photos-nav-btn"
                  onClick={() =>
                    prevTrip && navigate(`/photos/albums/${tripSlug(prevTrip)}`)
                  }
                  disabled={!prevTrip}
                  title={prevTrip?.destinations.join(", ") || ""}
                >
                  <BiChevronLeft />
                </button>
                <button
                  className="photos-nav-btn"
                  onClick={() =>
                    nextTrip && navigate(`/photos/albums/${tripSlug(nextTrip)}`)
                  }
                  disabled={!nextTrip}
                  title={nextTrip?.destinations.join(", ") || ""}
                >
                  <BiChevronRight />
                </button>
              </div>
            </div>
            <h2>{tripData.destinations.join(", ")}</h2>
            <p className="photos-trip-dates">
              {formatDateRange(tripData.start_date, tripData.end_date)}
            </p>
          </div>

          <div className="photo-grid">
            {photos.map((photo, index) => (
              <div
                key={photo.media_id}
                className="photo-grid-item"
                onClick={() => {
                  setLightboxPhotos(photos);
                  setLightboxIndex(index);
                }}
              >
                <img
                  src={`/api/v1/travels/photos/media/${photo.media_id}`}
                  alt={photo.caption || "Trip photo"}
                  loading="lazy"
                />
                {photo.is_aerial && (
                  <span className="photo-aerial-badge" title="Aerial/Drone">
                    <TbDrone />
                  </span>
                )}
                {user?.is_admin && (
                  <button
                    className={`photo-cover-btn ${photo.is_cover ? "active" : ""}`}
                    title={photo.is_cover ? "Current cover" : "Set as cover"}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCover(photo.media_id, tripData.trip_id);
                    }}
                  >
                    {photo.is_cover ? <BiSolidStar /> : <BiStar />}
                  </button>
                )}
              </div>
            ))}
          </div>

          {renderLightbox(photos, prevTrip, nextTrip)}
        </div>
      </section>
    );
  }

  // Country album view (from map tab)
  if (countryData) {
    const allCountryPhotos = countryData.trips.flatMap((t) => t.photos);

    return (
      <section className="photos">
        <div className="container">
          <div className="photos-trip-header">
            <div className="photos-trip-nav">
              <button
                className="photos-back-btn"
                onClick={() => navigate("/photos/map")}
              >
                <BiArrowBack /> Back to Map
              </button>
            </div>
            <h2 className="photo-country-header">
              {countryFlag(countryData.iso_alpha2)} {countryData.country_name}
            </h2>
            <p className="photos-trip-dates">
              {countryData.photo_count} photos from {countryData.trips.length}{" "}
              trip
              {countryData.trips.length !== 1 ? "s" : ""}
            </p>
          </div>

          {countryData.trips.map((tripGroup) => (
            <div key={tripGroup.trip_id} className="photo-country-trip-group">
              {tripGroup.trip_id === 0 ? (
                <h3 className="photo-country-trip-title no-link">
                  Other photos
                  <span className="photo-country-trip-date">
                    {tripGroup.photos.length} photos
                  </span>
                </h3>
              ) : (
                <h3
                  className="photo-country-trip-title"
                  onClick={() =>
                    navigate(
                      `/photos/albums/${tripGroup.trip_id}-${tripGroup.destinations
                        .join("-and-")
                        .toLowerCase()
                        .replace(
                          /[^a-z0-9]+/g,
                          "-",
                        )}-${new Date(tripGroup.start_date).getFullYear()}`,
                    )
                  }
                >
                  {tripGroup.destinations.join(", ")}
                  <span className="photo-country-trip-date">
                    {formatDateRange(tripGroup.start_date, tripGroup.end_date)}
                  </span>
                </h3>
              )}
              <div className="photo-grid">
                {tripGroup.photos.map((photo) => {
                  const globalIndex = allCountryPhotos.findIndex(
                    (p) => p.media_id === photo.media_id,
                  );
                  return (
                    <div
                      key={photo.media_id}
                      className="photo-grid-item"
                      onClick={() => {
                        setLightboxPhotos(allCountryPhotos);
                        setLightboxIndex(globalIndex);
                      }}
                    >
                      <img
                        src={`/api/v1/travels/photos/media/${photo.media_id}`}
                        alt={photo.caption || "Photo"}
                        loading="lazy"
                      />
                      {photo.is_aerial && (
                        <span
                          className="photo-aerial-badge"
                          title="Aerial/Drone"
                        >
                          <TbDrone />
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {renderLightbox(allCountryPhotos, null, null)}
        </div>
      </section>
    );
  }

  // Map view
  if (isMapTab && mapData) {
    return (
      <section className="photos">
        <div className="container">
          <div className="section-title">
            <h2>Photos</h2>
            <p>
              {mapData.total_photos} photos from {mapData.countries.length}{" "}
              countries
            </p>
          </div>

          <div className="travel-tabs">
            <button
              className="travel-tab"
              onClick={() => navigate("/photos/albums")}
            >
              Albums
            </button>
            <button className="travel-tab active">Map</button>
          </div>

          <div className="photo-map-container">
            {(() => {
              // Build lookup: geo region code -> country for highlighting + clicks
              const regionToCountry = new Map<string, PhotoMapCountry>();
              for (const c of mapData.countries) {
                for (const code of c.map_region_codes.split(",")) {
                  regionToCountry.set(code.trim(), c);
                }
              }
              return (
                <ComposableMap
                  projection="geoMercator"
                  projectionConfig={{ scale: 140 }}
                >
                  <defs>
                    {mapData.countries.map((country) => (
                      <pattern
                        key={country.un_country_id}
                        id={`photo-fill-${country.iso_numeric}`}
                        patternUnits="objectBoundingBox"
                        patternContentUnits="objectBoundingBox"
                        width="1"
                        height="1"
                      >
                        <image
                          href={`/api/v1/travels/photos/media/${country.thumbnail_media_id}`}
                          width="1"
                          height="1"
                          preserveAspectRatio="xMidYMid slice"
                        />
                      </pattern>
                    ))}
                  </defs>
                  <ZoomableGroup center={[20, 20]} zoom={1} maxZoom={3}>
                    <Geographies geography={geoUrl}>
                      {({ geographies }) =>
                        geographies.map((geo) => {
                          const geoId = String(geo.id);
                          const country = regionToCountry.get(geoId);
                          const hasPhotos = !!country;
                          return (
                            <Geography
                              key={geo.rsmKey}
                              geography={geo}
                              fill={
                                hasPhotos
                                  ? `url(#photo-fill-${geoId})`
                                  : "#e6e9ec"
                              }
                              stroke={hasPhotos ? "#ffffff" : "#ffffff"}
                              strokeWidth={hasPhotos ? 0.8 : 0.5}
                              onClick={
                                hasPhotos
                                  ? () =>
                                      navigate(
                                        `/photos/map/${countrySlug(country)}`,
                                      )
                                  : undefined
                              }
                              style={{
                                default: {
                                  outline: "none",
                                  cursor: hasPhotos ? "pointer" : "default",
                                },
                                hover: {
                                  outline: "none",
                                  fill: hasPhotos
                                    ? `url(#photo-fill-${geoId})`
                                    : "#d0d4d9",
                                  stroke: hasPhotos ? "#fbbf24" : "#ffffff",
                                  strokeWidth: hasPhotos ? 1.5 : 0.5,
                                  cursor: hasPhotos ? "pointer" : "default",
                                },
                                pressed: { outline: "none" },
                              }}
                            />
                          );
                        })
                      }
                    </Geographies>
                    {mapData.microstates.map((m) => {
                      const country = regionToCountry.get(m.map_region_code);
                      const hasPhotos = !!country;
                      return (
                        <Marker
                          key={m.map_region_code}
                          coordinates={[m.longitude, m.latitude]}
                          onClick={
                            hasPhotos
                              ? () =>
                                  navigate(
                                    `/photos/map/${countrySlug(country)}`,
                                  )
                              : undefined
                          }
                          style={
                            hasPhotos
                              ? {
                                  default: { cursor: "pointer" },
                                  hover: { cursor: "pointer" },
                                }
                              : undefined
                          }
                        >
                          <circle
                            r={1.5}
                            fill={
                              hasPhotos ? "var(--color-primary)" : "#c0c4c8"
                            }
                            stroke="#ffffff"
                            strokeWidth={0.3}
                          />
                        </Marker>
                      );
                    })}
                  </ZoomableGroup>
                </ComposableMap>
              );
            })()}
          </div>

          <div className="photo-map-legend">
            {mapData.countries
              .slice()
              .sort((a, b) => a.country_name.localeCompare(b.country_name))
              .map((country) => (
                <button
                  key={country.un_country_id}
                  className="photo-map-legend-item"
                  onClick={() =>
                    navigate(`/photos/map/${countrySlug(country)}`)
                  }
                >
                  <span className="photo-map-legend-flag">
                    {countryFlag(country.iso_alpha2)}
                  </span>
                  <span className="photo-map-legend-name">
                    {country.country_name}
                  </span>
                  <span className="photo-map-legend-count">
                    {country.photo_count}
                  </span>
                </button>
              ))}
          </div>
        </div>
      </section>
    );
  }

  // Albums index view
  if (!indexData || indexData.years.length === 0) {
    return (
      <section className="photos">
        <div className="container">
          <div className="section-title">
            <h2>Photos</h2>
            <p>Trip photographs from around the world</p>
          </div>
          <div className="travel-tabs">
            <button className="travel-tab active">Albums</button>
            <button
              className="travel-tab"
              onClick={() => navigate("/photos/map")}
            >
              Map
            </button>
          </div>
          <p>No photos available yet.</p>
        </div>
      </section>
    );
  }

  const availableYears = indexData.years.map((y) => y.year);
  const displayYear = selectedYear ?? availableYears[0];
  const displayYearGroup = indexData.years.find((y) => y.year === displayYear);

  return (
    <section className="photos">
      <div className="container">
        <div className="section-title">
          <h2>
            Photos
            {user?.is_admin && (
              <button
                className={`photos-hidden-toggle ${showHidden ? "active" : ""}`}
                onClick={() => setShowHidden(!showHidden)}
                title={showHidden ? "Hide hidden trips" : "Show hidden trips"}
              >
                {showHidden ? <BiShow /> : <BiHide />}
              </button>
            )}
          </h2>
          <p>
            Rescuing 5,000+ photos from Instagram&apos;s grid. Classification in
            progress.
          </p>
        </div>

        <div className="travel-tabs">
          <button className="travel-tab active">Albums</button>
          <button
            className="travel-tab"
            onClick={() => navigate("/photos/map")}
          >
            Map
          </button>
        </div>

        <div className="photos-year-selector">
          {availableYears.map((year) => (
            <button
              key={year}
              className={`photos-year-pill ${year === displayYear ? "active" : ""}`}
              onClick={() =>
                navigate(
                  year === availableYears[0]
                    ? "/photos/albums"
                    : `/photos/albums/${year}`,
                )
              }
            >
              {year}
            </button>
          ))}
        </div>

        {displayYearGroup && (
          <div className="photos-trips-grid">
            {displayYearGroup.trips.map((trip) => (
              <article
                key={trip.trip_id}
                className={`trip-photo-card ${trip.is_hidden ? "is-hidden" : ""} ${isTripCurrent(trip.start_date, trip.end_date) ? "is-current" : ""}`}
                onClick={() => navigate(`/photos/albums/${tripSlug(trip)}`)}
              >
                <div className="trip-photo-thumbnail">
                  <img
                    src={`/api/v1/travels/photos/media/${trip.thumbnail_media_id}`}
                    alt={trip.destinations.join(", ")}
                    loading="lazy"
                  />
                  {user?.is_admin && (
                    <button
                      className={`trip-hide-btn ${trip.is_hidden ? "active" : ""}`}
                      title={trip.is_hidden ? "Show trip" : "Hide trip"}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleHidden(trip.trip_id);
                      }}
                    >
                      {trip.is_hidden ? <BiShow /> : <BiHide />}
                    </button>
                  )}
                </div>
                <div className="trip-photo-info">
                  <h4>{trip.destinations.join(", ")}</h4>
                  <p className="trip-photo-dates">
                    {formatDateRange(trip.start_date, trip.end_date)}
                  </p>
                  <span className="trip-photo-count">
                    {trip.photo_count} photos
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
