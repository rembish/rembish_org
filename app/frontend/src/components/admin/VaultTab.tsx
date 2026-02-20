import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BiLock } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import type {
  VaultDocument,
  VaultLoyaltyProgram,
  VaultVaccination,
  VaultTravelDoc,
  VaultUser,
  ProgramOption,
} from "./types";
import VaultDocumentsSection from "./VaultDocumentsSection";
import VaultProgramsSection from "./VaultProgramsSection";
import VaultVaccinationsSection from "./VaultVaccinationsSection";
import VaultTravelDocsSection from "./VaultTravelDocsSection";
import DocumentFormModal from "./VaultDocumentForm";
import ProgramFormModal from "./VaultProgramForm";
import VaccinationFormModal from "./VaultVaccinationForm";
import TravelDocFormModal from "./VaultTravelDocForm";

export default function VaultTab() {
  const [unlocked, setUnlocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<VaultDocument[]>([]);
  const [programs, setPrograms] = useState<VaultLoyaltyProgram[]>([]);
  const [programOptions, setProgramOptions] = useState<ProgramOption[]>([]);
  const [users, setUsers] = useState<VaultUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [progModalOpen, setProgModalOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<VaultDocument | null>(null);
  const [editingProg, setEditingProg] = useState<VaultLoyaltyProgram | null>(
    null,
  );
  const [vaccinations, setVaccinations] = useState<VaultVaccination[]>([]);
  const [vaxModalOpen, setVaxModalOpen] = useState(false);
  const [editingVax, setEditingVax] = useState<VaultVaccination | null>(null);
  const [travelDocs, setTravelDocs] = useState<VaultTravelDoc[]>([]);
  const [travelDocModalOpen, setTravelDocModalOpen] = useState(false);
  const [editingTravelDoc, setEditingTravelDoc] =
    useState<VaultTravelDoc | null>(null);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [copied, setCopied] = useState<string | null>(null);
  const [expandedAlliances, setExpandedAlliances] = useState<Set<string>>(
    new Set(),
  );
  const [myUserId, setMyUserId] = useState<number | null>(null);
  const [airlineSearch, setAirlineSearch] = useState("");
  const [showExpiredTravelDocs, setShowExpiredTravelDocs] = useState(false);
  const lockTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const newTravelDocCountry = searchParams.get("newTravelDoc");

  const checkStatus = useCallback(() => {
    apiFetch("/api/auth/vault/status")
      .then((res) => res.json())
      .then((data) => {
        setUnlocked(data.unlocked);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const vaultFetch = useCallback(async (url: string, opts?: RequestInit) => {
    const res = await apiFetch(url, opts);
    if (res.status === 401) {
      const data = await res.json().catch(() => null);
      if (data?.detail === "vault_locked") {
        setUnlocked(false);
        return null;
      }
    }
    return res;
  }, []);

  const fetchData = useCallback(async () => {
    const params = selectedUserId ? `?user_id=${selectedUserId}` : "";
    const [docsRes, progsRes, optionsRes, vaxRes, tdocsRes] = await Promise.all(
      [
        vaultFetch(`/api/v1/admin/vault/documents${params}`),
        vaultFetch(`/api/v1/admin/vault/programs${params}`),
        vaultFetch("/api/v1/admin/vault/program-options"),
        vaultFetch(`/api/v1/admin/vault/vaccinations${params}`),
        vaultFetch(`/api/v1/admin/vault/travel-docs${params}`),
      ],
    );
    if (docsRes?.ok) {
      const data = await docsRes.json();
      setDocuments(data.documents);
    }
    if (progsRes?.ok) {
      const data = await progsRes.json();
      setPrograms(data.programs);
    }
    if (optionsRes?.ok) {
      const data = await optionsRes.json();
      setProgramOptions(data.programs);
    }
    if (vaxRes?.ok) {
      const data = await vaxRes.json();
      setVaccinations(data.vaccinations);
    }
    if (tdocsRes?.ok) {
      const data = await tdocsRes.json();
      setTravelDocs(data.travel_docs);
    }
  }, [vaultFetch, selectedUserId]);

  const fetchUsers = useCallback(() => {
    // Fetch other users + current admin (the users endpoint excludes self)
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
    checkStatus();
    fetchUsers();
  }, [checkStatus, fetchUsers]);

  useEffect(() => {
    if (unlocked) {
      fetchData();
      // Auto-lock timer: 10 min
      if (lockTimerRef.current) clearTimeout(lockTimerRef.current);
      lockTimerRef.current = setTimeout(() => setUnlocked(false), 600_000);
    }
    return () => {
      if (lockTimerRef.current) clearTimeout(lockTimerRef.current);
    };
  }, [unlocked, fetchData]);

  // Auto-open travel doc form when navigating from trip info with ?newTravelDoc=XX
  useEffect(() => {
    if (newTravelDocCountry && unlocked && users.length > 0) {
      setEditingTravelDoc(null);
      setTravelDocModalOpen(true);
      // Clear the param so it doesn't re-trigger
      searchParams.delete("newTravelDoc");
      setSearchParams(searchParams, { replace: true });
    }
  }, [newTravelDocCountry, unlocked, users, searchParams, setSearchParams]);

  useEffect(() => {
    const onVaultChange = () => checkStatus();
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, [checkStatus]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
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
      {
        method: "POST",
      },
    );
    if (res?.ok) fetchData();
  };

  const handleDeleteProg = async (id: number) => {
    if (!confirm("Delete this loyalty program?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/programs/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

  const handleToggleFavorite = async (id: number) => {
    const res = await vaultFetch(
      `/api/v1/admin/vault/programs/${id}/favorite`,
      {
        method: "POST",
      },
    );
    if (res?.ok) fetchData();
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
    // Upload file if provided (new docs only)
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
    const res = await vaultFetch(`/api/v1/admin/vault/files/${fileId}/url`);
    if (res?.ok) {
      const data = await res.json();
      window.open(data.url, "_blank");
    }
  };

  const toggleFilesExpanded = (key: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleDeleteVax = async (id: number) => {
    if (!confirm("Delete this vaccination record?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/vaccinations/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
  };

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

  const handleSaveProg = async (formData: {
    user_id: number;
    program_name: string;
    alliance: string;
    membership_number: string;
    notes: string;
  }) => {
    const body = {
      user_id: formData.user_id,
      program_name: formData.program_name,
      alliance: formData.alliance,
      membership_number: formData.membership_number || null,
      notes: formData.notes || null,
    };
    const isNew = !editingProg || editingProg.id === 0;
    const url = isNew
      ? "/api/v1/admin/vault/programs"
      : `/api/v1/admin/vault/programs/${editingProg!.id}`;
    const method = isNew ? "POST" : "PUT";
    const res = await vaultFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res?.ok) {
      const data = await res?.json().catch(() => null);
      throw new Error(data?.detail || "Failed to save program");
    }
    setProgModalOpen(false);
    setEditingProg(null);
    fetchData();
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

  const getUser = (userId: number) => users.find((u) => u.id === userId);

  const getUserName = (userId: number) => {
    if (userId === myUserId) return "Me";
    const u = getUser(userId);
    return u?.nickname || u?.name || `User #${userId}`;
  };

  return (
    <div className="vault-content">
      <div className="vault-toolbar">
        <div className="vault-filter">
          <select
            value={selectedUserId ?? ""}
            onChange={(e) =>
              setSelectedUserId(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">All users</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nickname || u.name || u.email}
              </option>
            ))}
          </select>
        </div>
      </div>

      <VaultDocumentsSection
        documents={documents}
        selectedUserId={selectedUserId}
        myUserId={myUserId}
        users={users}
        copied={copied}
        expandedFiles={expandedFiles}
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

      <VaultProgramsSection
        programs={programs}
        programOptions={programOptions}
        selectedUserId={selectedUserId}
        myUserId={myUserId}
        users={users}
        copied={copied}
        expandedAlliances={expandedAlliances}
        airlineSearch={airlineSearch}
        onAirlineSearchChange={setAirlineSearch}
        onExpandedAlliancesChange={setExpandedAlliances}
        onEditProg={(prog) => {
          setEditingProg(prog);
          setProgModalOpen(true);
        }}
        onAddProg={() => {
          setEditingProg(null);
          setProgModalOpen(true);
        }}
        onDeleteProg={handleDeleteProg}
        onToggleFavorite={handleToggleFavorite}
        onCopy={handleCopy}
        getUserName={getUserName}
        getUser={getUser}
      />

      <VaultVaccinationsSection
        vaccinations={vaccinations}
        selectedUserId={selectedUserId}
        copied={copied}
        expandedFiles={expandedFiles}
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

      <VaultTravelDocsSection
        travelDocs={travelDocs}
        selectedUserId={selectedUserId}
        showExpiredTravelDocs={showExpiredTravelDocs}
        expandedFiles={expandedFiles}
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

      {progModalOpen && (
        <ProgramFormModal
          isOpen={progModalOpen}
          onClose={() => {
            setProgModalOpen(false);
            setEditingProg(null);
          }}
          onSave={handleSaveProg}
          initialData={editingProg}
          users={users}
          programOptions={programOptions}
          existingPrograms={programs}
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
