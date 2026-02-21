import { useCallback, useEffect, useRef, useState } from "react";
import { BiLink } from "react-icons/bi";
import {
  FaFacebook,
  FaGlobe,
  FaInstagram,
  FaTripadvisor,
} from "react-icons/fa";
import type { Fixer, FixerLink } from "./types";
import {
  FIXER_LINK_TYPES,
  FIXER_RATING_LABELS,
  FIXER_TYPE_LABELS,
} from "./types";

function countryFlag(code: string): string {
  return String.fromCodePoint(
    ...code
      .toUpperCase()
      .split("")
      .map((c) => 0x1f1e6 - 65 + c.charCodeAt(0)),
  );
}

interface CountryOption {
  code: string;
  name: string;
}

const LINK_TYPE_ICONS: Record<string, React.ReactNode> = {
  website: <FaGlobe />,
  instagram: <FaInstagram />,
  facebook: <FaFacebook />,
  tripadvisor: <FaTripadvisor />,
  tourhq: "THQ",
  getyourguide: "GYG",
  nomadmania: "NM",
  other: <BiLink />,
};

export interface FixerFormData {
  name: string;
  type: string;
  phone: string;
  whatsapp: string;
  email: string;
  notes: string;
  rating: number | null;
  links: FixerLink[];
  country_codes: string[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: FixerFormData) => Promise<void>;
  initialData: Fixer | null;
}

