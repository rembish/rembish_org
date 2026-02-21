import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BiLock, BiPlus } from "react-icons/bi";
import { useVaultAuth } from "../../hooks/useVaultAuth";
import { apiFetch } from "../../lib/api";
import type {
  DocSection,
  VaultDocument,
  VaultTravelDoc,
  VaultUser,
  VaultVaccination,
} from "./types";
import { DOC_SECTIONS } from "./types";
import VaultDocumentsSection from "./VaultDocumentsSection";
import VaultVaccinationsSection from "./VaultVaccinationsSection";
import VaultTravelDocsSection from "./VaultTravelDocsSection";
import DocumentFormModal from "./VaultDocumentForm";
import VaccinationFormModal from "./VaultVaccinationForm";
import TravelDocFormModal from "./VaultTravelDocForm";

interface Props {
  activeSection: DocSection;
  onSectionChange: (section: DocSection) => void;
}

export default function DocumentsTab({
  activeSection,
  onSectionChange,
}: Props) {
  const { unlocked, loading, vaultFetch } = useVaultAuth();
  const [documents, setDocuments] = useState<VaultDocument[]>([]);
  const [vaccinations, setVaccinations] = useState<VaultVaccination[]>([]);
  const [travelDocs, setTravelDocs] = useState<VaultTravelDoc[]>([]);
  const [users, setUsers] = useState<VaultUser[]>([]);
  const [myUserId, setMyUserId] = useState<number | null>(null);
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<VaultDocument | null>(null);
  const [vaxModalOpen, setVaxModalOpen] = useState(false);
  const [editingVax, setEditingVax] = useState<VaultVaccination | null>(null);
  const [travelDocModalOpen, setTravelDocModalOpen] = useState(false);
  const [editingTravelDoc, setEditingTravelDoc] =
    useState<VaultTravelDoc | null>(null);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [copied, setCopied] = useState<string | null>(null);
  const [showExpiredTravelDocs, setShowExpiredTravelDocs] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const newTravelDocCountry = searchParams.get("newTravelDoc");

  const fetchData = useCallback(async () => {
    const [docsRes, vaxRes, tdocsRes] = await Promise.all([
      vaultFetch("/api/v1/admin/vault/documents"),
      vaultFetch("/api/v1/admin/vault/vaccinations"),
      vaultFetch("/api/v1/admin/vault/travel-docs"),
    ]);
    if (docsRes?.ok) {
      const data = await docsRes.json();
      setDocuments(data.documents);
    }
    if (vaxRes?.ok) {
      const data = await vaxRes.json();
      setVaccinations(data.vaccinations);
    }
    if (tdocsRes?.ok) {
      const data = await tdocsRes.json();
      setTravelDocs(data.travel_docs);
    }
  }, [vaultFetch]);

  const fetchUsers = useCallback(() => {
    Promise.all([
      apiFetch("/api/v1/admin/users/").then((r) => r.json()),
      apiFetch("/api/auth/me").then((r) => r.json()),
    ])
      .then(([usersData, me]) => {
        const others: VaultUser[] = (usersData.users || []).map(
          (u: VaultUser) => ({
            id: u.id,
            email: u.email,
            name: u.name,
            nickname: u.nickname,
            picture: u.picture,
          }),
        );
        if (me) {
          setMyUserId(me.id);
          others.unshift({
            id: me.id,
            email: me.email,
            name: me.name,
            nickname: me.nickname,
            picture: me.picture,
          });
        }
        setUsers(others);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    if (unlocked) fetchData();
  }, [unlocked, fetchData]);

  // Auto-open travel doc form when navigating from trip info with ?newTravelDoc=XX
  useEffect(() => {
    if (newTravelDocCountry && unlocked && users.length > 0) {
      onSectionChange("visas");
      setEditingTravelDoc(null);
      setTravelDocModalOpen(true);
      searchParams.delete("newTravelDoc");
      setSearchParams(searchParams, { replace: true });
    }
  }, [
    newTravelDocCountry,
    unlocked,
    users,
    searchParams,
    setSearchParams,
    onSectionChange,
  ]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  const toggleFilesExpanded = (key: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleFileUpload = async (
    entityType: string,
    entityId: number,
    file: File,
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("entity_type", entityType);
    fd.append("entity_id", String(entityId));
    const res = await vaultFetch("/api/v1/admin/vault/files/upload", {
      method: "POST",
      body: fd,
    });
    if (res?.ok) fetchData();
  };

  const handleDeleteFile = async (fileId: number) => {
    if (!confirm("Delete this file?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/files/${fileId}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

  const handleViewFile = async (fileId: number) => {
    const w = window.open("about:blank", "_blank");
    const res = await vaultFetch(`/api/v1/admin/vault/files/${fileId}/url`);
    if (res?.ok) {
      const data = await res.json();
      if (w) w.location.href = data.url;
      else window.location.href = data.url;
    } else {
      w?.close();
    }
  };

  // Document handlers
  const handleSaveDoc = async (formData: {
    user_id: number;
    doc_type: string;
    label: string;
    proper_name: string;
    issuing_country: string;
    issue_date: string;
    expiry_date: string;
    number: string;
    notes: string;
  }) => {
    const body = {
      user_id: formData.user_id,
      doc_type: formData.doc_type,
      label: formData.label,
      proper_name: formData.proper_name || null,
      issuing_country: formData.issuing_country || null,
      issue_date: formData.issue_date || null,
      expiry_date: formData.expiry_date || null,
      number: formData.number || null,
      notes: formData.notes || null,
    };
    const url = editingDoc
      ? `/api/v1/admin/vault/documents/${editingDoc.id}`
      : "/api/v1/admin/vault/documents";
    const method = editingDoc ? "PUT" : "POST";
    const res = await vaultFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res?.ok) {
      const data = await res?.json().catch(() => null);
      throw new Error(data?.detail || "Failed to save document");
    }
    setDocModalOpen(false);
    setEditingDoc(null);
    fetchData();
  };

  const handleDeleteDoc = async (id: number) => {
    if (!confirm("Archive this document?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/documents/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

  const handleRestoreDoc = async (id: number) => {
    const res = await vaultFetch(
      `/api/v1/admin/vault/documents/${id}/restore`,
      { method: "POST" },
    );
    if (res?.ok) fetchData();
  };

  // Vaccination handlers
  const handleSaveVax = async (formData: {
    user_id: number;
    vaccine_name: string;
    brand_name: string;
    dose_type: string;
    date_administered: string;
    expiry_date: string;
    batch_number: string;
    notes: string;
  }) => {
    const body = {
      user_id: formData.user_id,
      vaccine_name: formData.vaccine_name,
      brand_name: formData.brand_name || null,
      dose_type: formData.dose_type || null,
      date_administered: formData.date_administered || null,
      expiry_date: formData.expiry_date || null,
      batch_number: formData.batch_number || null,
      notes: formData.notes || null,
    };
    const url = editingVax
      ? `/api/v1/admin/vault/vaccinations/${editingVax.id}`
      : "/api/v1/admin/vault/vaccinations";
    const method = editingVax ? "PUT" : "POST";
    const res = await vaultFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res?.ok) {
      const data = await res?.json().catch(() => null);
      throw new Error(data?.detail || "Failed to save vaccination");
    }
    setVaxModalOpen(false);
    setEditingVax(null);
    fetchData();
  };

  const handleDeleteVax = async (id: number) => {
    if (!confirm("Delete this vaccination record?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/vaccinations/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

  // Travel doc handlers
  const handleSaveTravelDoc = async (formData: {
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
  }) => {
    const body = {
      user_id: formData.user_id,
      doc_type: formData.doc_type,
      label: formData.label,
      document_id: formData.document_id,
      country_code: formData.country_code || null,
      valid_from: formData.valid_from || null,
      valid_until: formData.valid_until || null,
      entry_type: formData.entry_type || null,
      notes: formData.notes || null,
    };
    const url = editingTravelDoc
      ? `/api/v1/admin/vault/travel-docs/${editingTravelDoc.id}`
      : "/api/v1/admin/vault/travel-docs";
    const method = editingTravelDoc ? "PUT" : "POST";
    const res = await vaultFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res?.ok) {
      const data = await res?.json().catch(() => null);
      throw new Error(data?.detail || "Failed to save travel document");
    }
    const saved = await res.json();
    if (formData.file && !editingTravelDoc) {
      const fd = new FormData();
      fd.append("file", formData.file);
      fd.append("entity_type", "travel_doc");
      fd.append("entity_id", String(saved.id));
      await vaultFetch("/api/v1/admin/vault/files/upload", {
        method: "POST",
        body: fd,
      });
    }
    setTravelDocModalOpen(false);
    setEditingTravelDoc(null);
    fetchData();
  };

  const handleDeleteTravelDoc = async (id: number) => {
    if (!confirm("Delete this travel document?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/travel-docs/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

  const handleMarkUsed = async (id: number) => {
    if (!confirm("Mark this document as used? This sets the expiry to today."))
      return;
    const res = await vaultFetch(
      `/api/v1/admin/vault/travel-docs/${id}/mark-used`,
      { method: "POST" },
    );
    if (res?.ok) fetchData();
  };

  const getUser = (userId: number) => users.find((u) => u.id === userId);
  const getUserName = (userId: number) => {
    if (userId === myUserId) return "Me";
    const u = getUser(userId);
    return u?.nickname || u?.name || `User #${userId}`;
  };

  if (loading) return <p>Loading...</p>;

  if (!unlocked) {
    return (
      <div className="vault-locked">
        <BiLock size={48} />
        <h2>Vault is Locked</h2>
        <p>Use the lock icon in the top-right corner to unlock.</p>
      </div>
    );
  }

  return (
    <div className="vault-content">
      <div className="vault-sub-tabs">
        {DOC_SECTIONS.map((s) => (
          <button
            key={s.key}
            className={`vault-sub-tab${activeSection === s.key ? " active" : ""}`}
            onClick={() => onSectionChange(s.key)}
          >
            {s.label}
          </button>
        ))}
        <div className="vault-sub-tabs-actions">
          {activeSection === "visas" && (
            <label className="vault-toggle-label">
              <input
                type="checkbox"
                checked={showExpiredTravelDocs}
                onChange={(e) => setShowExpiredTravelDocs(e.target.checked)}
              />
              Show expired
            </label>
          )}
          <button
            className="btn-icon"
            onClick={() => {
              if (activeSection === "ids") {
                setEditingDoc(null);
                setDocModalOpen(true);
              } else if (activeSection === "vaccinations") {
                setEditingVax(null);
                setVaxModalOpen(true);
              } else {
                setEditingTravelDoc(null);
                setTravelDocModalOpen(true);
              }
            }}
            title={
              activeSection === "ids"
                ? "Add document"
                : activeSection === "vaccinations"
                  ? "Add vaccination"
                  : "Add travel document"
            }
          >
            <BiPlus />
          </button>
        </div>
      </div>

      {activeSection === "ids" && (
        <VaultDocumentsSection
          documents={documents}
          copied={copied}
          expandedFiles={expandedFiles}
          hideHeader
          onEditDoc={(doc) => {
            setEditingDoc(doc);
            setDocModalOpen(true);
          }}
          onAddDoc={() => {
            setEditingDoc(null);
            setDocModalOpen(true);
          }}
          onDeleteDoc={handleDeleteDoc}
          onRestoreDoc={handleRestoreDoc}
          onCopy={handleCopy}
          onToggleFiles={toggleFilesExpanded}
          onFileUpload={handleFileUpload}
          onViewFile={handleViewFile}
          onDeleteFile={handleDeleteFile}
          getUserName={getUserName}
          getUser={getUser}
        />
      )}

      {activeSection === "vaccinations" && (
        <VaultVaccinationsSection
          vaccinations={vaccinations}
          copied={copied}
          expandedFiles={expandedFiles}
          hideHeader
          onEditVax={(vax) => {
            setEditingVax(vax);
            setVaxModalOpen(true);
          }}
          onAddVax={() => {
            setEditingVax(null);
            setVaxModalOpen(true);
          }}
          onDeleteVax={handleDeleteVax}
          onCopy={handleCopy}
          onToggleFiles={toggleFilesExpanded}
          onFileUpload={handleFileUpload}
          onViewFile={handleViewFile}
          onDeleteFile={handleDeleteFile}
          getUserName={getUserName}
          getUser={getUser}
        />
      )}

      {activeSection === "visas" && (
        <VaultTravelDocsSection
          travelDocs={travelDocs}
          showExpiredTravelDocs={showExpiredTravelDocs}
          expandedFiles={expandedFiles}
          hideHeader
          onShowExpiredChange={setShowExpiredTravelDocs}
          onEditTravelDoc={(doc) => {
            setEditingTravelDoc(doc);
            setTravelDocModalOpen(true);
          }}
          onAddTravelDoc={() => {
            setEditingTravelDoc(null);
            setTravelDocModalOpen(true);
          }}
          onDeleteTravelDoc={handleDeleteTravelDoc}
          onMarkUsed={handleMarkUsed}
          onToggleFiles={toggleFilesExpanded}
          onViewFile={handleViewFile}
          onDeleteFile={handleDeleteFile}
          getUserName={getUserName}
          getUser={getUser}
        />
      )}

      {docModalOpen && (
        <DocumentFormModal
          isOpen={docModalOpen}
          onClose={() => {
            setDocModalOpen(false);
            setEditingDoc(null);
          }}
          onSave={handleSaveDoc}
          initialData={editingDoc}
          users={users}
        />
      )}

      {vaxModalOpen && (
        <VaccinationFormModal
          isOpen={vaxModalOpen}
          onClose={() => {
            setVaxModalOpen(false);
            setEditingVax(null);
          }}
          onSave={handleSaveVax}
          initialData={editingVax}
          users={users}
        />
      )}

      {travelDocModalOpen && (
        <TravelDocFormModal
          isOpen={travelDocModalOpen}
          onClose={() => {
            setTravelDocModalOpen(false);
            setEditingTravelDoc(null);
          }}
          onSave={handleSaveTravelDoc}
          initialData={editingTravelDoc}
          users={users}
          documents={documents}
          vaultFetch={vaultFetch}
          defaultCountryCode={newTravelDocCountry}
        />
      )}
    </div>
  );
}
