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

function csvStatus(results: UploadResult[]): Status {
  const errors = results.filter((r) => r.status === "error");
  const created = results.filter((r) => r.status === "created").length;
  const replaced = results.filter((r) => r.status === "replaced").length;
  const parts = [
    created && `${created} new`,
    replaced && `${replaced} replaced`,
  ].filter(Boolean);
  const done = created + replaced;
  return {
    message: [
      done > 0 &&
        `Uploaded ${done} day${done !== 1 ? "s" : ""} (${parts.join(", ")})`,
      errors.length > 0 && `${errors.length} failed`,
    ]
      .filter(Boolean)
      .join(" · "),
    errors: errors.map((r) => `${r.file}: ${r.detail}`),
  };
}

interface TripTracksTabProps {
  tripId: string;
}

export default function TripTracksTab({ tripId }: TripTracksTabProps) {
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

  const load = () =>
    apiFetch(`/api/v1/travels/trips/${tripId}/gps-tracks`)
      .then((r) => r.json())
      .then((data) => {
        const list: GpsTrack[] = data.tracks || [];
        setTracks(list);
        setDefaultTz(data.default_timezone || "UTC");
        setActiveId((cur) => {
          if (list.length === 0) return null;
          if (cur === "all" || (cur && list.some((t) => t.id === cur)))
            return cur;
          const fromUrl = list.find((t) => t.local_date === dayParam);
          return fromUrl ? fromUrl.id : "all";
        });
      })
      .catch((err) => console.error("Failed to load GPS tracks:", err))
      .finally(() => setLoading(false));

  useEffect(() => {
    setLoading(true);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only per trip
  }, [tripId]);

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
      const r = await apiFetch(
        `/api/v1/travels/trips/${tripId}/gps-tracks/upload`,
        {
          method: "POST",
          body: form,
        },
      );
      const data = await r.json();
      setStatus(
        r.ok
          ? csvStatus(data.results)
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
      const r = await apiFetch(
        `/api/v1/travels/trips/${tripId}/gps-tracks/analysis`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
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
          <span>GPS Tracks ({tracks.length})</span>
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
                title="Time zone for the uploaded days — click to change"
              >
                {timezone || defaultTz}
              </button>
            )}
            <button
              className="btn-add-inline"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
            >
              <BiUpload /> {uploading ? "Uploading..." : "Upload CSVs"}
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
            No tracks yet. Upload the logger's day files (one CSV per day).
          </p>
        ) : (
          <>
            <div className="gps-day-pills">
              <button
                className={`gps-day-pill ${activeId === "all" ? "active" : ""}`}
                onClick={() => choose("all")}
              >
                <span>All days</span>
                <small>
                  {fmtKm(tracks.reduce((acc, t) => acc + t.distance_km, 0))}
                </small>
              </button>
              {tracks.map((t) => (
                <button
                  key={t.id}
                  className={`gps-day-pill ${t.id === activeId ? "active" : ""}`}
                  onClick={() => choose(t)}
                  title={t.title ?? undefined}
                >
                  <span>{fmtDay(t.local_date)}</span>
                  <small>{fmtKm(t.distance_km)}</small>
                </button>
              ))}
            </div>
            {activeId === "all" ? (
              <TrackDayView
                key="all"
                tracks={tracks}
                all
                onChanged={load}
                onOpenDay={choose}
              />
            ) : (
              active && (
                <TrackDayView
                  key={active.id}
                  tracks={[active]}
                  all={false}
                  onChanged={load}
                  onOpenDay={choose}
                />
              )
            )}
          </>
        )}
      </div>
    </div>
  );
}
