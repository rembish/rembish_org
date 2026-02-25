import { useCallback, useEffect, useState } from "react";
import { BiArchiveIn, BiArchiveOut, BiPencil } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type { DroneItem } from "./types";
import { fmtDate } from "./types";

export default function MyDrones({
  readOnly,
  addTrigger,
  onRetire,
}: {
  readOnly?: boolean;
  addTrigger?: number;
  onRetire?: () => void;
}) {
  const [drones, setDrones] = useState<DroneItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DroneItem | null>(null);

  // Form state
  const [formName, setFormName] = useState("");
  const [formModel, setFormModel] = useState("");
  const [formSerial, setFormSerial] = useState("");
  const [formAcquired, setFormAcquired] = useState("");
  const [formRetired, setFormRetired] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchDrones = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/travels/drones");
      if (res.ok) {
        const data = await res.json();
        setDrones(data.drones);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDrones();
  }, [fetchDrones]);

  useEffect(() => {
    if (addTrigger) openCreate();
  }, [addTrigger]);

  const openCreate = () => {
    setEditing(null);
    setFormName("");
    setFormModel("");
    setFormSerial("");
    setFormAcquired("");
    setFormRetired("");
    setFormNotes("");
    setModalOpen(true);
  };

  const openEdit = (d: DroneItem) => {
    setEditing(d);
    setFormName(d.name);
    setFormModel(d.model);
    setFormSerial(d.serial_number || "");
    setFormAcquired(d.acquired_date || "");
    setFormRetired(d.retired_date || "");
    setFormNotes(d.notes || "");
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!formName.trim() || !formModel.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: formName.trim(),
        model: formModel.trim(),
        serial_number: formSerial.trim() || null,
        acquired_date: formAcquired || null,
        retired_date: formRetired || null,
        notes: formNotes.trim() || null,
      };
      const url = editing
        ? `/api/v1/travels/drones/${editing.id}`
        : "/api/v1/travels/drones";
      const method = editing ? "PUT" : "POST";
      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setModalOpen(false);
        fetchDrones();
      }
    } finally {
      setSaving(false);
    }
  };

  const handleRetire = async (d: DroneItem) => {
    const action = d.retired_date ? "reactivate" : "retire";
    if (!confirm(`${action === "retire" ? "Retire" : "Reactivate"} ${d.name}?`))
      return;
    const res = await apiFetch(`/api/v1/travels/drones/${d.id}/retire`, {
      method: "PUT",
    });
    if (res.ok) {
      fetchDrones();
      onRetire?.();
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="my-drones">
      {drones.length === 0 ? (
        <p className="empty-state">No drones registered.</p>
      ) : (
        <div className="drone-cards">
          {[...drones]
            .sort((a, b) => (a.retired_date ? 1 : 0) - (b.retired_date ? 1 : 0))
            .map((d) => (
              <div
                key={d.id}
                className={`drone-card${d.retired_date ? " drone-card-retired" : ""}`}
              >
                {d.retired_date && (
                  <div className="drone-card-ribbon">Retired</div>
                )}
                <div className="drone-card-header">
                  <strong>{d.name}</strong>
                  {!readOnly && (
                    <span className="drone-card-actions">
                      <button
                        className="btn-icon"
                        onClick={() => openEdit(d)}
                        title="Edit"
                      >
                        <BiPencil />
                      </button>
                      <button
                        className="btn-icon"
                        onClick={() => handleRetire(d)}
                        title={d.retired_date ? "Reactivate" : "Retire"}
                      >
                        {d.retired_date ? <BiArchiveOut /> : <BiArchiveIn />}
                      </button>
                    </span>
                  )}
                </div>
                <div className="drone-card-body">
                  <span className="drone-badge">{d.model}</span>
                  <span className="drone-flights-badge">
                    {d.flights_count} flights
                  </span>
                </div>
                {d.serial_number && (
                  <div className="drone-card-detail">
                    S/N: {d.serial_number}
                  </div>
                )}
                {d.acquired_date && (
                  <div className="drone-card-detail">
                    Acquired: {fmtDate(d.acquired_date)}
                  </div>
                )}
                {d.retired_date && (
                  <div className="drone-card-detail">
                    Retired: {fmtDate(d.retired_date)}
                  </div>
                )}
                {d.notes && (
                  <div className="drone-card-detail drone-card-notes">
                    {d.notes}
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
              <h2>{editing ? "Edit Drone" : "Add Drone"}</h2>
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
              <div className="form-group">
                <label>Name *</label>
                <input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. air2.rembish.org"
                  required
                />
              </div>
              <div className="form-group">
                <label>Model *</label>
                <input
                  value={formModel}
                  onChange={(e) => setFormModel(e.target.value)}
                  placeholder="e.g. Mavic Air 2"
                  required
                />
              </div>
              <div className="form-group">
                <label>Serial Number</label>
                <input
                  value={formSerial}
                  onChange={(e) => setFormSerial(e.target.value)}
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
