import { BiEnvelope, BiNote, BiPencil, BiPlus, BiTrash } from "react-icons/bi";
import type { VaultAddress } from "./types";

interface Props {
  addresses: VaultAddress[];
  hideHeader?: boolean;
  onEditAddress: (addr: VaultAddress) => void;
  onAddAddress: () => void;
  onDeleteAddress: (id: number) => void;
}

function countryFlag(code: string): string {
  return String.fromCodePoint(
    ...code
      .toUpperCase()
      .split("")
      .map((c) => 0x1f1e6 - 65 + c.charCodeAt(0)),
  );
}

export default function VaultAddressesSection({
  addresses,
  hideHeader,
  onEditAddress,
  onAddAddress,
  onDeleteAddress,
}: Props) {
  return (
    <div className="vault-section">
      {!hideHeader && (
        <div className="vault-section-header">
          <h3>
            <BiEnvelope /> Postcard Addresses
          </h3>
          <button
            className="btn-icon"
            onClick={onAddAddress}
            title="Add address"
          >
            <BiPlus />
          </button>
        </div>
      )}
      <div className="vault-cards">
        {addresses.map((addr) => (
          <div key={addr.id} className="vault-card">
            <div className="vault-card-header">
              <div className="vault-card-label">
                {addr.country_code && (
                  <span title={addr.country_code}>
                    {countryFlag(addr.country_code)}{" "}
                  </span>
                )}
                {addr.name}
                {addr.user_picture && (
                  <img
                    src={addr.user_picture}
                    alt={addr.user_name || ""}
                    className="addr-card-avatar"
                    title={addr.user_name || "Linked user"}
                  />
                )}
                {!addr.user_picture && addr.user_name && (
                  <span className="addr-card-user-badge" title={addr.user_name}>
                    {addr.user_name}
                  </span>
                )}
              </div>
              <div className="vault-card-actions">
                <button
                  className="btn-icon"
                  onClick={() => onEditAddress(addr)}
                  title="Edit"
                >
                  <BiPencil />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => onDeleteAddress(addr.id)}
                  title="Delete"
                >
                  <BiTrash />
                </button>
              </div>
            </div>
            <div className="vault-card-address">
              {addr.address.split("\n").map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
            {addr.notes_masked && (
              <div className="vault-notes" title="Has notes">
                <BiNote />
              </div>
            )}
          </div>
        ))}
        {addresses.length === 0 && (
          <p className="vault-empty">No addresses yet.</p>
        )}
      </div>
    </div>
  );
}
