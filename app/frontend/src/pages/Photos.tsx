import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
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
import { useAuth } from "../hooks/useAuth";

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

export default function Photos() {
  const { tripId: tripIdParam } = useParams<{ tripId?: string }>();
  const tripId = parseTripId(tripIdParam);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  const [indexData, setIndexData] = useState<PhotosIndexResponse | null>(null);
  const [tripData, setTripData] = useState<TripPhotosResponse | null>(null);
  const [allTrips, setAllTrips] = useState<PhotoTripSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [showHidden, setShowHidden] = useState(() => {
    return localStorage.getItem("photos-show-hidden") === "true";
  });

  // Persist showHidden to localStorage
  useEffect(() => {
    localStorage.setItem("photos-show-hidden", String(showHidden));
  }, [showHidden]);

  const [peekTrip, setPeekTrip] = useState<{
    trip: PhotoTripSummary;
    direction: "next" | "prev";
  } | null>(null);

  // Fetch index or trip data based on route
  useEffect(() => {
    setLoading(true);
    setError(null);

    // Clear peek when changing trips
    setPeekTrip(null);

    if (tripId) {
      // Fetch trip data and index (for prev/next navigation)
      Promise.all([
        fetch(`/api/v1/travels/photos/${tripId}`).then((res) => {
          if (!res.ok) throw new Error("Failed to load photos");
          return res.json();
        }),
        allTrips.length === 0
          ? fetch("/api/v1/travels/photos")
              .then((res) => res.json())
              .then((data: PhotosIndexResponse) =>
                data.years.flatMap((y) => y.trips),
              )
          : Promise.resolve(allTrips),
      ])
        .then(([tripDataResult, trips]) => {
          setTripData(tripDataResult);
          setIndexData(null);
          if (trips !== allTrips) setAllTrips(trips);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    } else {
      // Fetch index
      fetch(`/api/v1/travels/photos${showHidden ? "?show_hidden=true" : ""}`)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load photos");
          return res.json();
        })
        .then((data: PhotosIndexResponse) => {
          setIndexData(data);
          setTripData(null);
          setAllTrips(data.years.flatMap((y) => y.trips));
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId, showHidden]);

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
      }
      setPeekTrip(null);
      // Clear the URL param
      setSearchParams({}, { replace: true });
    }
  }, [tripData, searchParams, setSearchParams]);

  // Toggle trip hidden status
  const toggleHidden = async (tripIdToToggle: number) => {
    try {
      const res = await fetch(
        `/api/v1/travels/photos/${tripIdToToggle}/toggle-hidden`,
        {
          method: "POST",
          credentials: "include",
        },
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
  const setCover = async (mediaId: number) => {
    if (!tripData) return;

    try {
      const res = await fetch(
        `/api/v1/travels/photos/${tripData.trip_id}/cover/${mediaId}`,
        {
          method: "POST",
          credentials: "include",
        },
      );

      if (!res.ok) throw new Error("Failed to set cover");

      // Update local state - clear all is_cover flags and set new one
      setTripData({
        ...tripData,
        photos: tripData.photos.map((p) => ({
          ...p,
          is_cover: p.media_id === mediaId,
        })),
      });
    } catch (err) {
      console.error("Failed to set cover:", err);
    }
  };

  // Lightbox keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (lightboxIndex === null || !tripData) return;

      const photos = tripData.photos;

      // Find prev/next trips for cross-trip navigation
      const currentIndex = allTrips.findIndex(
        (t) => t.trip_id === tripData.trip_id,
      );
      const prevTrip = currentIndex > 0 ? allTrips[currentIndex - 1] : null;
      const nextTrip =
        currentIndex < allTrips.length - 1 ? allTrips[currentIndex + 1] : null;

      if (e.key === "Escape") {
        if (peekTrip) {
          setPeekTrip(null);
        } else {
          setLightboxIndex(null);
        }
      } else if (e.key === "ArrowLeft") {
        if (peekTrip?.direction === "prev") {
          // Peeking at prev trip, go there
          navigate(`/photos/${tripSlug(peekTrip.trip)}?photo=last`);
        } else if (peekTrip?.direction === "next") {
          // Peeking at next trip, cancel peek
          setPeekTrip(null);
        } else if (lightboxIndex === 0 && prevTrip) {
          // Show peek of previous trip
          setPeekTrip({ trip: prevTrip, direction: "prev" });
        } else {
          setLightboxIndex((prev) =>
            prev !== null ? (prev - 1 + photos.length) % photos.length : null,
          );
        }
      } else if (e.key === "ArrowRight") {
        if (peekTrip?.direction === "next") {
          // Peeking at next trip, go there
          navigate(`/photos/${tripSlug(peekTrip.trip)}?photo=0`);
        } else if (peekTrip?.direction === "prev") {
          // Peeking at prev trip, cancel peek
          setPeekTrip(null);
        } else if (lightboxIndex === photos.length - 1 && nextTrip) {
          // Show peek of next trip
          setPeekTrip({ trip: nextTrip, direction: "next" });
        } else {
          setLightboxIndex((prev) =>
            prev !== null ? (prev + 1) % photos.length : null,
          );
        }
      }
    },
    [lightboxIndex, tripData, allTrips, navigate, peekTrip],
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

  // Trip detail view
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
                onClick={() => navigate("/photos")}
              >
                <BiArrowBack /> Back
              </button>
              <div className="photos-trip-nav-arrows">
                <button
                  className="photos-nav-btn"
                  onClick={() =>
                    prevTrip && navigate(`/photos/${tripSlug(prevTrip)}`)
                  }
                  disabled={!prevTrip}
                  title={prevTrip?.destinations.join(", ") || ""}
                >
                  <BiChevronLeft />
                </button>
                <button
                  className="photos-nav-btn"
                  onClick={() =>
                    nextTrip && navigate(`/photos/${tripSlug(nextTrip)}`)
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
                onClick={() => setLightboxIndex(index)}
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
                      setCover(photo.media_id);
                    }}
                  >
                    {photo.is_cover ? <BiSolidStar /> : <BiStar />}
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Lightbox */}
          {lightboxIndex !== null && photos[lightboxIndex] && (
            <div
              className="photo-lightbox"
              onClick={() => setLightboxIndex(null)}
            >
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
              <button
                className="lightbox-nav lightbox-prev"
                onClick={(e) => {
                  e.stopPropagation();
                  if (peekTrip?.direction === "prev") {
                    navigate(`/photos/${tripSlug(peekTrip.trip)}?photo=last`);
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
              <div
                className="lightbox-content"
                onClick={(e) => e.stopPropagation()}
              >
                <img
                  src={`/api/v1/travels/photos/media/${photos[lightboxIndex].media_id}`}
                  alt={photos[lightboxIndex].caption || "Trip photo"}
                />
                {photos[lightboxIndex].caption && (
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
                    navigate(`/photos/${tripSlug(peekTrip.trip)}?photo=0`);
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
                  ? `${peekTrip.direction === "next" ? "→" : "←"} ${peekTrip.trip.destinations.join(", ")}`
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
                          `/photos/${tripSlug(peekTrip.trip)}?photo=last`,
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
                        navigate(`/photos/${tripSlug(peekTrip.trip)}?photo=0`);
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
          )}
        </div>
      </section>
    );
  }

  // Index view
  if (!indexData || indexData.years.length === 0) {
    return (
      <section className="photos">
        <div className="container">
          <div className="section-title">
            <h2>Photos</h2>
            <p>Trip photographs from around the world</p>
          </div>
          <p>No photos available yet.</p>
        </div>
      </section>
    );
  }

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
            Rescuing 5,000+ photos from Instagram's grid. Classification in
            progress.
          </p>
        </div>

        <div className="photos-years">
          {indexData.years.map((yearGroup) => (
            <div key={yearGroup.year} className="photos-year-group">
              <h3 className="photos-year-title">{yearGroup.year}</h3>
              <div className="photos-trips-grid">
                {yearGroup.trips.map((trip) => (
                  <article
                    key={trip.trip_id}
                    className={`trip-photo-card ${trip.is_hidden ? "is-hidden" : ""} ${isTripCurrent(trip.start_date, trip.end_date) ? "is-current" : ""}`}
                    onClick={() => navigate(`/photos/${tripSlug(trip)}`)}
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
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
