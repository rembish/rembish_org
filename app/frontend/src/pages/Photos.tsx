import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  BiArrowBack,
  BiX,
  BiChevronLeft,
  BiChevronRight,
  BiStar,
  BiSolidStar,
  BiHide,
  BiShow,
} from "react-icons/bi";
import { TbDrone } from "react-icons/tb";
import { useAuth } from "../hooks/useAuth";

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
}

interface TripPhotosResponse {
  trip_id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
  photos: PhotoData[];
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

export default function Photos() {
  const { tripId } = useParams<{ tripId?: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [indexData, setIndexData] = useState<PhotosIndexResponse | null>(null);
  const [tripData, setTripData] = useState<TripPhotosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [showHidden, setShowHidden] = useState(false);

  // Fetch index or trip data based on route
  useEffect(() => {
    setLoading(true);
    setError(null);

    const url = tripId
      ? `/api/v1/travels/photos/${tripId}`
      : `/api/v1/travels/photos${showHidden ? "?show_hidden=true" : ""}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load photos");
        return res.json();
      })
      .then((data) => {
        if (tripId) {
          setTripData(data);
          setIndexData(null);
        } else {
          setIndexData(data);
          setTripData(null);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [tripId, showHidden]);

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

      if (e.key === "Escape") {
        setLightboxIndex(null);
      } else if (e.key === "ArrowLeft") {
        setLightboxIndex((prev) =>
          prev !== null ? (prev - 1 + photos.length) % photos.length : null,
        );
      } else if (e.key === "ArrowRight") {
        setLightboxIndex((prev) =>
          prev !== null ? (prev + 1) % photos.length : null,
        );
      }
    },
    [lightboxIndex, tripData],
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

    return (
      <section className="photos">
        <div className="container">
          <div className="photos-trip-header">
            <button
              className="photos-back-btn"
              onClick={() => navigate("/photos")}
            >
              <BiArrowBack /> Back to Photos
            </button>
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
              <button
                className="lightbox-nav lightbox-prev"
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIndex(
                    (lightboxIndex - 1 + photos.length) % photos.length,
                  );
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
                    {photos[lightboxIndex].caption}
                  </p>
                )}
              </div>
              <button
                className="lightbox-nav lightbox-next"
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIndex((lightboxIndex + 1) % photos.length);
                }}
              >
                <BiChevronRight />
              </button>
              <div className="lightbox-counter">
                {lightboxIndex + 1} / {photos.length}
              </div>
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
          <h2>Photos</h2>
          <p>
            Rescuing 5,000+ photos from Instagram's grid. Classification in
            progress.
          </p>
        </div>

        {user?.is_admin && (
          <div className="photos-admin-controls">
            <label className="photos-show-hidden">
              <input
                type="checkbox"
                checked={showHidden}
                onChange={(e) => setShowHidden(e.target.checked)}
              />
              Show hidden trips
            </label>
          </div>
        )}

        <div className="photos-years">
          {indexData.years.map((yearGroup) => (
            <div key={yearGroup.year} className="photos-year-group">
              <h3 className="photos-year-title">{yearGroup.year}</h3>
              <div className="photos-trips-grid">
                {yearGroup.trips.map((trip) => (
                  <article
                    key={trip.trip_id}
                    className={`trip-photo-card ${trip.is_hidden ? "is-hidden" : ""}`}
                    onClick={() => navigate(`/photos/${trip.trip_id}`)}
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
