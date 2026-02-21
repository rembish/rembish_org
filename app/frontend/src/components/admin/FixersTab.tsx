import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Fixer } from "./types";
import FixersSection from "./FixersSection";
import FixerFormModal, { type FixerFormData } from "./FixerFormModal";

interface Props {
  addTrigger?: number;
  search?: string;
  readOnly?: boolean;
}

export default function FixersTab({ addTrigger, search, readOnly }: Props) {
  const [fixers, setFixers] = useState<Fixer[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Fixer | null>(null);

  const fetchFixers = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/admin/fixers/");
      if (res.ok) {
        const data = await res.json();
        setFixers(data.fixers || []);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFixers();
  }, [fetchFixers]);

  // Open add modal when parent triggers
  const lastTriggerRef = useRef(addTrigger ?? 0);
  useEffect(() => {
    if (addTrigger != null && addTrigger > lastTriggerRef.current) {
      setEditing(null);
      setModalOpen(true);
    }
    lastTriggerRef.current = addTrigger ?? 0;
  }, [addTrigger]);

  const filteredFixers = useMemo(() => {
    const q = (search ?? "").toLowerCase().trim();
    if (!q) return fixers;
    return fixers.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.country_codes.some((cc) => cc.toLowerCase().includes(q)),
    );
  }, [fixers, search]);

  const handleSave = async (data: FixerFormData) => {
    const body = {
      name: data.name,
      type: data.type,
      phone: data.phone || null,
      whatsapp: data.whatsapp || null,
      email: data.email || null,
      notes: data.notes || null,
      rating: data.rating,
      links: data.links,
      country_codes: data.country_codes,
    };
    const url = editing
      ? `/api/v1/admin/fixers/${editing.id}`
      : "/api/v1/admin/fixers/";
    const method = editing ? "PUT" : "POST";
    const res = await apiFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      throw new Error(errData?.detail || "Failed to save fixer");
    }
    setModalOpen(false);
    setEditing(null);
    fetchFixers();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this fixer?")) return;
    const res = await apiFetch(`/api/v1/admin/fixers/${id}`, {
      method: "DELETE",
    });
    if (res.ok) fetchFixers();
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="vault-content">
      <FixersSection
        fixers={filteredFixers}
        readOnly={readOnly}
        onEdit={(f) => {
          setEditing(f);
          setModalOpen(true);
        }}
        onDelete={handleDelete}
      />

      {modalOpen && (
        <FixerFormModal
          isOpen={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setEditing(null);
          }}
          onSave={handleSave}
          initialData={editing}
        />
      )}
    </div>
  );
}
