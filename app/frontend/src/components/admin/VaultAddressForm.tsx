import { useCallback, useEffect, useRef, useState } from "react";
import type { VaultAddress, VaultUser } from "./types";

interface AddressSearchResult {
  display_name: string;
  country_code: string | null;
}

function countryFlag(code: string): string {
  return String.fromCodePoint(
    ...code
      .toUpperCase()
      .split("")
      .map((c) => 0x1f1e6 - 65 + c.charCodeAt(0)),
  );
}

export default function AddressFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  users,
  vaultFetch,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    name: string;
    address: string;
    country_code: string;
    user_id: number | null;
    notes: string;
  }) => Promise<void>;
  initialData: VaultAddress | null;
  users: VaultUser[];
  vaultFetch: (url: string, init?: RequestInit) => Promise<Response | null>;
}) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [userId, setUserId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Address search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<AddressSearchResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setName(initialData?.name ?? "");
      setAddress(initialData?.address ?? "");
      setCountryCode(initialData?.country_code ?? "");
      setUserId(initialData?.user_id ?? null);
      setNotes(initialData?.notes_decrypted ?? "");
      setSearchQuery("");
      setSearchResults([]);
      setShowResults(false);
      setError(null);
    }
  }, [isOpen, initialData]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setShowResults(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const doSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) {
        setSearchResults([]);
        setShowResults(false);
        return;
      }
      setSearching(true);
      try {
        const res = await vaultFetch(
          `/api/v1/admin/vault/address-search?q=${encodeURIComponent(q)}`,
        );
        if (res?.ok) {
          const data = await res.json();
          setSearchResults(data.results || []);
          setShowResults(true);
        }
      } finally {
        setSearching(false);
      }
    },
    [vaultFetch],
  );

  const handleSearchInput = (value: string) => {
    setSearchQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 400);
  };

  const handlePickResult = (result: AddressSearchResult) => {
    setAddress(result.display_name);
    if (result.country_code) {
      setCountryCode(result.country_code);
    }
    setShowResults(false);
    setSearchQuery("");
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    if (!address.trim()) {
      setError("Address is required");
      return;
    }
    setSaving(true);
    try {
      await onSave({
        name,
        address,
        country_code: countryCode,
        user_id: userId,
        notes,
      });
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
          <h2>{initialData ? "Edit Address" : "Add Address"}</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}
          <div className="form-group">
            <label>Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. John Doe"
            />
          </div>
          <div className="form-group" ref={dropdownRef}>
            <label>Search address</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchInput(e.target.value)}
              placeholder="Type to search Nominatim..."
            />
            {searching && (
              <div className="address-search-loading">Searching...</div>
            )}
            {showResults && searchResults.length > 0 && (
              <div className="address-search-dropdown">
                {searchResults.map((r, i) => (
                  <button
                    key={i}
                    type="button"
                    className="address-search-item"
                    onClick={() => handlePickResult(r)}
                  >
                    {r.country_code && (
                      <span className="address-search-flag">
                        {countryFlag(r.country_code)}
                      </span>
                    )}
                    <span className="address-search-name">
                      {r.display_name}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="form-group">
            <label>Address *</label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              rows={3}
              placeholder="Selected address (editable)"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Country Code</label>
              <input
                type="text"
                value={countryCode}
                onChange={(e) =>
                  setCountryCode(e.target.value.toUpperCase().slice(0, 2))
                }
                placeholder="e.g. DE"
                maxLength={2}
              />
            </div>
            <div className="form-group">
              <label>Linked User</label>
              <select
                value={userId ?? ""}
                onChange={(e) =>
                  setUserId(e.target.value ? Number(e.target.value) : null)
                }
              >
                <option value="">— None —</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nickname || u.name || u.email}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
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
