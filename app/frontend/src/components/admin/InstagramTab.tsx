import { useCallback, useEffect, useRef, useState } from "react";
import {
  BiCheck,
  BiChevronUp,
  BiChevronDown,
  BiFlag,
  BiSkipNext,
  BiTargetLock,
} from "react-icons/bi";
import { TbDrone } from "react-icons/tb";
import { apiFetch } from "../../lib/api";
import type {
  InstagramPost,
  LabelingStats,
  TCCDestinationOption,
  TripOption,
} from "./types";

export default function InstagramTab({
  initialIgId,
  onIgIdChange,
}: {
  initialIgId: string | null;
  onIgIdChange: (igId: string | null) => void;
}) {
  const [post, setPost] = useState<InstagramPost | null>(null);
  const [stats, setStats] = useState<LabelingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Navigation state (using ig_id strings)
  const [prevIgId, setPrevIgId] = useState<string | null>(null);
  const [nextIgId, setNextIgId] = useState<string | null>(null);

  // Preloaded posts cache (keyed by ig_id)
  const preloadedPosts = useRef<Map<string, InstagramPost>>(new Map());
  const preloadedImages = useRef<Set<string>>(new Set());

  // TCC options for destination selection
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);

  // Trips list for manual selection
  const [trips, setTrips] = useState<TripOption[]>([]);

  // Form state
  const [isAerial, setIsAerial] = useState<boolean>(false);
  const [isCover, setIsCover] = useState<boolean>(false);
  const [selectedTripId, setSelectedTripId] = useState<number | null>(null);
  const [selectedTccId, setSelectedTccId] = useState<number | null>(null);

  // TCC search for manual selection (when no trip)
  const [tccSearch, setTccSearch] = useState<string>("");
  const [tccSearchFocused, setTccSearchFocused] = useState<boolean>(false);
  const tccSearchInputRef = useRef<HTMLInputElement>(null);
  const labelerRef = useRef<HTMLDivElement>(null);

  const fetchStats = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/admin/instagram/stats");
      const data = await res.json();
      setStats(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  const fetchTccOptions = useCallback(() => {
    apiFetch("/api/v1/travels/tcc-options")
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
  }, []);

  const fetchTrips = useCallback((postedAt: string) => {
    const dateOnly = postedAt.split("T")[0];
    apiFetch(`/api/v1/admin/instagram/trips?before_date=${dateOnly}`)
      .then((res) => res.json())
      .then((data) => setTrips(data || []))
      .catch(() => {});
  }, []);

  // Preload a post's data and images
  const preloadPost = useCallback((igId: string) => {
    if (preloadedPosts.current.has(igId)) return;

    apiFetch(`/api/v1/admin/instagram/posts/${igId}`)
      .then((res) => res.json())
      .then((data: InstagramPost) => {
        preloadedPosts.current.set(igId, data);
        // Preload images
        for (const media of data.media) {
          const imgUrl = `/api/v1/admin/instagram/media/${media.id}`;
          if (!preloadedImages.current.has(imgUrl)) {
            const img = new Image();
            img.src = imgUrl;
            preloadedImages.current.add(imgUrl);
          }
        }
      })
      .catch(() => {});
  }, []);

  // Preload a chain of posts in the "next" direction
  const preloadChain = useCallback(
    (startIgId: string, depth: number) => {
      if (depth <= 0) return;
      apiFetch(`/api/v1/admin/instagram/posts/${startIgId}/nav`)
        .then((res) => res.json())
        .then((data) => {
          if (data.next_ig_id) {
            preloadPost(data.next_ig_id);
            // Recursive call - depth will decrease each time
            setTimeout(() => preloadChain(data.next_ig_id, depth - 1), 0);
          }
        })
        .catch(() => {});
    },
    [preloadPost],
  );

  const fetchNavigation = useCallback(
    (igId: string) => {
      apiFetch(`/api/v1/admin/instagram/posts/${igId}/nav`)
        .then((res) => res.json())
        .then((data) => {
          setPrevIgId(data.prev_ig_id);
          setNextIgId(data.next_ig_id);
          // Preload adjacent posts
          if (data.prev_ig_id) preloadPost(data.prev_ig_id);
          if (data.next_ig_id) {
            preloadPost(data.next_ig_id);
            // Preload a few more posts ahead (in the "next" direction)
            preloadChain(data.next_ig_id, 3);
          }
        })
        .catch(() => {});
    },
    [preloadPost, preloadChain],
  );

  const fetchPostByIgId = useCallback(
    (igId: string) => {
      // Check if we have this post preloaded
      const cached = preloadedPosts.current.get(igId);
      if (cached) {
        // Use cached data - instant!
        setPost(cached);
        setIsAerial(cached.is_aerial || false);
        setIsCover(cached.is_cover || false);
        // Set carousel index to cover media if editing a cover post
        const coverIdx = cached.cover_media_id
          ? cached.media.findIndex(
              (m: { id: number }) => m.id === cached.cover_media_id,
            )
          : -1;
        setCurrentImageIndex(coverIdx >= 0 ? coverIdx : 0);
        setSelectedTripId(cached.trip_id || cached.suggested_trip?.id || null);
        setSelectedTccId(cached.tcc_destination_id || null);
        // Czech Republic default is handled by effect when tccOptions loads
        setTccSearch("");
        setTccSearchFocused(false);
        onIgIdChange(igId);
        fetchNavigation(igId);
        if (cached.posted_at) {
          fetchTrips(cached.posted_at);
        }
        setLoading(false);
        // Remove from cache to allow refresh on next visit
        preloadedPosts.current.delete(igId);
        // Scroll to labeler
        setTimeout(
          () =>
            labelerRef.current?.scrollIntoView({
              behavior: "instant",
              block: "start",
            }),
          0,
        );
        return;
      }

      setLoading(true);
      apiFetch(`/api/v1/admin/instagram/posts/${igId}`)
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch post");
          return res.json();
        })
        .then((data) => {
          setPost(data);
          setIsAerial(data?.is_aerial || false);
          setIsCover(data?.is_cover || false);
          // Set carousel index to cover media if editing a cover post
          const cIdx = data?.cover_media_id
            ? data.media.findIndex(
                (m: { id: number }) => m.id === data.cover_media_id,
              )
            : -1;
          setCurrentImageIndex(cIdx >= 0 ? cIdx : 0);
          // Set trip from saved value or suggestion
          setSelectedTripId(data?.trip_id || data?.suggested_trip?.id || null);
          setSelectedTccId(data?.tcc_destination_id || null);
          // Czech Republic default is handled by effect when tccOptions loads
          setTccSearch("");
          setTccSearchFocused(false);
          onIgIdChange(igId);
          fetchNavigation(igId);
          // Fetch trips filtered by post date
          if (data?.posted_at) {
            fetchTrips(data.posted_at);
          }
          setLoading(false);
          // Scroll to labeler after loading
          setTimeout(
            () =>
              labelerRef.current?.scrollIntoView({
                behavior: "instant",
                block: "start",
              }),
            0,
          );
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    },
    [onIgIdChange, fetchNavigation, fetchTrips],
  );

  const fetchLatestPost = useCallback(() => {
    setLoading(true);
    apiFetch("/api/v1/admin/instagram/posts/latest")
      .then((res) => res.json())
      .then((igId) => {
        if (igId) {
          fetchPostByIgId(igId);
        } else {
          setPost(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [fetchPostByIgId]);

  const [fetching, setFetching] = useState(false);
  const [quotaHit, setQuotaHit] = useState(false);

  const fetchMoreFromInstagram = useCallback(async (): Promise<boolean> => {
    setFetching(true);
    try {
      const res = await apiFetch("/api/v1/admin/instagram/fetch?count=10", {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        const errMsg = err.detail || "Unknown error";
        // Detect rate limit / quota errors
        if (
          res.status === 429 ||
          errMsg.includes("timeout") ||
          errMsg.includes("limit") ||
          errMsg.includes("quota")
        ) {
          setQuotaHit(true);
          return false;
        }
        alert(`Failed to fetch: ${errMsg}`);
        return false;
      }
      const data = await res.json();
      fetchStats();
      setQuotaHit(false);
      return data.fetched > 0;
    } catch {
      setQuotaHit(true);
      return false;
    } finally {
      setFetching(false);
    }
  }, [fetchStats]);

  const [syncSuccess, setSyncSuccess] = useState(false);
  const [fillingGaps, setFillingGaps] = useState(false);
  const [fillGapsProgress, setFillGapsProgress] = useState<{
    fetched: number;
    checked: number;
    page: number;
  } | null>(null);
  const [fillGapsResult, setFillGapsResult] = useState<string | null>(null);

  const fillGaps = useCallback(() => {
    setFillingGaps(true);
    setFillGapsResult(null);
    setFillGapsProgress(null);

    const eventSource = new EventSource("/api/v1/admin/instagram/fill-gaps");

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.error) {
          eventSource.close();
          setFillingGaps(false);
          alert(`Failed to fill gaps: ${data.error}`);
          return;
        }

        setFillGapsProgress({
          fetched: data.fetched,
          checked: data.checked,
          page: data.page,
        });

        if (data.done) {
          eventSource.close();
          setFillingGaps(false);
          fetchStats();
          if (data.fetched > 0) {
            setFillGapsResult(`Found ${data.fetched} missing`);
            setTimeout(() => {
              setFillGapsResult(null);
              setFillGapsProgress(null);
            }, 5000);
          } else {
            setFillGapsResult("No gaps found");
            setTimeout(() => {
              setFillGapsResult(null);
              setFillGapsProgress(null);
            }, 3000);
          }
        }
      } catch {
        // Ignore parse errors
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setFillingGaps(false);
      setFillGapsResult("Connection lost");
      setTimeout(() => setFillGapsResult(null), 2000);
    };
  }, [fetchStats]);

  const syncNewFromInstagram = useCallback(async (): Promise<boolean> => {
    setFetching(true);
    try {
      const res = await apiFetch("/api/v1/admin/instagram/sync-new", {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Failed to sync: ${err.detail || "Unknown error"}`);
        return false;
      }
      const data = await res.json();
      fetchStats();
      if (data.fetched > 0) {
        // Navigate to the newest post (the one we just synced)
        fetchLatestPost();
        // Show success indicator briefly
        setSyncSuccess(true);
        setTimeout(() => setSyncSuccess(false), 1500);
      }
      return data.fetched > 0;
    } catch {
      alert("Failed to sync from Instagram");
      return false;
    } finally {
      setFetching(false);
    }
  }, [fetchStats, fetchLatestPost]);

  const jumpToFirstUnprocessed = useCallback(async () => {
    const res = await apiFetch(
      "/api/v1/admin/instagram/posts/first-unprocessed",
    );
    const igId = await res.json();

    if (igId) {
      fetchPostByIgId(igId);
    } else {
      // No unprocessed posts - try to fetch more from Instagram
      const fetched = await fetchMoreFromInstagram();
      if (fetched) {
        // Retry finding first unprocessed
        const retryRes = await apiFetch(
          "/api/v1/admin/instagram/posts/first-unprocessed",
        );
        const retryIgId = await retryRes.json();
        if (retryIgId) {
          fetchPostByIgId(retryIgId);
        } else {
          alert("Fetched posts but none are unprocessed (all might be videos)");
        }
      } else {
        alert("No more posts available from Instagram");
      }
    }
  }, [fetchPostByIgId, fetchMoreFromInstagram]);

  const jumpToFirstSkipped = useCallback(() => {
    apiFetch("/api/v1/admin/instagram/posts/first-skipped")
      .then((res) => res.json())
      .then((igId) => {
        if (igId) {
          fetchPostByIgId(igId);
        } else {
          alert("No skipped posts found!");
        }
      })
      .catch(() => {});
  }, [fetchPostByIgId]);

  useEffect(() => {
    fetchStats();
    fetchTccOptions();
    // Load specific post if ig_id provided, otherwise get latest
    // (fetchTrips is called after post loads with post date)
    if (initialIgId) {
      fetchPostByIgId(initialIgId);
    } else {
      fetchLatestPost();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-select TCC when trips load and selected trip has only one destination
  useEffect(() => {
    if (
      selectedTripId &&
      !selectedTccId &&
      trips.length > 0 &&
      tccOptions.length > 0
    ) {
      const trip = trips.find((t) => t.id === selectedTripId);
      if (trip && trip.destinations.length === 1) {
        const tcc = tccOptions.find((t) => t.name === trip.destinations[0]);
        if (tcc) setSelectedTccId(tcc.id);
      }
    }
  }, [trips, tccOptions, selectedTripId, selectedTccId]);

  // Default to Czech Republic when no trip is selected and tccOptions are loaded
  useEffect(() => {
    if (post && !selectedTripId && !selectedTccId && tccOptions.length > 0) {
      const czechTcc = tccOptions.find((t) => t.name === "Czech Republic");
      if (czechTcc) setSelectedTccId(czechTcc.id);
    }
  }, [post, selectedTripId, selectedTccId, tccOptions]);

  // Helper to select trip and auto-select TCC if only one destination
  // When "No trip" is selected, default to Czech Republic (home country)
  const selectTrip = useCallback(
    (tripId: number | null) => {
      setSelectedTripId(tripId);
      if (tripId) {
        const trip = trips.find((t) => t.id === tripId);
        if (trip && trip.destinations.length === 1) {
          const tcc = tccOptions.find((t) => t.name === trip.destinations[0]);
          setSelectedTccId(tcc?.id || null);
        } else {
          setSelectedTccId(null);
        }
      } else {
        // No trip = likely home country photo, default to Czech Republic
        const czechTcc = tccOptions.find((t) => t.name === "Czech Republic");
        setSelectedTccId(czechTcc?.id || null);
      }
    },
    [trips, tccOptions],
  );

  const handleLabel = useCallback(
    async (skip: boolean = false) => {
      if (!post) return;
      setSaving(true);

      const tripId = skip ? null : selectedTripId;

      try {
        const res = await apiFetch(
          `/api/v1/admin/instagram/posts/${post.ig_id}/label`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              skip,
              is_aerial: skip ? null : isAerial,
              is_cover: skip ? false : isCover,
              cover_media_id:
                !skip && isCover && post.media[currentImageIndex]
                  ? post.media[currentImageIndex].id
                  : null,
              un_country_id: null,
              tcc_destination_id: skip ? null : selectedTccId,
              trip_id: tripId,
              city_id: null,
            }),
          },
        );

        if (!res.ok) throw new Error("Failed to save label");

        const updatedStats = await fetchStats();

        // After saving, go to next post chronologically
        if (nextIgId) {
          fetchPostByIgId(nextIgId);
          // Proactively fetch more posts when running low (< 5 remaining)
          if (updatedStats && updatedStats.unlabeled < 5 && !fetching) {
            fetchMoreFromInstagram(); // Fire and forget - don't await
          }
        } else {
          // No next post - fetch more from Instagram and navigate
          const currentIgId = post.ig_id;
          const fetched = await fetchMoreFromInstagram();
          if (fetched) {
            // Re-fetch navigation to find the newly available next post
            const navRes = await apiFetch(
              `/api/v1/admin/instagram/posts/${currentIgId}/nav`,
            );
            const navData = await navRes.json();
            if (navData.next_ig_id) {
              fetchPostByIgId(navData.next_ig_id);
            } else {
              // New posts were fetched but not after this one - jump to first unprocessed
              jumpToFirstUnprocessed();
            }
          } else {
            // No posts fetched - jump to first unprocessed (might be earlier in queue)
            jumpToFirstUnprocessed();
          }
        }
      } catch (err) {
        alert(err instanceof Error ? err.message : "Failed to save");
      } finally {
        setSaving(false);
      }
    },
    [
      post,
      selectedTripId,
      isAerial,
      isCover,
      currentImageIndex,
      selectedTccId,
      nextIgId,
      fetching,
      fetchPostByIgId,
      fetchStats,
      fetchMoreFromInstagram,
      jumpToFirstUnprocessed,
    ],
  );

  const navigatePrev = useCallback(() => {
    if (prevIgId && !loading) {
      fetchPostByIgId(prevIgId);
    }
  }, [prevIgId, loading, fetchPostByIgId]);

  const navigateNext = useCallback(() => {
    if (nextIgId && !loading) {
      fetchPostByIgId(nextIgId);
    }
  }, [nextIgId, loading, fetchPostByIgId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }
      if (e.key === "Enter" && !saving && post) {
        e.preventDefault();
        handleLabel(false);
      } else if (e.key === "s" && !saving && post) {
        e.preventDefault();
        handleLabel(true);
      } else if (e.key === "d" && post) {
        e.preventDefault();
        setIsAerial((prev) => !prev);
      } else if (e.key === "c" && post) {
        e.preventDefault();
        setIsCover((prev) => !prev);
      } else if (e.key === "f") {
        // Jump to first unprocessed post
        e.preventDefault();
        jumpToFirstUnprocessed();
      } else if (e.key === "k") {
        // Jump to first skipped post
        e.preventDefault();
        jumpToFirstSkipped();
      } else if (e.key === "0") {
        // 0 = Clear trip AND TCC selection, focus search for manual entry
        e.preventDefault();
        setSelectedTripId(null);
        setSelectedTccId(null);
        setTccSearch("");
        // Focus TCC search input after state updates
        setTimeout(() => tccSearchInputRef.current?.focus(), 0);
      } else if (e.key >= "1" && e.key <= "9" && trips.length > 0) {
        // Number keys 1-9 to select trips
        const idx = parseInt(e.key) - 1;
        if (idx < trips.length) {
          e.preventDefault();
          const trip = trips[idx];
          selectTrip(selectedTripId === trip.id ? null : trip.id);
        }
      } else if (selectedTripId) {
        // QWERTY row keys to select TCC destinations
        const qwertyRow = "qwertyuiop";
        const idx = qwertyRow.indexOf(e.key.toLowerCase());
        if (idx !== -1) {
          const trip = trips.find((t) => t.id === selectedTripId);
          if (trip && idx < trip.destinations.length) {
            e.preventDefault();
            const destName = trip.destinations[idx];
            const tcc = tccOptions.find((t) => t.name === destName);
            if (tcc) {
              setSelectedTccId((prev) => (prev === tcc.id ? null : tcc.id));
            }
          }
        }
      }
      if (e.key === "ArrowUp") {
        // Navigate to newer post
        e.preventDefault();
        navigatePrev();
      } else if (e.key === "ArrowDown") {
        // Navigate to older post
        e.preventDefault();
        navigateNext();
      } else if (e.key === "ArrowLeft" && post && post.media.length > 1) {
        e.preventDefault();
        setCurrentImageIndex((prev) =>
          prev > 0 ? prev - 1 : post.media.length - 1,
        );
      } else if (e.key === "ArrowRight" && post && post.media.length > 1) {
        e.preventDefault();
        setCurrentImageIndex((prev) =>
          prev < post.media.length - 1 ? prev + 1 : 0,
        );
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    post,
    saving,
    tccOptions,
    trips,
    selectedTripId,
    jumpToFirstUnprocessed,
    jumpToFirstSkipped,
    handleLabel,
    navigatePrev,
    navigateNext,
    selectTrip,
  ]);

  // Show skeleton with spinner while loading (not blocking fetching)
  const showSpinner = loading;

  if (error) {
    return <p>Error: {error}</p>;
  }

  if (!post && !loading) {
    return (
      <div className="instagram-tab">
        <div className="instagram-stats">
          {stats && (
            <>
              <span className="stat-item">✓ {stats.labeled} labeled</span>
              <span className="stat-item">⊘ {stats.skipped} skipped</span>
              <span className="stat-item">{stats.total} total</span>
            </>
          )}
        </div>
        <div className="instagram-empty">
          <p>No posts found.</p>
        </div>
      </div>
    );
  }

  const currentMedia = post?.media[currentImageIndex];
  const postedDate = post ? new Date(post.posted_at) : null;

  return (
    <div className="instagram-tab">
      {/* Stats bar */}
      <div className="instagram-stats">
        {stats && (
          <>
            <span className="stat-item">✓ {stats.labeled} labeled</span>
            <span className="stat-item">⊘ {stats.skipped} skipped</span>
            <span className="stat-item">○ {stats.unlabeled} remaining</span>
          </>
        )}
        {fetching && (
          <span className="stat-item fetching-indicator">⏳ Fetching...</span>
        )}
        <button
          className={`btn-sync-new ${syncSuccess ? "sync-success" : ""}`}
          onClick={() => syncNewFromInstagram()}
          disabled={fetching}
          title="Sync new posts from Instagram (recent posts you've added)"
        >
          {syncSuccess ? "✓ Synced" : "↻ Sync new"}
        </button>
        <button
          className="btn-fetch-more"
          onClick={() => fetchMoreFromInstagram()}
          disabled={fetching}
          title="Fetch 10 older posts from Instagram"
        >
          + Fetch older
        </button>
        <button
          className="btn-fill-gaps"
          onClick={() => fillGaps()}
          disabled={fetching || fillingGaps}
          title="Scan for and fill missing posts between existing ones"
        >
          {fillingGaps ? "Scanning..." : "Fill gaps"}
        </button>
        <button
          className="btn-jump btn-unprocessed"
          onClick={jumpToFirstUnprocessed}
          disabled={loading}
          title="Jump to first unprocessed post"
        >
          <BiTargetLock /> Unprocessed
        </button>
        <button
          className="btn-jump btn-skipped"
          onClick={jumpToFirstSkipped}
          disabled={loading}
          title="Jump to first skipped post"
        >
          <BiFlag /> Skipped
        </button>
      </div>

      {/* Fill gaps progress indicator */}
      {(fillingGaps || fillGapsResult) && (
        <div className="fill-gaps-progress">
          {fillingGaps && fillGapsProgress && (
            <span>
              Scanning page {fillGapsProgress.page}... Found{" "}
              <strong>{fillGapsProgress.fetched}</strong> missing posts (checked{" "}
              {fillGapsProgress.checked})
            </span>
          )}
          {fillingGaps && !fillGapsProgress && <span>Starting scan...</span>}
          {!fillingGaps && fillGapsResult && (
            <span className="fill-gaps-done">{fillGapsResult}</span>
          )}
        </div>
      )}

      <div className="instagram-labeler" ref={labelerRef}>
        {/* Image section */}
        <div className="instagram-image-section">
          {quotaHit ? (
            <div className="instagram-quota-message">
              <span className="quota-icon">☕</span>
              <h3>Rate limit reached</h3>
              <p>Instagram API quota hit. Take a break!</p>
              <button
                className="btn-retry"
                onClick={() => {
                  setQuotaHit(false);
                  fetchMoreFromInstagram();
                }}
              >
                Try again
              </button>
            </div>
          ) : showSpinner ? (
            <div className="instagram-loading">
              <div className="spinner"></div>
            </div>
          ) : currentMedia ? (
            <img
              src={`/api/v1/admin/instagram/media/${currentMedia.id}`}
              alt={`Post ${post?.ig_id}`}
              className="instagram-image"
            />
          ) : null}
          {post && post.media.length > 1 && !showSpinner && !quotaHit && (
            <div className="image-nav">
              <button
                onClick={() =>
                  setCurrentImageIndex((prev) =>
                    prev > 0 ? prev - 1 : post.media.length - 1,
                  )
                }
              >
                ‹
              </button>
              <span>
                {currentImageIndex + 1} / {post.media.length}
              </span>
              <button
                onClick={() =>
                  setCurrentImageIndex((prev) =>
                    prev < post.media.length - 1 ? prev + 1 : 0,
                  )
                }
              >
                ›
              </button>
            </div>
          )}
        </div>

        {/* Info section */}
        <div className="instagram-info-section">
          {post && postedDate ? (
            <>
              <div className="post-meta">
                <span className="post-position">
                  {post.position} / {post.total}
                </span>
                <span className="post-date">
                  {postedDate.toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </span>
                <a
                  href={post.permalink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="post-link"
                >
                  View on IG ↗
                </a>
              </div>

              {post.ig_location_name && (
                <div className="post-location">📍 {post.ig_location_name}</div>
              )}

              {post.caption && (
                <div className="post-caption">{post.caption}</div>
              )}
            </>
          ) : (
            <div className="post-meta-skeleton">Loading post info...</div>
          )}

          {/* Labels form */}
          <div className="label-form">
            {/* Trip selector as radio buttons */}
            {trips.length > 0 && (
              <div className="trip-selector">
                <span className="selector-label">Trip:</span>
                <div className="trip-selector-content">
                  <div className="trip-buttons">
                    <button
                      type="button"
                      className={`trip-btn ${selectedTripId === null ? "selected" : ""}`}
                      onClick={() => selectTrip(null)}
                    >
                      <span className="trip-shortcut">0</span> None
                    </button>
                    {trips.map((trip, idx) => {
                      const isSelected = selectedTripId === trip.id;
                      const label = trip.destinations.join(", ") || "—";
                      return (
                        <button
                          key={trip.id}
                          type="button"
                          className={`trip-btn ${isSelected ? "selected" : ""}`}
                          onClick={() =>
                            selectTrip(isSelected ? null : trip.id)
                          }
                        >
                          <span className="trip-shortcut">{idx + 1}</span>{" "}
                          {label}
                        </button>
                      );
                    })}
                  </div>
                  {selectedTripId &&
                    (() => {
                      const trip = trips.find((t) => t.id === selectedTripId);
                      if (!trip) return null;
                      const start = new Date(
                        trip.start_date,
                      ).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                      });
                      const end = trip.end_date
                        ? new Date(trip.end_date).toLocaleDateString("en-GB", {
                            day: "numeric",
                            month: "short",
                          })
                        : null;
                      return (
                        <span className="trip-dates">
                          {start}
                          {end ? ` — ${end}` : ""}
                        </span>
                      );
                    })()}
                </div>
              </div>
            )}

            {/* TCC Destination selector - show selected trip's destinations */}
            {selectedTripId &&
              (() => {
                const trip = trips.find((t) => t.id === selectedTripId);
                if (!trip || trip.destinations.length === 0) return null;
                return (
                  <div className="tcc-selector">
                    <span className="selector-label">TCC:</span>
                    <div className="tcc-buttons">
                      {trip.destinations.map((destName, idx) => {
                        const tcc = tccOptions.find((t) => t.name === destName);
                        if (!tcc) return null;
                        const isSelected = selectedTccId === tcc.id;
                        return (
                          <button
                            key={tcc.id}
                            type="button"
                            className={`tcc-btn ${isSelected ? "selected" : ""}`}
                            onClick={() =>
                              setSelectedTccId(isSelected ? null : tcc.id)
                            }
                          >
                            <span className="tcc-shortcut">
                              {"qwertyuiop"[idx]}
                            </span>{" "}
                            {destName}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

            {/* TCC manual search when no trip selected */}
            {!selectedTripId && (
              <div className="tcc-search-selector">
                <span className="selector-label">TCC:</span>
                <div className="tcc-search-container">
                  {selectedTccId && !tccSearchFocused ? (
                    <div className="tcc-selected-display">
                      <span>
                        {tccOptions.find((t) => t.id === selectedTccId)?.name ||
                          "Unknown"}
                      </span>
                      <button
                        type="button"
                        className="tcc-clear-btn"
                        onClick={() => {
                          setSelectedTccId(null);
                          setTccSearch("");
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ) : (
                    <div className="tcc-autocomplete">
                      <input
                        ref={tccSearchInputRef}
                        type="text"
                        className="tcc-search-input"
                        placeholder={
                          selectedTccId
                            ? tccOptions.find((t) => t.id === selectedTccId)
                                ?.name || "Search..."
                            : "Search destination..."
                        }
                        value={tccSearch}
                        onChange={(e) => {
                          setTccSearch(e.target.value);
                          // Clear default selection when user starts typing
                          if (e.target.value && selectedTccId) {
                            setSelectedTccId(null);
                          }
                        }}
                        onFocus={() => setTccSearchFocused(true)}
                        onBlur={() =>
                          setTimeout(() => setTccSearchFocused(false), 200)
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            // If search text, select first match; otherwise keep default
                            if (tccSearch) {
                              const matches = tccOptions.filter(
                                (t) =>
                                  t.name
                                    .toLowerCase()
                                    .includes(tccSearch.toLowerCase()) ||
                                  t.region
                                    .toLowerCase()
                                    .includes(tccSearch.toLowerCase()),
                              );
                              if (matches.length > 0) {
                                setSelectedTccId(matches[0].id);
                              }
                            }
                            // Keep default (Czech Republic) if no search text
                            setTccSearch("");
                            setTccSearchFocused(false);
                            tccSearchInputRef.current?.blur();
                          } else if (e.key === "Escape") {
                            e.preventDefault();
                            setTccSearch("");
                            setTccSearchFocused(false);
                            tccSearchInputRef.current?.blur();
                          }
                        }}
                      />
                      {tccSearchFocused && tccSearch.length >= 1 && (
                        <div className="tcc-dropdown">
                          {tccOptions
                            .filter(
                              (t) =>
                                t.name
                                  .toLowerCase()
                                  .includes(tccSearch.toLowerCase()) ||
                                t.region
                                  .toLowerCase()
                                  .includes(tccSearch.toLowerCase()),
                            )
                            .slice(0, 10)
                            .map((tcc) => (
                              <button
                                key={tcc.id}
                                type="button"
                                className="tcc-dropdown-item"
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  setSelectedTccId(tcc.id);
                                  setTccSearch("");
                                  setTccSearchFocused(false);
                                }}
                              >
                                <span className="tcc-name">{tcc.name}</span>
                                <span className="tcc-region">{tcc.region}</span>
                              </button>
                            ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="photo-toggles">
              <label className="aerial-toggle">
                <input
                  type="checkbox"
                  checked={isAerial}
                  onChange={(e) => setIsAerial(e.target.checked)}
                />
                <TbDrone className="drone-icon" /> Aerial
                <span className="shortcut">(D)</span>
              </label>
              <label className="cover-toggle">
                <input
                  type="checkbox"
                  checked={isCover}
                  onChange={(e) => setIsCover(e.target.checked)}
                />
                Cover
                <span className="shortcut">(C)</span>
              </label>
            </div>
          </div>

          {/* Navigation and actions */}
          <div className="label-actions">
            <div className="nav-buttons">
              <button
                className="btn-nav"
                onClick={navigatePrev}
                disabled={!prevIgId || loading}
                title="Newer post (↑)"
              >
                <BiChevronUp />
              </button>
              <button
                className="btn-nav"
                onClick={navigateNext}
                disabled={!nextIgId || loading}
                title="Older post (↓)"
              >
                <BiChevronDown />
              </button>
            </div>
            <button
              className="btn-skip"
              onClick={() => handleLabel(true)}
              disabled={saving || loading || !post}
            >
              <BiSkipNext /> Skip <span className="shortcut">(S)</span>
            </button>
            <button
              className="btn-accept"
              onClick={() => handleLabel(false)}
              disabled={saving || loading || !post}
            >
              <BiCheck /> Save <span className="shortcut">(Enter)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
