import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BiLock } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import { useVaultAuth } from "../../hooks/useVaultAuth";
import type { VaultAddress, VaultUser } from "./types";
import VaultAddressesSection from "./VaultAddressesSection";
import AddressFormModal from "./VaultAddressForm";

export default function AddressesTab({
  addTrigger,
  search,
}: {
  addTrigger?: number;
  search?: string;
}) {
  const { unlocked, loading, vaultFetch } = useVaultAuth();
  const [addresses, setAddresses] = useState<VaultAddress[]>([]);
  const [users, setUsers] = useState<VaultUser[]>([]);
  const [addressModalOpen, setAddressModalOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<VaultAddress | null>(
    null,
  );

  const fetchData = useCallback(async () => {
    const res = await vaultFetch("/api/v1/admin/vault/addresses");
    if (res?.ok) {
      const data = await res.json();
      setAddresses(data.addresses);
    }
  }, [vaultFetch]);

  const fetchUsers = useCallback(() => {
    apiFetch("/api/v1/admin/users/")
      .then((r) => r.json())
      .then((data) => {
        setUsers(
          (data.users || []).map((u: VaultUser) => ({
            id: u.id,
            email: u.email,
            name: u.name,
            nickname: u.nickname,
            picture: u.picture,
          })),
        );
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    if (unlocked) fetchData();
  }, [unlocked, fetchData]);

  // Open add modal when parent triggers (ignore stale value on mount)
  const lastTriggerRef = useRef(addTrigger ?? 0);
  useEffect(() => {
    if (addTrigger != null && addTrigger > lastTriggerRef.current && unlocked) {
      setEditingAddress(null);
      setAddressModalOpen(true);
    }
    lastTriggerRef.current = addTrigger ?? 0;
  }, [addTrigger, unlocked]);

  const filteredAddresses = useMemo(() => {
    const q = (search ?? "").toLowerCase().trim();
    if (!q) return addresses;
    return addresses.filter(
      (a) =>
        a.name.toLowerCase().includes(q) || a.address.toLowerCase().includes(q),
    );
  }, [addresses, search]);

  const handleSaveAddress = async (formData: {
    name: string;
    address: string;
    country_code: string;
    user_id: number | null;
    notes: string;
  }) => {
    const body = {
      name: formData.name,
      address: formData.address,
      country_code: formData.country_code || null,
      user_id: formData.user_id,
      notes: formData.notes || null,
    };
    const url = editingAddress
      ? `/api/v1/admin/vault/addresses/${editingAddress.id}`
      : "/api/v1/admin/vault/addresses";
    const method = editingAddress ? "PUT" : "POST";
    const res = await vaultFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res?.ok) {
      const data = await res?.json().catch(() => null);
      throw new Error(data?.detail || "Failed to save address");
    }
    setAddressModalOpen(false);
    setEditingAddress(null);
    fetchData();
  };

  const handleDeleteAddress = async (id: number) => {
    if (!confirm("Delete this address?")) return;
    const res = await vaultFetch(`/api/v1/admin/vault/addresses/${id}`, {
      method: "DELETE",
    });
    if (res?.ok) fetchData();
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
      <VaultAddressesSection
        addresses={filteredAddresses}
        hideHeader
        onEditAddress={(addr) => {
          setEditingAddress(addr);
          setAddressModalOpen(true);
        }}
        onAddAddress={() => {
          setEditingAddress(null);
          setAddressModalOpen(true);
        }}
        onDeleteAddress={handleDeleteAddress}
      />

      {addressModalOpen && (
        <AddressFormModal
          isOpen={addressModalOpen}
          onClose={() => {
            setAddressModalOpen(false);
            setEditingAddress(null);
          }}
          onSave={handleSaveAddress}
          initialData={editingAddress}
          users={users}
          vaultFetch={vaultFetch}
        />
      )}
    </div>
  );
}
