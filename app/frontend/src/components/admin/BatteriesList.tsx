import { useCallback, useEffect, useState } from "react";
import { BiArchiveIn, BiArchiveOut, BiPencil } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type { BatteryItem, DroneItem } from "./types";
import { fmtDate } from "./types";

function fmtDuration(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function healthColor(pct: number | null): string {
  if (pct == null) return "";
  if (pct > 80) return "battery-health-good";
  if (pct >= 60) return "battery-health-warn";
  return "battery-health-bad";
}

export default function BatteriesList({
  readOnly,
  addTrigger,
  refreshTrigger,
}: {
  readOnly?: boolean;
  addTrigger?: number;
  refreshTrigger?: number;
}) {
  const [batteries, setBatteries] = useState<BatteryItem[]>([]);
  const [drones, setDrones] = useState<DroneItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<BatteryItem | null>(null);

  // Form state
  const [formSerial, setFormSerial] = useState("");
  const [formColor, setFormColor] = useState("");
  const [formModel, setFormModel] = useState("");
  const [formDroneId, setFormDroneId] = useState("");
  const [formDesignCap, setFormDesignCap] = useState("");
  const [formCellCount, setFormCellCount] = useState("");
  const [formAcquired, setFormAcquired] = useState("");
  const [formRetired, setFormRetired] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchBatteries = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/travels/batteries");
      if (res.ok) {
        const data = await res.json();
        setBatteries(data.batteries);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDrones = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/travels/drones");
      if (res.ok) {
        const data = await res.json();
        setDrones(data.drones);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchBatteries();
    fetchDrones();
  }, [fetchBatteries, fetchDrones]);

  useEffect(() => {
    if (refreshTrigger) fetchBatteries();
  }, [refreshTrigger, fetchBatteries]);

  useEffect(() => {
    if (addTrigger) openCreate();
  }, [addTrigger]);

  const openCreate = () => {
    setEditing(null);
    setFormSerial("");
    setFormColor("");
    setFormModel("");
    setFormDroneId("");
    setFormDesignCap("");
    setFormCellCount("");
    setFormAcquired("");
    setFormRetired("");
    setFormNotes("");
    setModalOpen(true);
  };

  const openEdit = (b: BatteryItem) => {
    setEditing(b);
    setFormSerial(b.serial_number);
    setFormColor(b.color || "");
    setFormModel(b.model || "");
    setFormDroneId(b.drone_id ? String(b.drone_id) : "");
    setFormDesignCap(
      b.design_capacity_mah ? String(b.design_capacity_mah) : "",
    );
    setFormCellCount(b.cell_count ? String(b.cell_count) : "");
    setFormAcquired(b.acquired_date || "");
    setFormRetired(b.retired_date || "");
    setFormNotes(b.notes || "");
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!editing && !formSerial.trim()) return;
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        color: formColor || null,
        model: formModel.trim() || null,
        drone_id: formDroneId ? Number(formDroneId) : null,
        design_capacity_mah: formDesignCap ? Number(formDesignCap) : null,
        cell_count: formCellCount ? Number(formCellCount) : null,
        acquired_date: formAcquired || null,
        retired_date: formRetired || null,
        notes: formNotes.trim() || null,
      };
      if (!editing) {
        body.serial_number = formSerial.trim();
      }
      const url = editing
        ? `/api/v1/travels/batteries/${editing.id}`
        : "/api/v1/travels/batteries";
      const method = editing ? "PUT" : "POST";
      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setModalOpen(false);
        fetchBatteries();
      }
    } finally {
      setSaving(false);
    }
  };

  const handleRetire = async (b: BatteryItem) => {
    const action = b.retired_date ? "reactivate" : "retire";
    if (
      !confirm(
        `${action === "retire" ? "Retire" : "Reactivate"} ${b.serial_number}?`,
      )
    )
      return;
    const res = await apiFetch(`/api/v1/travels/batteries/${b.id}/retire`, {
      method: "PUT",
    });
    if (res.ok) fetchBatteries();
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="my-drones">
      {batteries.length === 0 ? (
        <p className="empty-state">No batteries registered.</p>
      ) : (
        <div className="drone-cards">
          {[...batteries]
            .sort((a, b) => (a.retired_date ? 1 : 0) - (b.retired_date ? 1 : 0))
            .map((b) => (
              <div
                key={b.id}
                className={`drone-card${b.retired_date ? " drone-card-retired" : ""}`}
              >
                {b.retired_date && (
                  <div className="drone-card-ribbon">Retired</div>
                )}
                <div className="drone-card-header">
                  <span className="battery-card-title">
                    {b.color && (
                      <span
                        className="battery-color-dot"
                        style={{ backgroundColor: b.color }}
                      />
                    )}
                    <strong>{b.serial_number}</strong>
                  </span>
                  {!readOnly && (
                    <span className="drone-card-actions">
                      <button
                        className="btn-icon"
                        onClick={() => openEdit(b)}
                        title="Edit"
                      >
                        <BiPencil />
                      </button>
                      <button
                        className="btn-icon"
                        onClick={() => handleRetire(b)}
                        title={b.retired_date ? "Reactivate" : "Retire"}
                      >
                        {b.retired_date ? <BiArchiveOut /> : <BiArchiveIn />}
                      </button>
                    </span>
                  )}
                </div>
                <div className="drone-card-body">
                  {b.last_health_pct != null && (
                    <span
                      className={`drone-badge ${healthColor(b.last_health_pct)}`}
                    >
                      {b.last_health_pct}% health
                    </span>
                  )}
                  <span className="drone-flights-badge">
                    {b.flights_count} flights
                  </span>
                  {b.total_flight_time_sec > 0 && (
                    <span className="drone-flights-badge">
                      {fmtDuration(b.total_flight_time_sec)}
                    </span>
                  )}
                </div>
                {b.drone_name && (
                  <div className="drone-card-detail">Drone: {b.drone_name}</div>
                )}
                {b.last_cycles != null && (
                  <div className="drone-card-detail">
                    Cycles: {b.last_cycles}
                  </div>
                )}
                {b.design_capacity_mah && (
                  <div className="drone-card-detail">
                    Capacity: {b.design_capacity_mah} mAh
                    {b.cell_count ? ` (${b.cell_count}S)` : ""}
                  </div>
                )}
                {b.acquired_date && (
                  <div className="drone-card-detail">
                    Acquired: {fmtDate(b.acquired_date)}
                  </div>
                )}
                {b.retired_date && (
                  <div className="drone-card-detail">
                    Retired: {fmtDate(b.retired_date)}
                  </div>
                )}
                {b.notes && (
                  <div className="drone-card-detail drone-card-notes">
                    {b.notes}
                  </div>
                )}
              </div>
            ))}
        </div>
      )}

      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div
            className="modal-content modal-small"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>{editing ? "Edit Battery" : "Add Battery"}</h2>
              <button
                className="modal-close"
                onClick={() => setModalOpen(false)}
              >
                &times;
              </button>
            </div>
            <form
              className="user-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSave();
              }}
            >
              {editing ? (
                <div className="form-group">
                  <label>Serial Number</label>
                  <input value={formSerial} disabled />
                </div>
              ) : (
                <div className="form-group">
                  <label>Serial Number *</label>
                  <input
                    value={formSerial}
                    onChange={(e) => setFormSerial(e.target.value)}
                    placeholder="e.g. 3NDDH270028F5E"
                    required
                  />
                </div>
              )}
              <div className="form-group">
                <label>Color</label>
                <div className="color-picker-row">
                  <input
                    type="color"
                    value={formColor || "#808080"}
                    onChange={(e) => setFormColor(e.target.value)}
                    className="color-picker-input"
                  />
                  {formColor && (
                    <button
                      type="button"
                      className="btn-cancel btn-small"
                      onClick={() => setFormColor("")}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
              <div className="form-group">
                <label>Model</label>
                <input
                  value={formModel}
                  onChange={(e) => setFormModel(e.target.value)}
                  placeholder="e.g. BWX260-5000-15.4"
                />
              </div>
              <div className="form-group">
                <label>Drone</label>
                <select
                  value={formDroneId}
                  onChange={(e) => setFormDroneId(e.target.value)}
                >
                  <option value="">None</option>
                  {drones.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Design Capacity (mAh)</label>
                <input
                  type="number"
                  value={formDesignCap}
                  onChange={(e) => setFormDesignCap(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Cell Count</label>
                <input
                  type="number"
                  value={formCellCount}
                  onChange={(e) => setFormCellCount(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Acquired Date</label>
                <input
                  type="date"
                  value={formAcquired}
                  onChange={(e) => setFormAcquired(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Retired Date</label>
                <input
                  type="date"
                  value={formRetired}
                  onChange={(e) => setFormRetired(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-save" disabled={saving}>
                  {saving ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
