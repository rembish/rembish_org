import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { BiX, BiChevronLeft, BiChevronRight } from "react-icons/bi";
import { apiFetch } from "../lib/api";

interface CosplayPhoto {
  id: number;
  filename: string;
  width: number | null;
  height: number | null;
}

interface CosplayCostume {
  id: number;
  name: string;
  description: string | null;
  cover_photo_id: number | null;
  photos: CosplayPhoto[];
}

export default function CosplayGallery() {
  const navigate = useNavigate();
  const [costumes, setCostumes] = useState<CosplayCostume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [lightboxPhotos, setLightboxPhotos] = useState<CosplayPhoto[]>([]);

  useEffect(() => {
    apiFetch("/api/v1/travels/cosplay")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load cosplay gallery");
        return res.json();
      })
      .then((data: CosplayCostume[]) => {
        setCostumes(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const openLightbox = (photos: CosplayPhoto[], index: number) => {
    setLightboxPhotos(photos);
    setLightboxIndex(index);
  };

  const closeLightbox = () => {
    setLightboxIndex(null);
    setLightboxPhotos([]);
  };

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (lightboxIndex === null) return;
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowLeft" && lightboxIndex > 0)
        setLightboxIndex(lightboxIndex - 1);
      if (e.key === "ArrowRight" && lightboxIndex < lightboxPhotos.length - 1)
        setLightboxIndex(lightboxIndex + 1);
    },
    [lightboxIndex, lightboxPhotos.length],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
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

  if (loading)
    return (
      <section className="photos">
        <div className="container">Loading&hellip;</div>
      </section>
    );
  if (error)
    return (
      <section className="photos">
        <div className="container">Error: {error}</div>
      </section>
    );

  return (
    <section className="photos">
      <div className="container">
        <div className="section-title">
          <h2>Cosplay</h2>
          <p>Professional cosplay photoshoots</p>
        </div>

        <div className="travel-tabs">
          <button
            className="travel-tab"
            onClick={() => navigate("/photos/albums")}
          >
            Albums
          </button>
          <button
            className="travel-tab"
            onClick={() => navigate("/photos/map")}
          >
            Map
          </button>
          <button className="travel-tab active">Cosplay</button>
        </div>

        {costumes.length === 0 ? (
          <p>No cosplay photos yet.</p>
        ) : (
          <div className="photos-trips-grid">
            {costumes.map((costume) => {
              const cover = costume.cover_photo_id
                ? (costume.photos.find(
                    (p) => p.id === costume.cover_photo_id,
                  ) ?? costume.photos[0])
                : costume.photos[0];
              if (!cover) return null;
              const coverIndex = costume.photos.indexOf(cover);
              return (
                <div
                  key={costume.id}
                  className="trip-photo-card"
                  onClick={() =>
                    openLightbox(
                      costume.photos,
                      coverIndex >= 0 ? coverIndex : 0,
                    )
                  }
                >
                  <div className="trip-photo-thumbnail">
                    <img
                      src={`/api/v1/travels/cosplay/photos/${cover.id}`}
                      alt={costume.name}
                      loading="lazy"
                    />
                  </div>
                  <div className="trip-photo-info">
                    <h4>{costume.name}</h4>
                    <span className="trip-photo-count">
                      {costume.photos.length} photos
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {lightboxIndex !== null && lightboxPhotos[lightboxIndex] && (
        <div className="photo-lightbox" onClick={closeLightbox}>
          <button className="lightbox-close" onClick={closeLightbox}>
            <BiX />
          </button>
          <button
            className="lightbox-nav lightbox-prev"
            onClick={(e) => {
              e.stopPropagation();
              if (lightboxIndex > 0) setLightboxIndex(lightboxIndex - 1);
            }}
          >
            <BiChevronLeft />
          </button>
          <div
            className="lightbox-content"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={`/api/v1/travels/cosplay/photos/${lightboxPhotos[lightboxIndex].id}`}
              alt=""
            />
          </div>
          <button
            className="lightbox-nav lightbox-next"
            onClick={(e) => {
              e.stopPropagation();
              if (lightboxIndex < lightboxPhotos.length - 1)
                setLightboxIndex(lightboxIndex + 1);
            }}
          >
            <BiChevronRight />
          </button>
          <div className="lightbox-counter">
            {lightboxIndex + 1} / {lightboxPhotos.length}
          </div>
        </div>
      )}
    </section>
  );
}
