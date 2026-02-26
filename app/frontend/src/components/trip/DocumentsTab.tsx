import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BiFile, BiTrash, BiShieldQuarter } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type { TripDocumentsTabData } from "./types";

interface DocumentsTabProps {
  tripId: string;
  readOnly: boolean;
}

function formatFileSize(bytes: number | null): string {
  if (bytes === null || bytes === 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsTab({ tripId, readOnly }: DocumentsTabProps) {
  const navigate = useNavigate();
  const [data, setData] = useState<TripDocumentsTabData | null>(null);
  const [loading, setLoading] = useState(true);
  const [vaultUnlocked, setVaultUnlocked] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadLabel, setUploadLabel] = useState("");
  const [uploadNotes, setUploadNotes] = useState("");
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = useCallback(() => {
    apiFetch(`/api/v1/travels/trips/${tripId}/documents-tab`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load documents tab");
        return r.json();
      })
      .then((d) => setData(d))
      .catch((err) => console.error("Failed to load documents tab:", err))
      .finally(() => setLoading(false));
  }, [tripId]);

  useEffect(() => {
    fetchData();
    apiFetch("/api/auth/vault/status")
      .then((r) => r.json())
      .then((d) => setVaultUnlocked(d.unlocked === true))
      .catch(() => setVaultUnlocked(false));
  }, [fetchData]);

  useEffect(() => {
    const onVaultChange = () => {
      apiFetch("/api/auth/vault/status")
        .then((r) => r.json())
        .then((d) => setVaultUnlocked(d.unlocked === true))
        .catch(() => setVaultUnlocked(false));
    };
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile || !uploadLabel.trim()) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", selectedFile);
      form.append("label", uploadLabel.trim());
      if (uploadNotes.trim()) form.append("notes", uploadNotes.trim());
      const res = await apiFetch(`/api/v1/travels/trips/${tripId}/documents`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error("Upload failed");
      setUploadLabel("");
      setUploadNotes("");
      setSelectedFile(null);
      setShowUploadForm(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchData();
    } catch (err) {
      console.error("Failed to upload document:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm("Delete this document?")) return;
    try {
      await apiFetch(`/api/v1/travels/trips/${tripId}/documents/${docId}`, {
        method: "DELETE",
      });
      fetchData();
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  const handleViewFile = (docId: number) => {
    if (!vaultUnlocked) {
      alert("Unlock the vault to view documents.");
      return;
    }
    window.open(
      `/api/v1/travels/trips/${tripId}/documents/${docId}/file`,
      "_blank",
    );
  };

  if (loading) {
    return (
      <div className="trip-documents-tab">
        <p>Loading documents...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="trip-documents-tab">
        <p>Failed to load documents.</p>
      </div>
    );
  }

  return (
    <div className="trip-documents-tab">
      {/* What to bring — passports (from visas) + vaccination book (if required) */}
      {(data.passports.length > 0 || data.required_vaccines.length > 0) && (
        <div className="trip-docs-section">
          <div className="trip-docs-section-header">
            <h3>What to bring</h3>
            <button
              className="btn-add-inline"
              onClick={() => navigate("/admin/documents")}
            >
              Manage in Vault
            </button>
          </div>
          {data.passports.map((p) => (
            <div key={p.id} className="trip-doc-card">
              <div className="trip-doc-card-main">
                <span className="trip-doc-card-label">
                  {p.issuing_country && (
                    <Flag code={p.issuing_country} size={16} />
                  )}
                  {p.label}
                </span>
                {p.expiry_date && (
                  <span className="trip-doc-card-meta">
                    Expires: {p.expiry_date}
                  </span>
                )}
              </div>
              {p.has_files && (
                <span className="trip-doc-card-badge">has scan</span>
              )}
            </div>
          ))}
          {data.required_vaccines.length > 0 && (
            <div
              className="trip-doc-card trip-doc-card-highlight"
              onClick={() => navigate("/admin/documents/vaccinations")}
            >
              <div className="trip-doc-card-main">
                <span className="trip-doc-card-label">
                  <BiShieldQuarter />
                  Vaccination Book (ICV)
                </span>
                <span className="trip-doc-card-meta">
                  Required: {data.required_vaccines.join(", ")}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Travel Documents section */}
      {data.travel_docs.length > 0 && (
        <div className="trip-docs-section">
          <div className="trip-docs-section-header">
            <h3>Visas & Travel Documents</h3>
            <button
              className="btn-add-inline"
              onClick={() => navigate("/admin/documents/visas")}
            >
              Manage in Vault
            </button>
          </div>
          <div className="travel-doc-badges">
            {data.travel_docs.map((td) => (
              <span
                key={td.id}
                className={`travel-doc-badge${td.expires_before_trip ? " travel-doc-expiring" : ""}`}
                onClick={() => navigate("/admin/documents/visas")}
              >
                {td.label}
                {td.entry_type && (
                  <span className="travel-doc-entry-type">{td.entry_type}</span>
                )}
                {td.passport_label && (
                  <span className="travel-doc-passport">
                    {td.passport_label}
                  </span>
                )}
                {td.valid_until && (
                  <span className="travel-doc-validity">
                    until {td.valid_until}
                  </span>
                )}
                {td.expires_before_trip && (
                  <span className="travel-doc-warning">expires!</span>
                )}
                {td.has_files && <span className="travel-doc-file">📎</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Trip Documents section */}
      <div className="trip-docs-section">
        <div className="trip-docs-section-header">
          <h3>Trip Documents ({data.documents.length})</h3>
          {!readOnly && (
            <button
              type="button"
              className="btn-add-inline"
              onClick={() => {
                setShowUploadForm(true);
                setSelectedFile(null);
                setUploadLabel("");
                setUploadNotes("");
              }}
            >
              + Add
            </button>
          )}
        </div>

        {/* Upload form */}
        {showUploadForm && !readOnly && (
          <div className="trip-doc-upload-form">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,image/*"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
            <input
              type="text"
              placeholder="Label (e.g., Travel Insurance)"
              value={uploadLabel}
              onChange={(e) => setUploadLabel(e.target.value)}
              className="trip-doc-upload-label-input"
            />
            <input
              type="text"
              placeholder="Notes (optional)"
              value={uploadNotes}
              onChange={(e) => setUploadNotes(e.target.value)}
              className="trip-doc-upload-label-input"
            />
            <div className="trip-doc-upload-actions">
              <button
                className="btn-primary btn-sm"
                disabled={!selectedFile || !uploadLabel.trim() || uploading}
                onClick={handleUpload}
              >
                {uploading ? "Uploading..." : "Upload"}
              </button>
              <button
                className="btn-secondary btn-sm"
                onClick={() => {
                  setShowUploadForm(false);
                  setSelectedFile(null);
                  setUploadLabel("");
                  setUploadNotes("");
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {data.documents.length === 0 && !showUploadForm ? (
          <p className="flight-empty">No trip documents uploaded yet.</p>
        ) : (
          <div className="transport-booking-list">
            {data.documents.map((doc) => (
              <div key={doc.id} className="transport-booking-card">
                <div className="transport-booking-main">
                  <div className="transport-booking-header">
                    <BiFile
                      style={{ verticalAlign: "middle", marginRight: 4 }}
                    />
                    <span className="transport-booking-operator">
                      {doc.label}
                    </span>
                  </div>
                  <div className="transport-booking-details">
                    {doc.document_name && (
                      <span className="flight-badge">{doc.document_name}</span>
                    )}
                    {doc.document_size && (
                      <span className="flight-badge">
                        {formatFileSize(doc.document_size)}
                      </span>
                    )}
                    {doc.created_at && (
                      <span className="flight-badge">
                        {new Date(doc.created_at).toLocaleDateString("en-GB", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </span>
                    )}
                  </div>
                  {doc.notes && (
                    <div className="transport-booking-route">
                      <div className="transport-booking-route-row">
                        <span className="transport-booking-route-label">
                          Note
                        </span>
                        <span>{doc.notes}</span>
                      </div>
                    </div>
                  )}
                </div>
                <div className="transport-booking-actions">
                  <button
                    className="transport-booking-doc-btn"
                    onClick={() => handleViewFile(doc.id)}
                    title={
                      vaultUnlocked
                        ? `View ${doc.document_name || "file"}`
                        : "Unlock vault to view"
                    }
                  >
                    <BiFile size={16} />
                  </button>
                  {!readOnly && (
                    <button
                      className="flight-delete-btn"
                      onClick={() => handleDelete(doc.id)}
                      title="Delete document"
                    >
                      <BiTrash />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
