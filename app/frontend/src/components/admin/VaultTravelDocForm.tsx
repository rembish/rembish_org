import { useEffect, useState } from "react";
import { BiCloudUpload, BiFile } from "react-icons/bi";
import type {
  VaultTravelDoc,
  VaultUser,
  VaultDocument,
  ExtractedDocMetadata,
} from "./types";
import { TRAVEL_DOC_TYPE_LABELS, fmtFileSize } from "./types";

export default function TravelDocFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  users,
  documents,
  vaultFetch,
  defaultCountryCode,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    user_id: number;
    doc_type: string;
    label: string;
    document_id: number | null;
    country_code: string;
    valid_from: string;
    valid_until: string;
    entry_type: string;
    notes: string;
    file: File | null;
  }) => Promise<void>;
  initialData: VaultTravelDoc | null;
  users: VaultUser[];
  documents: VaultDocument[];
  vaultFetch: (url: string, opts?: RequestInit) => Promise<Response | null>;
  defaultCountryCode?: string | null;
}) {
  const [form, setForm] = useState({
    user_id: initialData?.user_id ?? users[0]?.id ?? 0,
    doc_type: initialData?.doc_type ?? "e_visa",
    label: initialData?.label ?? "",
    document_id: initialData?.document_id ?? (null as number | null),
    country_code: initialData?.country_code ?? defaultCountryCode ?? "",
    valid_from: initialData?.valid_from ?? "",
    valid_until: initialData?.valid_until ?? "",
    entry_type: initialData?.entry_type ?? "",
    notes: initialData?.notes_decrypted ?? "",
  });
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setForm({
        user_id: initialData?.user_id ?? users[0]?.id ?? 0,
        doc_type: initialData?.doc_type ?? "e_visa",
        label: initialData?.label ?? "",
        document_id: initialData?.document_id ?? null,
        country_code: initialData?.country_code ?? defaultCountryCode ?? "",
        valid_from: initialData?.valid_from ?? "",
        valid_until: initialData?.valid_until ?? "",
        entry_type: initialData?.entry_type ?? "",
        notes: initialData?.notes_decrypted ?? "",
      });
      setFile(null);
      setError(null);
    }
  }, [isOpen, initialData, users, defaultCountryCode]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleExtract = async () => {
    if (!file) return;
    setExtracting(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await vaultFetch("/api/v1/admin/vault/travel-docs/extract", {
        method: "POST",
        body: fd,
      });
      if (res?.ok) {
        const data: ExtractedDocMetadata = await res.json();
        if (data.error) {
          setError(data.error);
        } else {
          setForm((prev) => ({
            ...prev,
            doc_type: data.doc_type || prev.doc_type,
            label: data.label || prev.label,
            document_id: data.document_id ?? prev.document_id,
            country_code: data.country_code || prev.country_code,
            valid_from: data.valid_from || prev.valid_from,
            valid_until: data.valid_until || prev.valid_until,
            entry_type: data.entry_type || prev.entry_type,
            notes: data.notes || prev.notes,
          }));
        }
      }
    } catch {
      setError("Extraction failed");
    } finally {
      setExtracting(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.label.trim()) {
      setError("Label is required");
      return;
    }
    setSaving(true);
    try {
      await onSave({ ...form, document_id: form.document_id, file });
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
          <h2>
            {initialData ? "Edit Travel Document" : "Add Travel Document"}
          </h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}
          {!initialData && (
            <div
              className={`travel-doc-dropzone${dragOver ? " dragover" : ""}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              {file ? (
                <div className="vault-card-file-info">
                  <BiFile /> {file.name} ({fmtFileSize(file.size)})
                  <button
                    type="button"
                    className="btn-extract"
                    onClick={handleExtract}
                    disabled={extracting}
                  >
                    {extracting ? "Extracting..." : "Extract with AI"}
                  </button>
                </div>
              ) : (
                <label>
                  <BiCloudUpload size={24} /> Drop PDF/image here or{" "}
                  <input
                    type="file"
                    accept=".pdf,image/jpeg,image/png,image/webp"
                    style={{ display: "none" }}
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  <span className="btn-extract">browse</span>
                </label>
              )}
            </div>
          )}
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
            <label>Linked Passport</label>
            <select
              value={form.document_id ?? ""}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  document_id: e.target.value ? Number(e.target.value) : null,
                }))
              }
            >
              <option value="">— None —</option>
              {documents
                .filter(
                  (d) =>
                    d.doc_type === "passport" &&
                    !d.is_archived &&
                    d.user_id === form.user_id,
                )
                .map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.label}
                    {d.issuing_country ? ` (${d.issuing_country})` : ""}
                  </option>
                ))}
            </select>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Document Type *</label>
              <select
                value={form.doc_type}
                onChange={(e) =>
                  setForm((p) => ({ ...p, doc_type: e.target.value }))
                }
              >
                {Object.entries(TRAVEL_DOC_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Country Code</label>
              <input
                type="text"
                value={form.country_code}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    country_code: e.target.value.toUpperCase().slice(0, 2),
                  }))
                }
                placeholder="e.g. IN, GB"
                maxLength={2}
              />
            </div>
          </div>
          <div className="form-group">
            <label>Label *</label>
            <input
              type="text"
              value={form.label}
              onChange={(e) =>
                setForm((p) => ({ ...p, label: e.target.value }))
              }
              placeholder="e.g. India e-Visa, UK ETA"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Valid From</label>
              <input
                type="date"
                value={form.valid_from}
                onChange={(e) =>
                  setForm((p) => ({ ...p, valid_from: e.target.value }))
                }
              />
            </div>
            <div className="form-group">
              <label>Valid Until</label>
              <input
                type="date"
                value={form.valid_until}
                onChange={(e) =>
                  setForm((p) => ({ ...p, valid_until: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-group">
            <label>Entry Type</label>
            <select
              value={form.entry_type}
              onChange={(e) =>
                setForm((p) => ({ ...p, entry_type: e.target.value }))
              }
            >
              <option value="">—</option>
              <option value="single">Single entry</option>
              <option value="double">Double entry</option>
              <option value="multiple">Multiple entry</option>
            </select>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) =>
                setForm((p) => ({ ...p, notes: e.target.value }))
              }
              rows={2}
              placeholder="Visa number, conditions, etc."
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
