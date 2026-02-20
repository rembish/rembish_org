import { useEffect, useState } from "react";
import type { VaultDocument, VaultUser } from "./types";

export default function DocumentFormModal({
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
    doc_type: string;
    label: string;
    proper_name: string;
    issuing_country: string;
    issue_date: string;
    expiry_date: string;
    number: string;
    notes: string;
  }) => Promise<void>;
  initialData: VaultDocument | null;
  users: VaultUser[];
}) {
  const [form, setForm] = useState({
    user_id: initialData?.user_id ?? users[0]?.id ?? 0,
    doc_type: initialData?.doc_type ?? "passport",
    label: initialData?.label ?? "",
    proper_name: initialData?.proper_name ?? "",
    issuing_country: initialData?.issuing_country ?? "",
    issue_date: initialData?.issue_date ?? "",
    expiry_date: initialData?.expiry_date ?? "",
    number: initialData?.number_decrypted ?? "",
    notes: initialData?.notes_decrypted ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm({
        user_id: initialData?.user_id ?? users[0]?.id ?? 0,
        doc_type: initialData?.doc_type ?? "passport",
        label: initialData?.label ?? "",
        proper_name: initialData?.proper_name ?? "",
        issuing_country: initialData?.issuing_country ?? "",
        issue_date: initialData?.issue_date ?? "",
        expiry_date: initialData?.expiry_date ?? "",
        number: initialData?.number_decrypted ?? "",
        notes: initialData?.notes_decrypted ?? "",
      });
      setError(null);
    }
  }, [isOpen, initialData, users]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.label.trim()) {
      setError("Label is required");
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
          <h2>{initialData ? "Edit Document" : "Add Document"}</h2>
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
            <label>Type *</label>
            <select
              value={form.doc_type}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  doc_type: e.target.value as
                    | "passport"
                    | "id_card"
                    | "drivers_license",
                }))
              }
            >
              <option value="passport">Passport</option>
              <option value="id_card">ID Card</option>
              <option value="drivers_license">Driver&apos;s License</option>
            </select>
          </div>
          <div className="form-group">
            <label>Label *</label>
            <input
              type="text"
              value={form.label}
              onChange={(e) =>
                setForm((p) => ({ ...p, label: e.target.value }))
              }
              placeholder="e.g. CZ Passport"
            />
          </div>
          <div className="form-group">
            <label>Official Name (as on document)</label>
            <input
              type="text"
              value={form.proper_name}
              onChange={(e) =>
                setForm((p) => ({ ...p, proper_name: e.target.value }))
              }
              placeholder="e.g. ALEX REMBISH"
            />
          </div>
          <div className="form-group">
            <label>Issuing Country (ISO alpha-2)</label>
            <input
              type="text"
              value={form.issuing_country}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  issuing_country: e.target.value.toUpperCase(),
                }))
              }
              placeholder="CZ"
              maxLength={2}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Issue Date</label>
              <input
                type="date"
                value={form.issue_date}
                onChange={(e) =>
                  setForm((p) => ({ ...p, issue_date: e.target.value }))
                }
              />
            </div>
            <div className="form-group">
              <label>Expiry Date</label>
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
            <label>Number</label>
            <input
              type="text"
              value={form.number}
              onChange={(e) =>
                setForm((p) => ({ ...p, number: e.target.value }))
              }
              placeholder="Document number"
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
