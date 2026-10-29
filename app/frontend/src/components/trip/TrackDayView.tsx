import { useMemo, useRef, useState } from "react";
import {
  BiChevronDown,
  BiChevronUp,
  BiCollapseHorizontal,
  BiDownload,
  BiExpandHorizontal,
  BiRefresh,
  BiTrash,
} from "react-icons/bi";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { apiFetch } from "../../lib/api";
import { isMotorised, MODE_ORDER, MODES, modeColor } from "./gpsModes";
import {
  fmtDay,
  fmtDuration,
  fmtKm,
  fmtTime,
  type GpsLeg,
  type GpsTrack,
} from "./gpsTypes";
import ModeSwatch from "./ModeSwatch";

function legBounds(leg: GpsLeg): L.LatLngBounds {
  const pts = leg.lines.flat();
  return pts.length > 0
    ? L.latLngBounds(pts)
    : L.latLngBounds([[leg.lat, leg.lon]]).pad(0.5);
}

function FitBounds({ bounds }: { bounds: L.LatLngBounds | null }) {
  const map = useMap();
  useEffect(() => {
    if (!bounds?.isValid()) return;
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    if (ne.equals(sw)) map.setView(ne, 17);
    else map.fitBounds(bounds, { padding: [30, 30], maxZoom: 17 });
  }, [map, bounds]);
  return null;
}

/** Leaflet caches its container size; tell it when the layout changes. */
function ResizeOnChange({ trigger }: { trigger: unknown }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map, trigger]);
  return null;
}

const LEGS_PREF_KEY = "gpsTracks.showLegs";
const LEGEND_PREF_KEY = "gpsTracks.legendOpen";

function readFlag(key: string): boolean {
  try {
    return localStorage.getItem(key) !== "0";
  } catch {
    return true;
  }
}

function writeFlag(key: string, value: boolean): void {
  try {
    localStorage.setItem(key, value ? "1" : "0");
  } catch {
    // preference only; ignore blocked storage
  }
}