export default function FixerFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
}: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState("guide");
  const [phone, setPhone] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [rating, setRating] = useState<number | null>(null);
  const [links, setLinks] = useState<FixerLink[]>([]);
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [countrySearch, setCountrySearch] = useState("");
  const [countryOptions, setCountryOptions] = useState<CountryOption[]>([]);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const countryDropdownRef = useRef<HTMLDivElement>(null);
  const linkUrlRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Fetch country options once on mount
  useEffect(() => {
    fetch("/api/v1/admin/fixers/countries", { credentials: "include" })
      .then((r) => r.json())
      .then((data) => setCountryOptions(data.countries || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (isOpen) {
      setName(initialData?.name ?? "");
      setType(initialData?.type ?? "guide");
      setPhone(initialData?.phone ?? "");
      setWhatsapp(initialData?.whatsapp ?? "");
      setEmail(initialData?.email ?? "");
      setNotes(initialData?.notes ?? "");
      setRating(initialData?.rating ?? null);
      setLinks(initialData?.links?.length ? [...initialData.links] : []);
      setCountryCodes(initialData?.country_codes ?? []);
      setCountrySearch("");
      setShowCountryDropdown(false);
      setError(null);
    }
  }, [isOpen, initialData]);

  // Close country dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        countryDropdownRef.current &&
        !countryDropdownRef.current.contains(e.target as Node)
      ) {
        setShowCountryDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filteredCountries = useCallback(() => {
    const q = countrySearch.toLowerCase().trim();
    if (!q) return [];
    return countryOptions.filter(
      (c) =>
        !countryCodes.includes(c.code) &&
        (c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q)),
    );
  }, [countrySearch, countryOptions, countryCodes]);

  const addCountry = (code: string) => {
    if (!countryCodes.includes(code)) {
      setCountryCodes([...countryCodes, code]);
    }
    setCountrySearch("");
    setShowCountryDropdown(false);
  };

  const removeCountry = (code: string) => {
    setCountryCodes(countryCodes.filter((c) => c !== code));
  };

  const addLink = (linkType: string) => {
    const newLinks = [...links, { type: linkType, url: "" }];
    setLinks(newLinks);
    // Auto-focus the new URL input after render
    requestAnimationFrame(() => {
      linkUrlRefs.current[newLinks.length - 1]?.focus();
    });
  };

  const updateLinkUrl = (index: number, url: string) => {
    const updated = [...links];
    updated[index] = { ...updated[index], url };
    setLinks(updated);
  };

  const removeLink = (index: number) => {
    setLinks(links.filter((_, i) => i !== index));
  };

  // Which single-use link types are already added?
  const usedLinkTypes = new Set(
    links.filter((l) => l.type !== "other").map((l) => l.type),
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setSaving(true);
    try {
      await onSave({
        name,
        type,
        phone,
        whatsapp,
        email,
        notes,
        rating,
        links: links.filter((l) => l.url.trim()),
        country_codes: countryCodes,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const dropdownItems = filteredCountries();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{initialData ? "Edit Fixer" : "Add Fixer"}</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}

          {/* Name + Type */}
          <div className="form-row">
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Contact name"
              />
            </div>
            <div className="form-group">
              <label>Type *</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                {Object.entries(FIXER_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* WhatsApp + Phone */}
          <div className="form-row">
            <div className="form-group">
              <label>WhatsApp</label>
              <input
                type="text"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                placeholder="+1234567890"
              />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1234567890"
              />
            </div>
          </div>

          {/* Email */}
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@example.com"
            />
          </div>

          {/* Countries — searchable multi-select */}
          <div className="form-group">
            <label>Countries</label>
            <div className="fixer-country-search" ref={countryDropdownRef}>
              <input
                type="text"
                value={countrySearch}
                onChange={(e) => {
                  setCountrySearch(e.target.value);
                  setShowCountryDropdown(e.target.value.trim().length > 0);
                }}
                onFocus={() => {
                  if (countrySearch.trim()) setShowCountryDropdown(true);
                }}
                placeholder="Search country..."
              />
              {showCountryDropdown && dropdownItems.length > 0 && (
                <div className="fixer-country-dropdown">
                  {dropdownItems.map((c) => (
                    <div
                      key={c.code}
                      className="fixer-country-dropdown-item"
                      onClick={() => addCountry(c.code)}
                    >
                      {countryFlag(c.code)} {c.name} ({c.code})
                    </div>
                  ))}
                </div>
              )}
            </div>
            {countryCodes.length > 0 && (
              <div className="fixer-country-tags">
                {countryCodes.map((cc) => {
                  const opt = countryOptions.find((c) => c.code === cc);
                  return (
                    <span key={cc} className="fixer-country-tag">
                      {countryFlag(cc)} {cc}
                      {opt && (
                        <span className="fixer-country-tag-name">
                          {opt.name}
                        </span>
                      )}
                      <button type="button" onClick={() => removeCountry(cc)}>
                        &times;
                      </button>
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          {/* Rating */}
          <div className="form-group">
            <label>Rating</label>
            <div className="fixer-rating-selector">
              {([1, 2, 3, 4] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  className={`fixer-rating-btn${rating === val ? " active" : ""}`}
                  onClick={() => setRating(rating === val ? null : val)}
                  title={FIXER_RATING_LABELS[val].label}
                >
                  {FIXER_RATING_LABELS[val].emoji}
                </button>
              ))}
            </div>
          </div>

          {/* Links — icon buttons */}
          <div className="form-group">
            <label>Links</label>
            <div className="fixer-link-type-buttons">
              {Object.entries(FIXER_LINK_TYPES).map(([key, label]) => {
                const disabled = key !== "other" && usedLinkTypes.has(key);
                return (
                  <button
                    key={key}
                    type="button"
                    className="fixer-link-type-btn"
                    disabled={disabled}
                    onClick={() => addLink(key)}
                    title={label}
                  >
                    {LINK_TYPE_ICONS[key]}
                  </button>
                );
              })}
            </div>
            {links.map((lnk, i) => (
              <div key={i} className="fixer-link-row">
                <span
                  className="fixer-link-row-icon"
                  title={FIXER_LINK_TYPES[lnk.type] || lnk.type}
                >
                  {LINK_TYPE_ICONS[lnk.type] || <BiLink />}
                </span>
                <input
                  ref={(el) => {
                    linkUrlRefs.current[i] = el;
                  }}
                  type="url"
                  value={lnk.url}
                  onChange={(e) => updateLinkUrl(i, e.target.value)}
                  placeholder="https://..."
                />
                <button
                  type="button"
                  className="btn-icon"
                  onClick={() => removeLink(i)}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>

          {/* Notes */}
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
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
