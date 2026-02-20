import { useCallback, useEffect, useState } from "react";
import { BiLock } from "react-icons/bi";
import { useVaultAuth } from "../../hooks/useVaultAuth";
import { apiFetch } from "../../lib/api";
import type { VaultLoyaltyProgram, VaultUser, ProgramOption } from "./types";
import VaultProgramsSection from "./VaultProgramsSection";
import ProgramFormModal from "./VaultProgramForm";

export default function LoyaltyTab() {
  const { unlocked, loading, vaultFetch } = useVaultAuth();
  const [programs, setPrograms] = useState<VaultLoyaltyProgram[]>([]);
  const [programOptions, setProgramOptions] = useState<ProgramOption[]>([]);
  const [users, setUsers] = useState<VaultUser[]>([]);
  const [myUserId, setMyUserId] = useState<number | null>(null);
  const [progModalOpen, setProgModalOpen] = useState(false);
  const [editingProg, setEditingProg] = useState<VaultLoyaltyProgram | null>(
    null,
  );
  const [copied, setCopied] = useState<string | null>(null);
  const [expandedAlliances, setExpandedAlliances] = useState<Set<string>>(
    new Set(),
  );
  const [airlineSearch, setAirlineSearch] = useState("");

  const fetchData = useCallback(async () => {
    const [progsRes, optionsRes] = await Promise.all([
      vaultFetch("/api/v1/admin/vault/programs"),
      vaultFetch("/api/v1/admin/vault/program-options"),
    ]);
    if (progsRes?.ok) {
      const data = await progsRes.json();
      setPrograms(data.programs);
    }
    if (optionsRes?.ok) {
      const data = await optionsRes.json();
      setProgramOptions(data.programs);
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

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
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
      <VaultProgramsSection
        programs={programs}
        programOptions={programOptions}
        myUserId={myUserId}
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
    </div>
  );
}