/** Vertical, collapsible; lists only the modes that occur on this day. */
function Legend({ legs }: { legs: GpsLeg[] }) {
  const [open, setOpen] = useState(() => readFlag(LEGEND_PREF_KEY));
  const present = new Set(legs.map((l) => l.mode));
  const modes = MODE_ORDER.filter((m) => present.has(m));
  const toggle = () => {
    writeFlag(LEGEND_PREF_KEY, !open);
    setOpen(!open);
  };
  return (
    <div className={`gps-legend ${open ? "open" : ""}`}>
      <button className="gps-legend-toggle" onClick={toggle}>
        Legend {open ? <BiChevronUp /> : <BiChevronDown />}
      </button>
      {open && (
        <ul>
          {modes.map((m) => (
            <li key={m}>
              <ModeSwatch mode={m} />
              {MODES[m].label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Dashed joins wherever the logger paused: between lines of a leg and between legs. */
function connectors(legs: GpsLeg[]): [number, number][][] {
  const out: [number, number][][] = [];
  let last: [number, number] | null = null;
  for (const leg of legs) {
    const lines =
      leg.mode === "stop"
        ? [[[leg.lat, leg.lon] as [number, number]]]
        : leg.lines;
    for (const line of lines) {
      if (line.length === 0) continue;
      const first = line[0];
      if (last && (last[0] !== first[0] || last[1] !== first[1])) {
        out.push([last, first]);
      }
      last = line[line.length - 1];
    }
  }
  return out;
}

interface DayViewProps {
  /** One day, or every day of the trip when `all` is set. */
  tracks: GpsTrack[];
  all: boolean;
  onChanged: () => void;
  onOpenDay: (track: GpsTrack) => void;
}

function sum(
  tracks: GpsTrack[],
  key: "point_count" | "wake_count" | "poi_count" | "distance_km",
): number {
  return tracks.reduce((acc, t) => acc + t[key], 0);
}

export default function TrackDayView({
  tracks,
  all,
  onChanged,
  onOpenDay,
}: DayViewProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [showLegs, setShowLegs] = useState(() => readFlag(LEGS_PREF_KEY));
  const rowRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const track = tracks[0];
  const tz = track.timezone;
  // Every leg with the time zone of its own day (days can differ on multi-country trips)
  const items = useMemo(
    () => tracks.flatMap((t) => t.legs.map((leg) => ({ leg, tz: t.timezone }))),
    [tracks],
  );
  const legs = useMemo(() => items.map((i) => i.leg), [items]);

  const dayBounds = useMemo(() => {
    const b = L.latLngBounds([]);
    for (const leg of legs) b.extend(legBounds(leg));
    return b;
  }, [legs]);
  const selectedLeg = legs.find((l) => l.id === selected) ?? null;
  const bounds = useMemo(
    () => (selectedLeg ? legBounds(selectedLeg) : dayBounds),
    [selectedLeg, dayBounds],
  );
  // Joins stay within a day; nights between days are not drawn.
  const joins = useMemo(
    () => tracks.flatMap((t) => connectors(t.legs)),
    [tracks],
  );
  const zones = [...new Set(tracks.map((t) => t.timezone))];
  const focus = hovered ?? selected;

  const select = (id: number) => {
    setSelected((cur) => (cur === id ? null : id));
    rowRefs.current[id]?.scrollIntoView({ block: "nearest" });
  };

  const toggleLegs = () => {
    writeFlag(LEGS_PREF_KEY, !showLegs);
    setShowLegs(!showLegs);
  };

  const reprocess = async () => {
    const analysed = track.legs_source === "annotated";
    if (
      analysed &&
      !confirm(
        "This day has an analysis. Reprocessing replaces it with automatic legs. Continue?",
      )
    )
      return;
    const zone = prompt("Time zone for this day (IANA name):", tz);
    if (!zone) return;
    setBusy(true);
    const r = await apiFetch(
      `/api/v1/travels/gps-tracks/${track.id}/reprocess`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timezone: zone, discard_analysis: analysed }),
      },
    );
    setBusy(false);
    if (!r.ok) {
      alert((await r.json()).detail || "Reprocessing failed");
      return;
    }
    onChanged();
  };

  const remove = async () => {
    if (
      !confirm(
        `Delete the track for ${fmtDay(track.local_date)} and its raw file?`,
      )
    )
      return;
    setBusy(true);
    await apiFetch(`/api/v1/travels/gps-tracks/${track.id}`, {
      method: "DELETE",
    });
    setBusy(false);
    onChanged();
  };

  return (
    <div className="gps-day">
      {!all && track.title && (
        <div className="gps-day-heading">
          <strong>{track.title}</strong>
          {track.note && <span>{track.note}</span>}
        </div>
      )}
      <div className="gps-day-summary">
        {all ? (
          <>
            <span className="flight-badge">
              {tracks.length} day{tracks.length !== 1 ? "s" : ""}
            </span>
            <span className="flight-badge">
              {fmtKm(sum(tracks, "distance_km"))}
            </span>
            <span className="flight-badge">
              top {Math.round(Math.max(...tracks.map((t) => t.max_speed_kmh)))}{" "}
              km/h
            </span>
            <span className="flight-badge">
              {sum(tracks, "point_count").toLocaleString("en-GB")} points
            </span>
            <span className="flight-badge">
              {sum(tracks, "wake_count")} wake-ups
            </span>
            {zones.map((z) => (
              <span key={z} className="flight-badge">
                {z}
              </span>
            ))}
          </>
        ) : (
          <>
            <span className="flight-badge">
              {fmtTime(track.started_at, tz)}–{fmtTime(track.ended_at, tz)}
            </span>
            <span className="flight-badge">{fmtKm(track.distance_km)}</span>
            <span className="flight-badge">
              top {Math.round(track.max_speed_kmh)} km/h
            </span>
            <span className="flight-badge">
              {track.point_count.toLocaleString("en-GB")} points
            </span>
            <span className="flight-badge">{track.wake_count} wake-ups</span>
            {track.poi_count > 0 && (
              <span
                className="flight-badge"
                title="Often accidental pocket presses"
              >
                {track.poi_count} button press
                {track.poi_count !== 1 ? "es" : ""}
              </span>
            )}
            <span className="flight-badge">{tz}</span>
            <span className="flight-badge">
              {track.legs_source === "auto" ? "automatic legs" : "analysed"}
            </span>
          </>
        )}
      </div>

      <div className={`gps-day-body ${showLegs ? "" : "map-only"}`}>
        <div className="gps-map">
          <MapContainer
            key={all ? "all" : track.id}
            center={dayBounds.isValid() ? dayBounds.getCenter() : [0, 0]}
            zoom={13}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <FitBounds bounds={bounds} />
            <ResizeOnChange trigger={showLegs} />
            {joins.map((pts, i) => (
              <Polyline
                key={`j${i}`}
                positions={pts}
                pathOptions={{
                  color: modeColor("gap"),
                  weight: 2,
                  dashArray: "4 6",
                  opacity: 0.8,
                }}
              />
            ))}
            {items.map(({ leg, tz }) => {
              const dim = focus !== null && focus !== leg.id;
              const strong = focus === leg.id;
              const color = modeColor(leg.mode);
              const weight = strong ? 6 : 4;
              const opacity = dim ? 0.3 : 0.95;
              const handlers = {
                click: () => select(leg.id),
                mouseover: () => setHovered(leg.id),
                mouseout: () => setHovered(null),
              };
              if (leg.mode === "stop") {
                return (
                  <CircleMarker
                    key={leg.id}
                    center={[leg.lat, leg.lon]}
                    radius={strong ? 8 : 5}
                    pathOptions={{
                      color: "#fff",
                      weight: 1.5,
                      fillColor: color,
                      fillOpacity: dim ? 0.35 : 0.95,
                    }}
                    eventHandlers={handlers}
                  >
                    <Tooltip>
                      {leg.title || "Stop"} · {fmtTime(leg.started_at, tz)}–
                      {fmtTime(leg.ended_at, tz)}
                    </Tooltip>
                  </CircleMarker>
                );
              }
              if (leg.mode === "gap") {
                return leg.lines.map((line, i) => (
                  <Polyline
                    key={`${leg.id}-${i}`}
                    positions={line}
                    pathOptions={{
                      color,
                      weight: strong ? 4 : 2,
                      opacity,
                      dashArray: MODES.gap.dash,
                    }}
                    eventHandlers={handlers}
                  />
                ));
              }
              // White casing under each line keeps it readable on any tile
              // and makes the dash patterns show as colour on white.
              return leg.lines.map((line, i) => [
                <Polyline
                  key={`${leg.id}-${i}-casing`}
                  positions={line}
                  interactive={false}
                  pathOptions={{ color: "#fff", weight: weight + 3, opacity }}
                />,
                <Polyline
                  key={`${leg.id}-${i}`}
                  positions={line}
                  pathOptions={{
                    color,
                    weight,
                    opacity,
                    dashArray: MODES[leg.mode].dash,
                  }}
                  eventHandlers={handlers}
                />,
              ]);
            })}
          </MapContainer>
          <Legend legs={legs} />
        </div>

        {showLegs && (
          <div className="gps-legs">
            {tracks.map((t) => (
              <div key={t.id} className="gps-legs-day">
                {all && (
                  <button
                    className="gps-legs-day-header"
                    onClick={() => onOpenDay(t)}
                    title="Open this day"
                  >
                    <span>
                      {fmtDay(t.local_date)}
                      {t.title && <em> · {t.title}</em>}
                    </span>
                    <span>{fmtKm(t.distance_km)} ›</span>
                  </button>
                )}
                {t.legs.map((leg) => (
                  <div
                    key={leg.id}
                    ref={(el) => {
                      rowRefs.current[leg.id] = el;
                    }}
                    className={`gps-leg ${selected === leg.id ? "selected" : ""} ${
                      hovered === leg.id ? "hovered" : ""
                    }`}
                    onClick={() => select(leg.id)}
                    onMouseEnter={() => setHovered(leg.id)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    <ModeSwatch mode={leg.mode} />
                    <span className="gps-leg-time">
                      {fmtTime(leg.started_at, t.timezone)}–
                      {fmtTime(leg.ended_at, t.timezone)}
                    </span>
                    <span className="gps-leg-main">
                      <span className="gps-leg-title">
                        {leg.title || MODES[leg.mode].label}
                        {leg.is_hidden && (
                          <span className="gps-leg-hidden">hidden</span>
                        )}
                      </span>
                      <span className="gps-leg-stats">
                        {fmtDuration(leg.started_at, leg.ended_at)}
                        {leg.mode !== "stop" && ` · ${fmtKm(leg.distance_km)}`}
                        {isMotorised(leg.mode) &&
                          ` · top ${Math.round(leg.max_speed_kmh)} km/h`}
                        {leg.mode === "gap" && " moved without a fix"}
                      </span>
                      {leg.note && (
                        <span className="gps-leg-note">{leg.note}</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="gps-day-actions">
        <button
          className="btn-add-inline"
          onClick={toggleLegs}
          title={showLegs ? "Map only" : "Show the legs list"}
        >
          {showLegs ? <BiExpandHorizontal /> : <BiCollapseHorizontal />}
          {showLegs ? "Map only" : "Show legs"}
        </button>
        {all && (
          <span className="gps-actions-hint">
            Open a day for CSV, Reprocess and Delete
          </span>
        )}
        {!all && (
          <>
            <a
              className="btn-add-inline"
              href={`/api/v1/travels/gps-tracks/${track.id}/raw`}
              title={`Download ${track.source_file}`}
            >
              <BiDownload /> CSV
            </a>
            <button
              className="btn-add-inline"
              onClick={reprocess}
              disabled={busy}
              title="Re-run automatic processing (optionally in another time zone)"
            >
              <BiRefresh /> Reprocess
            </button>
            <button className="btn-add-inline" onClick={remove} disabled={busy}>
              <BiTrash /> Delete
            </button>
          </>
        )}
      </div>
    </div>
  );
}
