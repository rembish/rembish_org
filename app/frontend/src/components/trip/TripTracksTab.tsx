import { useCallback, useEffect, useRef, useState } from "react";
import { BiFile, BiUpload, BiX } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import { fmtDay, fmtKm, type GpsTrack, type UploadResult } from "./gpsTypes";
import TrackDayView from "./TrackDayView";

interface Status {
  message: string;
  errors: string[];
}

function UploadStatus({
  status,
  onDismiss,
}: {
  status: Status;
  onDismiss: () => void;
}) {
  const failed = status.errors.length > 0;

  useEffect(() => {
    if (failed) return;
    const t = setTimeout(onDismiss, 5000);
    return () => clearTimeout(t);
  }, [failed, onDismiss]);

  return (
    <div className={`gps-upload-status ${failed ? "has-errors" : ""}`}>
      <span>{status.message}</span>
      <button
        className="gps-upload-dismiss"
        onClick={onDismiss}
        title="Dismiss"
      >
        <BiX />
      </button>
      {status.errors.map((e, i) => (
        <div key={i} className="gps-upload-error">
          {e}
        </div>
      ))}
    </div>
  );
}

const plural = (n: number, word: string) => `${n} ${word}${n !== 1 ? "s" : ""}`;

function csvStatus(results: UploadResult[], card: boolean): Status {
  const errors = results.filter((r) => r.status === "error");
  const done = results.filter(
    (r) => r.status === "created" || r.status === "replaced",
  );
  const created = done.filter((r) => r.status === "created").length;
  const replaced = done.length - created;
  const skipped = results.filter((r) => r.status === "skipped").length;
  let parts: (string | false)[];
  if (card) {
    // Where the new days went: trips by number, the rest to days out
    const trips = [
      ...new Set(done.filter((r) => r.trip_id).map((r) => `#${r.trip_id}`)),
    ];
    const out = done.filter((r) => !r.trip_id).length;
    parts = [
      trips.length > 0 && `to trip ${trips.join(", ")}`,
      out > 0 && `${out} day${out !== 1 ? "s" : ""} out`,
    ];
  } else {
    parts = [
      created > 0 && `${created} new`,
      replaced > 0 && `${replaced} replaced`,
    ];
  }
  return {
    message: [
      done.length > 0 &&
        `Uploaded ${plural(done.length, "day")} (${parts.filter(Boolean).join(", ")})`,
      skipped > 0 && `${skipped} already on the site`,
      errors.length > 0 && `${errors.length} failed`,
    ]
      .filter(Boolean)
      .join(" · "),
    // Notes on uploaded days (e.g. a day in two trips) are shown with the errors
    errors: [
      ...errors.map((r) => `${r.file}: ${r.detail}`),
      ...done.filter((r) => r.detail).map((r) => `${r.file}: ${r.detail}`),
    ],
  };
}

