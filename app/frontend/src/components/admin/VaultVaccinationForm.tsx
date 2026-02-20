import { useEffect, useState } from "react";
import type { VaultVaccination, VaultUser } from "./types";

export default function VaccinationFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  users,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    user_id: number;
    vaccine_name: string;
    brand_name: string;
    dose_type: string;
    date_administered: string;
    expiry_date: string;
    batch_number: string;
    notes: string;
  }) => Promise<void>;
  initialData: VaultVaccination | null;
  users: VaultUser[];
}) {
  const [form, setForm] = useState({
    user_id: initialData?.user_id ?? users[0]?.id ?? 0,
    vaccine_name: initialData?.vaccine_name ?? "",
    brand_name: initialData?.brand_name ?? "",
    dose_type: initialData?.dose_type ?? "",
    date_administered: initialData?.date_administered ?? "",
    expiry_date: initialData?.expiry_date ?? "",
    batch_number: initialData?.batch_number_decrypted ?? "",
    notes: initialData?.notes_decrypted ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm({
        user_id: initialData?.user_id ?? users[0]?.id ?? 0,
        vaccine_name: initialData?.vaccine_name ?? "",
        brand_name: initialData?.brand_name ?? "",
        dose_type: initialData?.dose_type ?? "",
        date_administered: initialData?.date_administered ?? "",
        expiry_date: initialData?.expiry_date ?? "",
        batch_number: initialData?.batch_number_decrypted ?? "",
        notes: initialData?.notes_decrypted ?? "",
      });
      setError(null);
    }
  }, [isOpen, initialData, users]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.vaccine_name.trim()) {
      setError("Vaccine name is required");
      return;
    }
    setSaving(true);
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content modal-small"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{initialData ? "Edit Vaccination" : "Add Vaccination"}</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}
          <div className="form-group">
            <label>User *</label>
            <select
              value={form.user_id}
              onChange={(e) =>
                setForm((p) => ({ ...p, user_id: Number(e.target.value) }))
              }
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nickname || u.name || `User #${u.id}`}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Vaccine Name *</label>
            <input
              type="text"
              value={form.vaccine_name}
              onChange={(e) =>
                setForm((p) => ({ ...p, vaccine_name: e.target.value }))
              }
              placeholder="e.g. Hepatitis A + B"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Brand Name</label>
              <input
                type="text"
                value={form.brand_name}
                onChange={(e) =>
                  setForm((p) => ({ ...p, brand_name: e.target.value }))
                }
                placeholder="e.g. Twinrix"
              />
            </div>
            <div className="form-group">
              <label>Dose Type</label>
              <input
                type="text"
                value={form.dose_type}
                onChange={(e) =>
                  setForm((p) => ({ ...p, dose_type: e.target.value }))
                }
                placeholder="e.g. Booster, 3-dose series"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Date Administered</label>
              <input
                type="date"
                value={form.date_administered}
                onChange={(e) =>
                  setForm((p) => ({ ...p, date_administered: e.target.value }))
                }
              />
            </div>
            <div className="form-group">
              <label>Expiry Date (blank = lifetime)</label>
              <input
                type="date"
                value={form.expiry_date}
                onChange={(e) =>
                  setForm((p) => ({ ...p, expiry_date: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-group">
            <label>Batch / Certificate Number</label>
            <input
              type="text"
              value={form.batch_number}
              onChange={(e) =>
                setForm((p) => ({ ...p, batch_number: e.target.value }))
              }
              placeholder="Lot/batch number"
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) =>
                setForm((p) => ({ ...p, notes: e.target.value }))
              }
              rows={2}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-save" disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
