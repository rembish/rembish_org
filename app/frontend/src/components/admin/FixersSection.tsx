import { BiEnvelope, BiLink, BiPencil, BiPhone, BiTrash } from "react-icons/bi";
import {
  FaFacebook,
  FaGlobe,
  FaInstagram,
  FaTripadvisor,
  FaWhatsapp,
} from "react-icons/fa";
import type { Fixer } from "./types";
import {
  FIXER_LINK_TYPES,
  FIXER_RATING_LABELS,
  FIXER_TYPE_LABELS,
} from "./types";

const LINK_ICONS: Record<string, React.ReactNode> = {
  website: <FaGlobe />,
  instagram: <FaInstagram />,
  facebook: <FaFacebook />,
  tripadvisor: <FaTripadvisor />,
  tourhq: "THQ",
  getyourguide: "GYG",
  nomadmania: "NM",
  other: <BiLink />,
};

function countryFlag(code: string): string {
  return String.fromCodePoint(
    ...code
      .toUpperCase()
      .split("")
      .map((c) => 0x1f1e6 - 65 + c.charCodeAt(0)),
  );
}

function whatsappUrl(num: string): string {
  return `https://wa.me/${num.replace(/[^0-9]/g, "")}`;
}

interface Props {
  fixers: Fixer[];
  readOnly?: boolean;
  onEdit: (fixer: Fixer) => void;
  onDelete: (id: number) => void;
}

export default function FixersSection({
  fixers,
  readOnly,
  onEdit,
  onDelete,
}: Props) {
  return (
    <div className="vault-section">
      <div className="vault-cards">
        {fixers.map((f) => (
          <div key={f.id} className="vault-card fixer-card">
            <div className="vault-card-header">
              <div className="vault-card-label">
                {f.name}
                {f.rating != null && FIXER_RATING_LABELS[f.rating] && (
                  <span
                    className="fixer-rating"
                    title={FIXER_RATING_LABELS[f.rating].label}
                  >
                    {FIXER_RATING_LABELS[f.rating].emoji}
                  </span>
                )}
              </div>
              {!readOnly && (
                <div className="vault-card-actions">
                  <button
                    className="btn-icon"
                    onClick={() => onEdit(f)}
                    title="Edit"
                  >
                    <BiPencil />
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => onDelete(f.id)}
                    title="Delete"
                  >
                    <BiTrash />
                  </button>
                </div>
              )}
            </div>

            <div className="fixer-card-type-row">
              <span className="fixer-card-type">
                {FIXER_TYPE_LABELS[f.type] || f.type}
              </span>
              {f.country_codes.map((cc) => (
                <span key={cc} className="fixer-card-type" title={cc}>
                  {countryFlag(cc)}
                </span>
              ))}
            </div>

            <div className="fixer-contact-info">
              {f.phone && (
                <a href={`tel:${f.phone}`} className="fixer-contact-link">
                  <BiPhone /> {f.phone}
                </a>
              )}
              {f.whatsapp && (
                <a
                  href={whatsappUrl(f.whatsapp)}
                  className="fixer-contact-link"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <FaWhatsapp /> {f.whatsapp}
                </a>
              )}
              {f.email && (
                <a href={`mailto:${f.email}`} className="fixer-contact-link">
                  <BiEnvelope /> {f.email}
                </a>
              )}
            </div>

            {f.links.length > 0 && (
              <div className="fixer-links">
                {f.links.map((lnk, i) => (
                  <a
                    key={i}
                    href={lnk.url}
                    className="fixer-link-badge"
                    target="_blank"
                    rel="noopener noreferrer"
                    title={FIXER_LINK_TYPES[lnk.type] || lnk.type}
                  >
                    {LINK_ICONS[lnk.type] || <BiLink />}
                  </a>
                ))}
              </div>
            )}

            {f.notes && (
              <div className="fixer-notes-text" title={f.notes}>
                {f.notes}
              </div>
            )}
          </div>
        ))}
        {fixers.length === 0 && <p className="vault-empty">No fixers yet.</p>}
      </div>
    </div>
  );
}
