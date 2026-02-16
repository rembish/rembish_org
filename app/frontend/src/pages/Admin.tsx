import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import {
  BiBriefcase,
  BiCake,
  BiCalendar,
  BiCar,
  BiChevronLeft,
  BiChevronRight,
  BiChevronUp,
  BiChevronDown,
  BiPaperPlane,
  BiParty,
  BiPlus,
  BiPencil,
  BiTable,
  BiTrash,
  BiCheck,
  BiSkipNext,
  BiTargetLock,
  BiFlag,
} from "react-icons/bi";
import { TbDrone } from "react-icons/tb";
import { useAuth } from "../hooks/useAuth";
import TripFormModal, { TripFormData } from "../components/TripFormModal";
import UserFormModal, { UserFormData } from "../components/UserFormModal";

interface TripDestination {
  name: string;
  is_partial: boolean;
}

interface TripCity {
  name: string;
  is_partial: boolean;
}

interface TripParticipant {
  id: number;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

interface Trip {
  id: number;
  start_date: string;
  end_date: string | null;
  trip_type: "regular" | "work" | "relocation";
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  destinations: TripDestination[];
  cities: TripCity[];
  participants: TripParticipant[];
  other_participants_count: number | null;
}

interface TripsResponse {
  trips: Trip[];
  total: number;
}

interface TCCDestinationOption {
  id: number;
  name: string;
  region: string;
  country_code: string | null;
}

interface Holiday {
  date: string;
  name: string;
  local_name: string | null;
  country_code?: string;
}

interface UserBirthday {
  date: string; // MM-DD format
  name: string;
}

type AdminTab = "trips" | "close-ones" | "instagram";

// Instagram labeling types
interface InstagramMedia {
  id: number;
  media_type: string;
  storage_path: string | null;
  order: number;
}

interface InstagramPost {
  id: number; // DB id (for media endpoints)
  ig_id: string; // Instagram ID (for routing)
  caption: string | null;
  media_type: string;
  posted_at: string;
  permalink: string;
  ig_location_name: string | null;
  ig_location_lat: number | null;
  ig_location_lng: number | null;
  media: InstagramMedia[];
  position: number;
  total: number;
  un_country_id: number | null;
  tcc_destination_id: number | null;
  trip_id: number | null;
  city_id: number | null;
  is_aerial: boolean | null;
  is_cover: boolean;
  cover_media_id: number | null;
  suggested_trip: {
    id: number;
    start_date: string;
    end_date: string | null;
    destinations: string[];
  } | null;
  previous_labels: {
    un_country_id: number | null;
    un_country_name: string | null;
    tcc_destination_id: number | null;
    tcc_destination_name: string | null;
    trip_id: number | null;
    city_id: number | null;
    city_name: string | null;
    is_aerial: boolean | null;
  } | null;
}

interface LabelingStats {
  total: number;
  labeled: number;
  skipped: number;
  unlabeled: number;
}

interface TripOption {
  id: number;
  start_date: string;
  end_date: string | null;
  destinations: string[];
}

interface CloseOneUser {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
  birthday: string | null;
  is_admin: boolean;
  is_active: boolean;
  trips_count: number;
}

function CloseOnesTab() {
  const [users, setUsers] = useState<CloseOneUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<CloseOneUser | null>(null);

  const fetchUsers = useCallback(() => {
    fetch("/api/v1/admin/users/", { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch users");
        return res.json();
      })
      .then((data) => {
        setUsers(data.users || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleAddUser = () => {
    setEditingUser(null);
    setModalOpen(true);
  };

  const handleEditUser = (user: CloseOneUser) => {
    setEditingUser(user);
    setModalOpen(true);
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("Are you sure you want to remove this user?")) return;

    try {
      const res = await fetch(`/api/v1/admin/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete user");
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  const handleSaveUser = async (data: UserFormData) => {
    const url = editingUser
      ? `/api/v1/admin/users/${editingUser.id}`
      : "/api/v1/admin/users/";
    const method = editingUser ? "PUT" : "POST";

    // Convert empty strings to null for optional fields
    const payload = {
      ...data,
      birthday: data.birthday || null,
    };

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      let message = "Failed to save user";
      if (typeof errorData.detail === "string") {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        message = errorData.detail
          .map((e: { msg: string }) => e.msg)
          .join(", ");
      }
      throw new Error(message);
    }

    fetchUsers();
  };

  const getInitialFormData = (): UserFormData | null => {
    if (!editingUser) return null;
    return {
      email: editingUser.email,
      name: editingUser.name || "",
      nickname: editingUser.nickname || "",
      birthday: editingUser.birthday || "",
    };
  };

  if (loading) {
    return <p>Loading users...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  return (
    <div className="close-ones-tab">
      <div className="close-ones-header">
        <button className="btn-add-user" onClick={handleAddUser}>
          <BiPlus /> Add User
        </button>
      </div>

      <div className="users-grid">
        {users.length === 0 ? (
          <p className="no-users">No close ones added yet.</p>
        ) : (
          users.map((user) => (
            <div key={user.id} className="user-card">
              <div className="user-card-avatar">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.nickname || user.name || ""}
                  />
                ) : (
                  <span className="avatar-initial">
                    {(user.nickname ||
                      user.name ||
                      user.email)[0].toUpperCase()}
                  </span>
                )}
              </div>
              <div className="user-card-info">
                <div className="user-card-name">
                  {user.nickname || user.name || "—"}
                  {user.is_admin && <span className="admin-badge">Admin</span>}
                  <span
                    className={`status-badge ${user.is_active ? "active" : "pending"}`}
                  >
                    {user.is_active ? "Active" : "Pending"}
                  </span>
                </div>
                <div className="user-card-email">{user.email}</div>
                <div className="user-card-meta">
                  {user.birthday && (
                    <span className="birthday-badge">
                      <BiCake />{" "}
                      {new Date(user.birthday + "T00:00:00").toLocaleDateString(
                        "en-GB",
                        { day: "numeric", month: "short" },
                      )}
                    </span>
                  )}
                  {user.trips_count > 0 && (
                    <span className="trips-badge">
                      {user.trips_count} trip{user.trips_count !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <div className="user-card-actions">
                <button
                  className="user-action-btn"
                  onClick={() => handleEditUser(user)}
                  title="Edit"
                >
                  <BiPencil />
                </button>
                <button
                  className="user-action-btn delete"
                  onClick={() => handleDeleteUser(user.id)}
                  title="Remove"
                >
                  <BiTrash />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <UserFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveUser}
        initialData={getInitialFormData()}
        title={editingUser ? "Edit User" : "Add User"}
      />
    </div>
  );
}

function InstagramTab({
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
      const res = await fetch("/api/v1/admin/instagram/stats", {
        credentials: "include",
      });
      const data = await res.json();
      setStats(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  const fetchTccOptions = useCallback(() => {
    fetch("/api/v1/travels/tcc-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
  }, []);

  const fetchTrips = useCallback((postedAt: string) => {
    const dateOnly = postedAt.split("T")[0];
    fetch(`/api/v1/admin/instagram/trips?before_date=${dateOnly}`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setTrips(data || []))
      .catch(() => {});
  }, []);

  // Preload a post's data and images
  const preloadPost = useCallback((igId: string) => {
    if (preloadedPosts.current.has(igId)) return;

    fetch(`/api/v1/admin/instagram/posts/${igId}`, { credentials: "include" })
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
      fetch(`/api/v1/admin/instagram/posts/${startIgId}/nav`, {
        credentials: "include",
      })
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
      fetch(`/api/v1/admin/instagram/posts/${igId}/nav`, {
        credentials: "include",
      })
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
      fetch(`/api/v1/admin/instagram/posts/${igId}`, {
        credentials: "include",
      })
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
    fetch("/api/v1/admin/instagram/posts/latest", { credentials: "include" })
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
      const res = await fetch("/api/v1/admin/instagram/fetch?count=10", {
        method: "POST",
        credentials: "include",
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
      const res = await fetch("/api/v1/admin/instagram/sync-new", {
        method: "POST",
        credentials: "include",
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
    const res = await fetch("/api/v1/admin/instagram/posts/first-unprocessed", {
      credentials: "include",
    });
    const igId = await res.json();

    if (igId) {
      fetchPostByIgId(igId);
    } else {
      // No unprocessed posts - try to fetch more from Instagram
      const fetched = await fetchMoreFromInstagram();
      if (fetched) {
        // Retry finding first unprocessed
        const retryRes = await fetch(
          "/api/v1/admin/instagram/posts/first-unprocessed",
          { credentials: "include" },
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
    fetch("/api/v1/admin/instagram/posts/first-skipped", {
      credentials: "include",
    })
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
        const res = await fetch(
          `/api/v1/admin/instagram/posts/${post.ig_id}/label`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
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
            const navRes = await fetch(
              `/api/v1/admin/instagram/posts/${currentIgId}/nav`,
              { credentials: "include" },
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

// Check if trip overlaps with a given year (for NY trips spanning Dec-Jan)
function tripOverlapsYear(trip: Trip, year: number): boolean {
  const startYear = new Date(trip.start_date).getFullYear();
  const endYear = trip.end_date
    ? new Date(trip.end_date).getFullYear()
    : startYear;
  return year >= startYear && year <= endYear;
}

// Build a map of TCC destination -> first visit date (across all trips)
function buildFirstVisitMap(trips: Trip[]): Map<string, string> {
  const firstVisit = new Map<string, string>();
  // Sort trips by date ascending to find first visits
  const sorted = [...trips].sort(
    (a, b) =>
      new Date(a.start_date).getTime() - new Date(b.start_date).getTime(),
  );
  for (const trip of sorted) {
    for (const dest of trip.destinations) {
      if (!firstVisit.has(dest.name)) {
        firstVisit.set(dest.name, trip.start_date);
      }
    }
  }
  return firstVisit;
}

// Build a map of TCC destination -> first visit date within a specific year
function buildFirstVisitInYearMap(
  trips: Trip[],
  year: number,
): Map<string, string> {
  const firstVisit = new Map<string, string>();
  const yearTrips = trips
    .filter((t) => tripOverlapsYear(t, year))
    .sort(
      (a, b) =>
        new Date(a.start_date).getTime() - new Date(b.start_date).getTime(),
    );

  for (const trip of yearTrips) {
    for (const dest of trip.destinations) {
      if (!firstVisit.has(dest.name)) {
        firstVisit.set(dest.name, trip.start_date);
      }
    }
  }
  return firstVisit;
}

// Get all years that have trips (including overlapping)
function getYearsWithTrips(trips: Trip[]): number[] {
  const years = new Set<number>();
  for (const trip of trips) {
    const startYear = new Date(trip.start_date).getFullYear();
    const endYear = trip.end_date
      ? new Date(trip.end_date).getFullYear()
      : startYear;
    for (let y = startYear; y <= endYear; y++) {
      years.add(y);
    }
  }
  return Array.from(years).sort((a, b) => b - a);
}

// Format date as "D Mon" or "D Mon - D Mon" for ranges
function formatDateRange(startDate: string, endDate: string | null): string {
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
  const start = new Date(startDate);
  const startStr = `${start.getDate()} ${months[start.getMonth()]}`;

  if (!endDate) return startStr;

  const end = new Date(endDate);
  const endStr = `${end.getDate()} ${months[end.getMonth()]}`;

  // Include year if different
  const startYear = start.getFullYear();
  const endYear = end.getFullYear();

  if (startYear !== endYear) {
    return `${start.getDate()} ${months[start.getMonth()]} ${startYear} – ${end.getDate()} ${months[end.getMonth()]} ${endYear}`;
  }

  if (startStr === endStr) return startStr;
  return `${startStr} – ${endStr}`;
}

// Calculate trip duration in days
function getDuration(startDate: string, endDate: string | null): number {
  const start = new Date(startDate);
  const end = endDate ? new Date(endDate) : start;
  return (
    Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1
  );
}

// Check if trip is in the future (not yet completed)
function isFutureTrip(trip: Trip): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const endDate = trip.end_date
    ? new Date(trip.end_date)
    : new Date(trip.start_date);
  return endDate > today;
}

// Get all dates in a trip's range
function getTripDateRange(trip: Trip): string[] {
  const dates: string[] = [];
  const start = new Date(trip.start_date + "T00:00:00");
  const end = trip.end_date
    ? new Date(trip.end_date + "T00:00:00")
    : new Date(trip.start_date + "T00:00:00");
  const current = new Date(start);
  while (current <= end) {
    const y = current.getFullYear();
    const m = String(current.getMonth() + 1).padStart(2, "0");
    const d = String(current.getDate()).padStart(2, "0");
    dates.push(`${y}-${m}-${d}`);
    current.setDate(current.getDate() + 1);
  }
  return dates;
}

// Get holidays that match a trip's destinations and date range
function getTripHolidays(
  trip: Trip,
  holidays: Holiday[],
  tccOptions: TCCDestinationOption[],
): Holiday[] {
  // Get country codes from trip destinations
  const tripCountryCodes = new Set<string>();
  for (const dest of trip.destinations) {
    const tcc = tccOptions.find((o) => o.name === dest.name);
    if (tcc?.country_code) tripCountryCodes.add(tcc.country_code);
  }
  if (tripCountryCodes.size === 0) return [];

  // Get all dates in trip range
  const tripDates = new Set(getTripDateRange(trip));

  // Find holidays that match both date and country
  return holidays.filter(
    (h) =>
      tripDates.has(h.date) &&
      h.country_code &&
      tripCountryCodes.has(h.country_code),
  );
}

interface YearCalendarViewProps {
  year: number;
  trips: Trip[];
  holidays: Holiday[];
  czechHolidays: Holiday[];
  birthdays: UserBirthday[];
  onDateClick: (date: string, trip?: Trip) => void;
  tccOptions: TCCDestinationOption[];
}

function YearCalendarView({
  year,
  trips,
  holidays,
  czechHolidays,
  birthdays,
  onDateClick,
  tccOptions,
}: YearCalendarViewProps) {
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // Build lookup maps for quick access
  // Holiday map: date -> list of holidays (can have multiple countries)
  const holidayMap = new Map<string, Holiday[]>();
  for (const h of holidays) {
    if (!holidayMap.has(h.date)) holidayMap.set(h.date, []);
    holidayMap.get(h.date)!.push(h);
  }

  // Helper to get country codes for a trip's destinations
  const getTripCountryCodes = (trip: Trip): Set<string> => {
    const codes = new Set<string>();
    for (const dest of trip.destinations) {
      const tcc = tccOptions.find((o) => o.name === dest.name);
      if (tcc?.country_code) codes.add(tcc.country_code);
    }
    return codes;
  };

  // Helper to find holidays matching trip's destination countries
  const getMatchingHolidays = (
    trip: Trip,
    dateHolidays: Holiday[],
  ): Holiday[] => {
    const tripCodes = getTripCountryCodes(trip);
    return dateHolidays.filter(
      (h) => h.country_code && tripCodes.has(h.country_code),
    );
  };

  const birthdayMap = new Map<string, UserBirthday[]>();
  for (const b of birthdays) {
    const key = `${year}-${b.date}`; // YYYY-MM-DD
    if (!birthdayMap.has(key)) birthdayMap.set(key, []);
    birthdayMap.get(key)!.push(b);
  }

  // Czech holiday map: date -> holiday name (for background coloring)
  const czechHolidayMap = new Map<string, string>();
  for (const h of czechHolidays) {
    czechHolidayMap.set(h.date, h.local_name || h.name);
  }

  // Format date as YYYY-MM-DD in local time (for trip iteration)
  const toLocalDateStr = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  };

  // Build trip date ranges
  const tripDates = new Map<string, Trip[]>();
  for (const trip of trips) {
    const start = new Date(trip.start_date + "T00:00:00");
    const end = trip.end_date
      ? new Date(trip.end_date + "T00:00:00")
      : new Date(trip.start_date + "T00:00:00");
    const current = new Date(start);
    while (current <= end) {
      const dateStr = toLocalDateStr(current);
      if (!tripDates.has(dateStr)) tripDates.set(dateStr, []);
      tripDates.get(dateStr)!.push(trip);
      current.setDate(current.getDate() + 1);
    }
  }

  const isWeekend = (date: Date) => {
    const day = date.getDay();
    return day === 0 || day === 6;
  };

  const getDaysInMonth = (month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month: number) => {
    // Returns 0-6 (Mon=0 to Sun=6)
    const day = new Date(year, month, 1).getDay();
    return day === 0 ? 6 : day - 1;
  };

  const getTripClass = (trip: Trip) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const endDate = trip.end_date
      ? new Date(trip.end_date)
      : new Date(trip.start_date);
    const isFuture = endDate > today;
    if (isFuture) return "future";
    if (trip.trip_type === "work") return "work";
    return "regular";
  };

  const renderMonth = (month: number) => {
    const daysInMonth = getDaysInMonth(month);
    const firstDay = getFirstDayOfMonth(month);
    const days: JSX.Element[] = [];

    // Empty cells for days before the 1st
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty" />);
    }

    // Today for future trip check
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Day cells
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = toLocalDateStr(date);
      const dayTrips = tripDates.get(dateStr) || [];
      const dateHolidays = holidayMap.get(dateStr) || [];
      const dayBirthdays = birthdayMap.get(dateStr);
      const czechHoliday = czechHolidayMap.get(dateStr);
      const weekend = isWeekend(date);

      // Check if trip overlaps with destination country holiday (only for future trips)
      const trip = dayTrips.length > 0 ? dayTrips[0] : null;
      const isFuture =
        trip &&
        (trip.end_date ? new Date(trip.end_date) : new Date(trip.start_date)) >
          today;
      const matchingHolidays = trip
        ? getMatchingHolidays(trip, dateHolidays)
        : [];
      const hasTripOnHoliday = isFuture && matchingHolidays.length > 0;

      // Check if trip overlaps with a birthday (for all trips, not just future)
      const hasTripOnBirthday = trip && dayBirthdays && dayBirthdays.length > 0;

      // Priority: trip > birthday > czech-holiday > weekend
      const classes = ["calendar-day"];
      let title = "";

      if (trip) {
        classes.push("trip", getTripClass(trip));

        // Check if start/end for border radius
        if (trip.start_date === dateStr) classes.push("trip-start");
        if ((trip.end_date || trip.start_date) === dateStr)
          classes.push("trip-end");

        // Build tooltip with destinations, holidays, and birthdays
        const destNames = trip.destinations.map((d) => d.name).join(", ");
        const parts = [destNames || "Trip"];
        if (hasTripOnHoliday) {
          parts.push(matchingHolidays.map((h) => h.name).join(", "));
        }
        if (hasTripOnBirthday) {
          parts.push(
            dayBirthdays!.map((b) => `${b.name}'s birthday`).join(", "),
          );
        }
        title = parts.join(" - ");
      } else if (dayBirthdays && dayBirthdays.length > 0) {
        classes.push("birthday");
        title = dayBirthdays.map((b) => `${b.name}'s birthday`).join(", ");
      } else if (czechHoliday) {
        classes.push("czech-holiday");
        title = czechHoliday;
      } else if (weekend) {
        classes.push("weekend");
      }

      days.push(
        <div
          key={day}
          className={classes.join(" ")}
          title={title}
          onClick={() =>
            onDateClick(dateStr, dayTrips.length > 0 ? dayTrips[0] : undefined)
          }
        >
          {day}
          {hasTripOnBirthday && <BiCake className="day-icon day-icon-left" />}
          {hasTripOnHoliday && <BiParty className="day-icon day-icon-right" />}
        </div>,
      );
    }

    return (
      <div key={month} className="calendar-month">
        <div className="calendar-month-header">{monthNames[month]}</div>
        <div className="calendar-days-header">
          {weekDays.map((d) => (
            <div key={d}>{d}</div>
          ))}
        </div>
        <div className="calendar-days">{days}</div>
      </div>
    );
  };

  return (
    <div className="year-calendar">
      {Array.from({ length: 12 }, (_, i) => renderMonth(i))}
    </div>
  );
}

function TripsTab({
  selectedYear,
  onYearChange,
}: {
  selectedYear: number | null;
  onYearChange: (year: number) => void;
}) {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTrip, setEditingTrip] = useState<Trip | null>(null);
  const [tccOptions, setTccOptions] = useState<TCCDestinationOption[]>([]);
  const [preselectedDate, setPreselectedDate] = useState<string | null>(null);

  // View mode: table or calendar
  const [viewMode, setViewMode] = useState<"table" | "calendar">(() => {
    const stored = localStorage.getItem("trips-view-mode");
    return stored === "calendar" ? "calendar" : "table";
  });

  // Destination holidays for trip badges (calendar + table)
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  // Czech holidays for calendar background coloring
  const [czechHolidays, setCzechHolidays] = useState<Holiday[]>([]);

  // User birthdays for calendar view
  const [birthdays, setBirthdays] = useState<UserBirthday[]>([]);

  // Persist view mode
  useEffect(() => {
    localStorage.setItem("trips-view-mode", viewMode);
  }, [viewMode]);

  const fetchTrips = useCallback(() => {
    fetch("/api/v1/travels/trips", { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch trips");
        return res.json();
      })
      .then((data: TripsResponse) => {
        setTrips(data.trips);
        // If no year selected, default to current year or most recent
        if (!selectedYear) {
          const years = getYearsWithTrips(data.trips);
          const currentYear = new Date().getFullYear();
          onYearChange(years.includes(currentYear) ? currentYear : years[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedYear, onYearChange]);

  useEffect(() => {
    fetchTrips();
    // Fetch TCC options for mapping names to IDs
    fetch("/api/v1/travels/tcc-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => setTccOptions(data.destinations || []))
      .catch(() => {});
    // Fetch users for birthdays
    fetch("/api/v1/travels/users-options", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        const users = data.users || [];
        // Also fetch admin users to get all birthdays
        fetch("/api/v1/admin/users/", { credentials: "include" })
          .then((res) => res.json())
          .then((adminData) => {
            const allUsers = [...users, ...(adminData.users || [])];
            const bdays: UserBirthday[] = [];
            for (const u of allUsers) {
              if (u.birthday) {
                // birthday is YYYY-MM-DD, extract MM-DD
                const mmdd = u.birthday.slice(5); // "MM-DD"
                bdays.push({
                  date: mmdd,
                  name: u.nickname || u.name || "User",
                });
              }
            }
            setBirthdays(bdays);
          })
          .catch(() => {});
      })
      .catch(() => {});
  }, [fetchTrips]);

  // Fetch holidays for destination countries of trips in selected year
  useEffect(() => {
    if (!selectedYear || trips.length === 0 || tccOptions.length === 0) {
      setHolidays([]);
      return;
    }

    // Get trips in selected year
    const yearTrips = trips.filter((t) => tripOverlapsYear(t, selectedYear));

    // Get unique country codes from those trips' destinations
    const countryCodes = new Set<string>();
    for (const trip of yearTrips) {
      for (const dest of trip.destinations) {
        const tcc = tccOptions.find((o) => o.name === dest.name);
        if (tcc?.country_code) {
          countryCodes.add(tcc.country_code);
        }
      }
    }

    if (countryCodes.size === 0) {
      setHolidays([]);
      return;
    }

    // Fetch holidays for each country
    const fetchPromises = Array.from(countryCodes).map((code) =>
      fetch(`/api/v1/travels/holidays/${selectedYear}/${code}`, {
        credentials: "include",
      })
        .then((res) => res.json())
        .then((data) =>
          (data.holidays || []).map(
            (h: { date: string; name: string; local_name: string | null }) => ({
              ...h,
              country_code: code,
            }),
          ),
        )
        .catch(() => []),
    );

    Promise.all(fetchPromises).then((results) => {
      setHolidays(results.flat());
    });
  }, [selectedYear, trips, tccOptions]);

  // Fetch Czech holidays for calendar background (always, regardless of trips)
  useEffect(() => {
    if (!selectedYear) {
      setCzechHolidays([]);
      return;
    }

    fetch(`/api/v1/travels/holidays/${selectedYear}/CZ`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        setCzechHolidays(
          (data.holidays || []).map(
            (h: { date: string; name: string; local_name: string | null }) => ({
              ...h,
              country_code: "CZ",
            }),
          ),
        );
      })
      .catch(() => setCzechHolidays([]));
  }, [selectedYear]);

  if (loading) {
    return <p>Loading trips...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  const years = getYearsWithTrips(trips);
  const filteredTrips = selectedYear
    ? trips.filter((t) => tripOverlapsYear(t, selectedYear))
    : trips;

  // Build first visit maps
  const firstVisitEver = buildFirstVisitMap(trips);
  const firstVisitThisYear = selectedYear
    ? buildFirstVisitInYearMap(trips, selectedYear)
    : new Map<string, string>();

  // Sort by start date descending within year
  const sortedTrips = [...filteredTrips].sort(
    (a, b) =>
      new Date(b.start_date).getTime() - new Date(a.start_date).getTime(),
  );

  // Calculate stats for selected year
  const yearTrips = sortedTrips;
  const totalDays = yearTrips.reduce(
    (sum, t) => sum + getDuration(t.start_date, t.end_date),
    0,
  );
  const workTrips = yearTrips.filter((t) => t.trip_type === "work").length;
  const uniqueDestinations = new Set(
    yearTrips.flatMap((t) => t.destinations.map((d) => d.name)),
  ).size;

  const handlePrevYear = () => {
    const idx = years.indexOf(selectedYear!);
    if (idx < years.length - 1) {
      onYearChange(years[idx + 1]);
    }
  };

  const handleNextYear = () => {
    const idx = years.indexOf(selectedYear!);
    if (idx > 0) {
      onYearChange(years[idx - 1]);
    }
  };

  const handleAddTrip = () => {
    setEditingTrip(null);
    setPreselectedDate(null);
    setModalOpen(true);
  };

  const handleEditTrip = (trip: Trip) => {
    setEditingTrip(trip);
    setPreselectedDate(null);
    setModalOpen(true);
  };

  // Handle calendar date click
  const handleCalendarDateClick = (date: string, trip?: Trip) => {
    if (trip) {
      handleEditTrip(trip);
    } else {
      setEditingTrip(null);
      setPreselectedDate(date);
      setModalOpen(true);
    }
  };

  const deleteTripById = async (tripId: number) => {
    const res = await fetch(`/api/v1/travels/trips/${tripId}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to delete trip");
    fetchTrips();
  };

  const handleDeleteTrip = async (tripId: number) => {
    if (!confirm("Are you sure you want to delete this trip?")) return;

    try {
      await deleteTripById(tripId);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete trip");
    }
  };

  const handleSaveTrip = async (data: TripFormData) => {
    const url = editingTrip
      ? `/api/v1/travels/trips/${editingTrip.id}`
      : "/api/v1/travels/trips";
    const method = editingTrip ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to save trip");
    }

    fetchTrips();
  };

  // Convert Trip to TripFormData for editing or preselected date for new trip
  const getInitialFormData = (): TripFormData | null => {
    if (editingTrip) {
      return {
        start_date: editingTrip.start_date,
        end_date: editingTrip.end_date,
        trip_type: editingTrip.trip_type,
        flights_count: editingTrip.flights_count,
        working_days: editingTrip.working_days,
        rental_car: editingTrip.rental_car,
        description: editingTrip.description,
        destinations: editingTrip.destinations
          .map((d) => {
            const tccOpt = tccOptions.find((o) => o.name === d.name);
            return {
              tcc_destination_id: tccOpt?.id || 0,
              is_partial: d.is_partial,
            };
          })
          .filter((d) => d.tcc_destination_id !== 0),
        cities: editingTrip.cities.map((c) => ({
          name: c.name,
          is_partial: c.is_partial,
        })),
        participant_ids: editingTrip.participants.map((p) => p.id),
        other_participants_count: editingTrip.other_participants_count,
      };
    }

    // If preselected date from calendar, return form with that date
    if (preselectedDate) {
      return {
        start_date: preselectedDate,
        end_date: null,
        trip_type: "regular",
        flights_count: null,
        working_days: null,
        rental_car: null,
        description: null,
        destinations: [],
        cities: [],
        participant_ids: [],
        other_participants_count: null,
      };
    }

    return null;
  };

  return (
    <div className="admin-trips">
      <div className="trips-header">
        <div className="year-selector">
          <button
            className="year-nav-btn"
            onClick={handlePrevYear}
            disabled={years.indexOf(selectedYear!) >= years.length - 1}
          >
            <BiChevronLeft />
          </button>
          <select
            value={selectedYear || ""}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="year-select"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <button
            className="year-nav-btn"
            onClick={handleNextYear}
            disabled={years.indexOf(selectedYear!) <= 0}
          >
            <BiChevronRight />
          </button>
          <button
            className="view-toggle-btn"
            onClick={() =>
              setViewMode((v) => (v === "table" ? "calendar" : "table"))
            }
            title={viewMode === "table" ? "Calendar view" : "Table view"}
          >
            {viewMode === "table" ? <BiCalendar /> : <BiTable />}
          </button>
          <button className="btn-add-trip" onClick={handleAddTrip}>
            <BiPlus /> Add Trip
          </button>
        </div>
        <div className="trips-stats">
          <span>{yearTrips.length} trips</span>
          <span>{totalDays} days</span>
          <span>{uniqueDestinations} TCC</span>
          {workTrips > 0 && <span>{workTrips} work</span>}
        </div>
      </div>

      {viewMode === "calendar" && selectedYear ? (
        <YearCalendarView
          year={selectedYear}
          trips={filteredTrips}
          holidays={holidays}
          czechHolidays={czechHolidays}
          birthdays={birthdays}
          onDateClick={handleCalendarDateClick}
          tccOptions={tccOptions}
        />
      ) : (
        <div className="trips-rows">
          {sortedTrips.map((trip) => {
            const isOverlapping =
              new Date(trip.start_date).getFullYear() !==
              (trip.end_date
                ? new Date(trip.end_date).getFullYear()
                : new Date(trip.start_date).getFullYear());
            const isFuture = isFutureTrip(trip);

            return (
              <div
                key={trip.id}
                className={`trip-row ${trip.trip_type !== "regular" ? `${trip.trip_type}-trip` : ""} ${isOverlapping ? "overlapping" : ""} ${isFuture ? "future-trip" : ""}`}
              >
                <div className="trip-row-date">
                  <span className="trip-date-range">
                    {formatDateRange(trip.start_date, trip.end_date)}
                  </span>
                  <div className="trip-date-meta">
                    <span
                      className="trip-badge days"
                      title={`${getDuration(trip.start_date, trip.end_date)} days`}
                    >
                      {getDuration(trip.start_date, trip.end_date)}d
                    </span>
                    {isFuture && (
                      <span
                        className="trip-badge future"
                        title="Future trip (not in stats)"
                      >
                        ⏳
                      </span>
                    )}
                    {trip.trip_type === "work" && (
                      <span
                        className="trip-badge work"
                        title={
                          trip.working_days
                            ? `${trip.working_days} working days`
                            : "Work trip"
                        }
                      >
                        <BiBriefcase />
                        {trip.working_days && <span>{trip.working_days}</span>}
                      </span>
                    )}
                    {trip.trip_type === "relocation" && (
                      <span
                        className="trip-badge relocation"
                        title="Relocation"
                      >
                        📦
                      </span>
                    )}
                    {trip.flights_count && trip.flights_count > 0 && (
                      <span
                        className="trip-badge flights"
                        title={`${trip.flights_count} flights`}
                      >
                        <BiPaperPlane />
                        <span>{trip.flights_count}</span>
                      </span>
                    )}
                    {trip.rental_car && (
                      <span className="trip-badge car" title={trip.rental_car}>
                        <BiCar />
                      </span>
                    )}
                    {isFuture &&
                      (() => {
                        const tripHolidays = getTripHolidays(
                          trip,
                          holidays,
                          tccOptions,
                        );
                        if (tripHolidays.length > 0) {
                          const holidayNames = tripHolidays
                            .map((h) => h.name)
                            .join(", ");
                          return (
                            <span
                              className="trip-badge holiday"
                              title={holidayNames}
                            >
                              <BiParty />
                            </span>
                          );
                        }
                        return null;
                      })()}
                  </div>
                </div>
                <div className="trip-row-main">
                  <div className="trip-destinations-row">
                    <span className="trip-destinations">
                      {trip.destinations.map((d, i) => {
                        const isFirstEver =
                          firstVisitEver.get(d.name) === trip.start_date;
                        const isFirstThisYear =
                          !isFirstEver &&
                          firstVisitThisYear.get(d.name) === trip.start_date;
                        return (
                          <span key={i}>
                            {i > 0 && ", "}
                            <span
                              className={
                                isFirstEver
                                  ? "dest-first-ever"
                                  : isFirstThisYear
                                    ? "dest-first-year"
                                    : ""
                              }
                            >
                              {d.name}
                            </span>
                          </span>
                        );
                      })}
                      {trip.destinations.length === 0 && "—"}
                    </span>
                    {(trip.participants.length > 0 ||
                      (trip.other_participants_count &&
                        trip.other_participants_count > 0)) && (
                      <span className="trip-participants-inline">
                        {trip.participants.map((p) => (
                          <span
                            key={p.id}
                            className="participant-avatar"
                            title={p.name || p.nickname || "Unknown"}
                          >
                            {p.picture ? (
                              <img src={p.picture} alt={p.nickname || ""} />
                            ) : (
                              <span className="avatar-initial">
                                {(p.nickname || p.name || "?")[0]}
                              </span>
                            )}
                          </span>
                        ))}
                        {trip.other_participants_count &&
                          trip.other_participants_count > 0 && (
                            <span className="participant-count">
                              +{trip.other_participants_count}
                            </span>
                          )}
                      </span>
                    )}
                  </div>
                  {trip.cities.length > 0 && (
                    <div className="trip-cities">
                      {trip.cities.map((city, i) => (
                        <span key={city.name}>
                          {i > 0 && ", "}
                          {city.is_partial ? (
                            <span className="city-partial">({city.name})</span>
                          ) : (
                            city.name
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                  {trip.description && (
                    <div className="trip-description">{trip.description}</div>
                  )}
                  <div className="trip-row-actions">
                    <button
                      className="trip-action-btn"
                      onClick={() => handleEditTrip(trip)}
                      title="Edit trip"
                    >
                      <BiPencil />
                    </button>
                    <button
                      className="trip-action-btn delete"
                      onClick={() => handleDeleteTrip(trip.id)}
                      title="Delete trip"
                    >
                      <BiTrash />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="trips-total">
        Total: {trips.length} trips across {years.length} years
      </div>

      <TripFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrip}
        onDelete={
          editingTrip
            ? async () => {
                await deleteTripById(editingTrip.id);
              }
            : undefined
        }
        initialData={getInitialFormData()}
        title={editingTrip ? "Edit Trip" : "Add Trip"}
      />
    </div>
  );
}

export default function Admin() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { tab, year } = useParams();
  const activeTab = (tab as AdminTab) || "trips";
  // For trips tab, 'year' is the year number
  // For instagram tab, 'year' is the ig_id (Instagram ID string)
  const selectedYear = tab === "instagram" ? null : year ? Number(year) : null;
  const instagramIgId = tab === "instagram" && year ? year : null;

  const setActiveTab = (newTab: AdminTab) => {
    if (newTab === "trips" && selectedYear) {
      navigate(`/admin/${newTab}/${selectedYear}`);
    } else {
      navigate(`/admin/${newTab}`);
    }
  };

  const setSelectedYear = (newYear: number) => {
    navigate(`/admin/${activeTab}/${newYear}`);
  };

  const setInstagramIgId = (igId: string | null) => {
    if (igId) {
      navigate(`/admin/instagram/${igId}`, { replace: true });
    } else {
      navigate(`/admin/instagram`, { replace: true });
    }
  };

  // Redirect non-admin users
  if (!authLoading && !user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  // Remove year from URL for close-ones tab
  if (activeTab === "close-ones" && year) {
    return <Navigate to="/admin/close-ones" replace />;
  }

  if (authLoading) {
    return (
      <section id="admin" className="admin">
        <div className="container">
          <p>Loading...</p>
        </div>
      </section>
    );
  }

  return (
    <section id="admin" className="admin">
      <div className="container">
        <div className="admin-header">
          <h1>Admin</h1>
        </div>

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "trips" ? "active" : ""}`}
            onClick={() => setActiveTab("trips")}
          >
            Trips
          </button>
          <button
            className={`admin-tab ${activeTab === "instagram" ? "active" : ""}`}
            onClick={() => setActiveTab("instagram")}
          >
            Instagram
          </button>
          <button
            className={`admin-tab ${activeTab === "close-ones" ? "active" : ""}`}
            onClick={() => setActiveTab("close-ones")}
          >
            Close Ones
          </button>
        </div>

        <div className="admin-content">
          {activeTab === "trips" && (
            <TripsTab
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />
          )}
          {activeTab === "close-ones" && <CloseOnesTab />}
          {activeTab === "instagram" && (
            <InstagramTab
              key={instagramIgId ?? "latest"}
              initialIgId={instagramIgId}
              onIgIdChange={setInstagramIgId}
            />
          )}
        </div>
      </div>
    </section>
  );
}