/** Title and trip controls for one day out. */
function DayOutControls({
  track,
  onChanged,
}: {
  track: GpsTrack;
  onChanged: () => void;
}) {
  const [title, setTitle] = useState(track.title ?? "");
  const [tripId, setTripId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const patch = async (body: Record<string, unknown>) => {
    setError(null);
    const r = await apiFetch(`/api/v1/travels/gps-tracks/${track.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      setError(String((await r.json()).detail || "Update failed"));
      return;
    }
    onChanged();
  };

  const attach = () => {
    const id = Number(tripId.replace("#", ""));
    if (!Number.isInteger(id) || id <= 0) {
      setError("Enter a trip number");
      return;
    }
    patch({ trip_id: id });
  };

  return (
    <div className="gps-dayout-controls">
      <input
        value={title}
        placeholder="Title for this day"
        maxLength={200}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && patch({ title })}
      />
      <button
        className="btn-add-inline"
        onClick={() => patch({ title })}
        disabled={title === (track.title ?? "")}
      >
        Save title
      </button>
      <input
        className="gps-dayout-trip"
        value={tripId}
        placeholder="Trip #"
        inputMode="numeric"
        onChange={(e) => setTripId(e.target.value.trim())}
        onKeyDown={(e) => e.key === "Enter" && attach()}
      />
      <button className="btn-add-inline" onClick={attach} disabled={!tripId}>
        Attach to trip
      </button>
      {error && <span className="gps-upload-error">{error}</span>}
    </div>
  );
}

// Days out are listed newest first, a page at a time (the API caps a page at 100).
const DAYS_OUT_PAGE = 20;
const thisYear = String(new Date().getFullYear());
const MAX_PAGE = 100;

interface TripTracksTabProps {
  /** Without a trip: days out, and the upload takes a whole card. */
  tripId?: string;
}

export default function TripTracksTab({ tripId }: TripTracksTabProps) {
  const base = tripId
    ? `/api/v1/travels/trips/${tripId}/gps-tracks`
    : "/api/v1/travels/gps-tracks";
  const listUrl = tripId ? base : `${base}/unassigned`;
  const [tracks, setTracks] = useState<GpsTrack[]>([]);
  const [defaultTz, setDefaultTz] = useState("UTC");
  const [timezone, setTimezone] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [editingTz, setEditingTz] = useState(false);
  const clearStatus = useCallback(() => setStatus(null), []);
  const fileInput = useRef<HTMLInputElement>(null);
  const analysisInput = useRef<HTMLInputElement>(null);

  const dayParam = new URLSearchParams(window.location.search).get("day");
  // "all" is the overview of every day
  const [activeId, setActiveId] = useState<number | "all" | null>(null);

  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  // How many days out are on screen; a reload after a change keeps them all.
  const shownRef = useRef(DAYS_OUT_PAGE);

  const pageUrl = (limit: number, offset: number) =>
    tripId ? listUrl : `${listUrl}?limit=${limit}&offset=${offset}`;

  const load = () =>
    apiFetch(pageUrl(Math.min(MAX_PAGE, shownRef.current), 0))
      .then((r) => r.json())
      .then((data) => {
        const list: GpsTrack[] = data.tracks || [];
        setTracks(list);
        setTotal(data.total ?? list.length);
        setDefaultTz(data.default_timezone || "UTC");
        setActiveId((cur) => {
          if (list.length === 0) return null;
          if (
            (cur === "all" && tripId) ||
            (cur && list.some((t) => t.id === cur))
          )
            return cur;
          const fromUrl = list.find((t) => t.local_date === dayParam);
          if (fromUrl) return fromUrl.id;
          // A trip opens on its overview; days out on the newest day
          return tripId ? "all" : list[0].id;
        });
      })
      .catch((err) => console.error("Failed to load GPS tracks:", err))
      .finally(() => setLoading(false));

  const loadOlder = () => {
    setLoadingMore(true);
    apiFetch(pageUrl(DAYS_OUT_PAGE, tracks.length))
      .then((r) => r.json())
      .then((data) => {
        const more: GpsTrack[] = data.tracks || [];
        setTracks((cur) => {
          const known = new Set(cur.map((t) => t.id));
          const next = [...cur, ...more.filter((t) => !known.has(t.id))];
          shownRef.current = next.length;
          return next;
        });
        setTotal(data.total ?? total);
      })
      .catch((err) => console.error("Failed to load older days:", err))
      .finally(() => setLoadingMore(false));
  };

  useEffect(() => {
    setLoading(true);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only per trip
  }, [listUrl]);

  const active = tracks.find((t) => t.id === activeId) ?? null;

  const choose = (track: GpsTrack | "all") => {
    setActiveId(track === "all" ? "all" : track.id);
    const url = new URL(window.location.href);
    if (track === "all") url.searchParams.delete("day");
    else url.searchParams.set("day", track.local_date);
    window.history.replaceState(null, "", url);
  };

  const upload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const form = new FormData();
    for (const f of Array.from(files)) form.append("files", f);
    form.append("timezone", timezone || defaultTz);
    setUploading(true);
    setStatus(null);
    try {
      const r = await apiFetch(`${base}/upload`, {
        method: "POST",
        body: form,
      });
      const data = await r.json();
      setStatus(
        r.ok
          ? csvStatus(data.results, !tripId)
          : { message: "Upload failed", errors: [String(data.detail)] },
      );
      await load();
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const uploadAnalysis = async (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    setUploading(true);
    setStatus(null);
    try {
      let body: unknown;
      try {
        body = JSON.parse(await file.text());
      } catch {
        setStatus({ message: `${file.name} is not valid JSON`, errors: [] });
        return;
      }
      const r = await apiFetch(`${base}/analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (r.ok) {
        const n = data.days.length;
        setStatus({
          message: `Analysis applied to ${n} day${n !== 1 ? "s" : ""}`,
          errors: [],
        });
        await load();
      } else {
        // 422 detail is a list of problems (ours) or pydantic's field errors
        const detail = Array.isArray(data.detail) ? data.detail : [data.detail];
        setStatus({
          message: "Analysis not applied — nothing was changed",
          errors: detail.map((d: unknown) =>
            typeof d === "string"
              ? d
              : `${((d as { loc?: unknown[] }).loc ?? []).join(".")}: ${(d as { msg?: string }).msg}`,
          ),
        });
      }
    } finally {
      setUploading(false);
      if (analysisInput.current) analysisInput.current.value = "";
    }
  };

  if (loading) {
    return (
      <div className="trip-transport-tab">
        <p>Loading tracks...</p>
      </div>
    );
  }

  return (
    <div className="trip-transport-tab gps-tracks-tab">
      <div className="form-section">
        <h3 className="section-header-with-action">
          <span>
            {tripId ? "GPS Tracks" : "Days out"} (
            {tripId ? tracks.length : total})
          </span>
          <span className="gps-upload">
            {editingTz ? (
              <input
                className="gps-tz-input"
                autoFocus
                value={timezone}
                placeholder={defaultTz}
                onChange={(e) => setTimezone(e.target.value.trim())}
                onBlur={() => setEditingTz(false)}
                onKeyDown={(e) => e.key === "Enter" && setEditingTz(false)}
              />
            ) : (
              <button
                className="gps-tz-chip"
                onClick={() => setEditingTz(true)}
                title={
                  tripId
                    ? "Time zone for the uploaded days — click to change"
                    : "Time zone for days that fall in no trip (trip days use the trip's) — click to change"
                }
              >
                {timezone || defaultTz}
              </button>
            )}
            <button
              className="btn-add-inline"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
            >
              <BiUpload />{" "}
              {uploading
                ? "Uploading..."
                : tripId
                  ? "Upload CSVs"
                  : "Upload card"}
            </button>
            <input
              ref={fileInput}
              type="file"
              accept=".csv,.CSV"
              multiple
              hidden
              onChange={(e) => upload(e.target.files)}
            />
            {tracks.length > 0 && (
              <button
                className="btn-add-inline"
                onClick={() => analysisInput.current?.click()}
                disabled={uploading}
                title="Upload an analysis JSON (see the GPS analysis runbook)"
              >
                <BiFile /> Upload analysis
              </button>
            )}
            <input
              ref={analysisInput}
              type="file"
              accept=".json,application/json"
              hidden
              onChange={(e) => uploadAnalysis(e.target.files)}
            />
          </span>
        </h3>

        {status && <UploadStatus status={status} onDismiss={clearStatus} />}

        {tracks.length === 0 ? (
          <p className="flight-empty">
            {tripId
              ? "No tracks yet. Upload the logger's day files (one CSV per day)."
              : "No days out. Upload the logger's day files: days inside a trip go to that trip, days in no trip appear here."}
          </p>
        ) : (
          <>
            <div className="gps-day-pills">
              {/* The overview is for one trip's days; days out are unrelated */}
              {tripId && (
                <button
                  className={`gps-day-pill ${activeId === "all" ? "active" : ""}`}
                  onClick={() => choose("all")}
                >
                  <span>All days</span>
                  <small>
                    {fmtKm(tracks.reduce((acc, t) => acc + t.distance_km, 0))}
                  </small>
                </button>
              )}
              {tracks.map((t) => (
                <button
                  key={t.id}
                  className={`gps-day-pill ${t.id === activeId ? "active" : ""}`}
                  onClick={() => choose(t)}
                  title={t.title ?? undefined}
                >
                  <span>
                    {fmtDay(t.local_date)}
                    {/* Days out span years; a trip's days don't need it */}
                    {!tripId &&
                      !t.local_date.startsWith(thisYear) &&
                      ` ${t.local_date.slice(0, 4)}`}
                  </span>
                  <small>{fmtKm(t.distance_km)}</small>
                </button>
              ))}
              {!tripId && tracks.length < total && (
                <button
                  className="gps-day-pill gps-day-more"
                  onClick={loadOlder}
                  disabled={loadingMore}
                >
                  <span>{loadingMore ? "Loading..." : "Show older"}</span>
                  <small>{total - tracks.length} more</small>
                </button>
              )}
            </div>
            {activeId === "all" && tripId ? (
              <TrackDayView
                key="all"
                tracks={tracks}
                all
                onChanged={load}
                onOpenDay={choose}
              />
            ) : (
              active && (
                <>
                  {!tripId && (
                    <DayOutControls
                      key={`controls-${active.id}`}
                      track={active}
                      onChanged={load}
                    />
                  )}
                  <TrackDayView
                    key={`day-${active.id}`}
                    tracks={[active]}
                    all={false}
                    onChanged={load}
                    onOpenDay={choose}
                  />
                </>
              )
            )}
          </>
        )}
      </div>
    </div>
  );
}
