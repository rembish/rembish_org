import {
  BiCheck,
  BiFile,
  BiLink,
  BiNote,
  BiPaperclip,
  BiPencil,
  BiPlus,
  BiTrash,
  BiWorld,
} from "react-icons/bi";
import Flag from "../Flag";
import type { VaultTravelDoc, VaultUser } from "./types";
import {
  TRAVEL_DOC_TYPE_LABELS,
  ENTRY_TYPE_LABELS,
  expiryClass,
  fmtDate,
  fmtFileSize,
} from "./types";

interface Props {
  travelDocs: VaultTravelDoc[];
  showExpiredTravelDocs: boolean;
  expandedFiles: Set<string>;
  hideHeader?: boolean;
  onShowExpiredChange: (value: boolean) => void;
  onEditTravelDoc: (doc: VaultTravelDoc) => void;
  onAddTravelDoc: () => void;
  onDeleteTravelDoc: (id: number) => void;
  onMarkUsed: (id: number) => void;
  onToggleFiles: (key: string) => void;
  onViewFile: (fileId: number) => void;
  onDeleteFile: (fileId: number) => void;
  getUserName: (userId: number) => string;
  getUser: (userId: number) => VaultUser | undefined;
}

export default function VaultTravelDocsSection({
  travelDocs,
  showExpiredTravelDocs,
  expandedFiles,
  hideHeader,
  onShowExpiredChange,
  onEditTravelDoc,
  onAddTravelDoc,
  onDeleteTravelDoc,
  onMarkUsed,
  onToggleFiles,
  onViewFile,
  onDeleteFile,
  getUserName,
  getUser,
}: Props) {
  return (
    <div className="vault-section">
      {!hideHeader && (
        <div className="vault-section-header">
          <h3>
            <BiWorld /> Travel Documents
          </h3>
          <div className="vault-section-actions">
            <label className="vault-toggle-label">
              <input
                type="checkbox"
                checked={showExpiredTravelDocs}
                onChange={(e) => onShowExpiredChange(e.target.checked)}
              />
              Show expired
            </label>
            <button
              className="btn-icon"
              onClick={onAddTravelDoc}
              title="Add travel document"
            >
              <BiPlus />
            </button>
          </div>
        </div>
      )}
      <div className="vault-cards">
        {travelDocs
          .filter((td) => {
            if (showExpiredTravelDocs) return true;
            if (!td.valid_until) return true;
            // Match expiryClass logic: expired if expiry date < now
            return new Date(td.valid_until + "T00:00:00") >= new Date();
          })
          .sort((a, b) => {
            // No expiry date -> end of list
            if (!a.valid_until && !b.valid_until) return 0;
            if (!a.valid_until) return 1;
            if (!b.valid_until) return -1;
            return a.valid_until.localeCompare(b.valid_until);
          })
          .map((td) => {
            const ec = td.valid_until
              ? expiryClass(td.valid_until, "id_card")
              : "";
            return (
              <div
                key={td.id}
                className={`vault-card${ec ? ` vault-card-${ec}` : ""}`}
              >
                {ec === "expiry-warning" && (
                  <div className="vault-ribbon vault-ribbon-warning">
                    Expiring soon
                  </div>
                )}
                {ec === "expiry-expired" && (
                  <div className="vault-ribbon vault-ribbon-expired">
                    Expired
                  </div>
                )}
                <div className="vault-card-header">
                  <div className="vault-card-label">
                    {td.country_code && (
                      <Flag code={td.country_code} size={16} />
                    )}
                    {td.label}
                  </div>
                  <div className="vault-card-actions">
                    {(!td.valid_until ||
                      td.valid_until >=
                        new Date().toISOString().slice(0, 10)) && (
                      <button
                        className="btn-icon"
                        onClick={() => onMarkUsed(td.id)}
                        title="Mark as used"
                      >
                        <BiCheck />
                      </button>
                    )}
                    <button
                      className="btn-icon"
                      onClick={() => onEditTravelDoc(td)}
                      title="Edit"
                    >
                      <BiPencil />
                    </button>
                    <button
                      className="btn-icon"
                      onClick={() => onDeleteTravelDoc(td.id)}
                      title="Delete"
                    >
                      <BiTrash />
                    </button>
                  </div>
                </div>
                <div className="vault-card-vax-details">
                  <span className="vault-card-type">
                    {TRAVEL_DOC_TYPE_LABELS[td.doc_type] || td.doc_type}
                  </span>
                  {td.entry_type && (
                    <span className="vault-card-entry-type">
                      {ENTRY_TYPE_LABELS[td.entry_type] || td.entry_type}
                    </span>
                  )}
                  {td.notes_masked && (
                    <span className="vault-card-entry-type" title="Has notes">
                      <BiNote />
                    </span>
                  )}
                </div>
                {td.passport_label && (
                  <div className="vault-card-passport">{td.passport_label}</div>
                )}
                <div
                  className="vault-card-avatar"
                  title={getUserName(td.user_id)}
                >
                  {getUser(td.user_id)?.picture ? (
                    <img
                      src={getUser(td.user_id)!.picture!}
                      alt={getUserName(td.user_id)}
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <span>{getUserName(td.user_id).charAt(0)}</span>
                  )}
                </div>
                <div className="vault-card-dates">
                  {td.valid_from && <span>From: {fmtDate(td.valid_from)}</span>}
                  {td.valid_until && (
                    <span className={ec}>Until: {fmtDate(td.valid_until)}</span>
                  )}
                </div>
                {td.files.length > 0 && (
                  <div className="vault-card-file-info">
                    <button
                      className="vault-file-badge"
                      onClick={() => onToggleFiles(`td-${td.id}`)}
                    >
                      <BiPaperclip /> {td.files.length} file
                      {td.files.length > 1 ? "s" : ""}
                    </button>
                  </div>
                )}
                {expandedFiles.has(`td-${td.id}`) && (
                  <div className="vault-card-files">
                    {td.files.map((f) => (
                      <div key={f.id} className="vault-file-row">
                        <span>
                          <BiFile /> {f.label || f.mime_type.split("/")[1]} (
                          {fmtFileSize(f.file_size)})
                        </span>
                        <div>
                          <button
                            className="btn-icon"
                            onClick={() => onViewFile(f.id)}
                            title="View"
                          >
                            <BiLink />
                          </button>
                          <button
                            className="btn-icon"
                            onClick={() => onDeleteFile(f.id)}
                            title="Delete"
                          >
                            <BiTrash />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {td.trip_ids.length > 0 && (
                  <div className="vault-notes">
                    Assigned to {td.trip_ids.length} trip
                    {td.trip_ids.length > 1 ? "s" : ""}
                  </div>
                )}
              </div>
            );
          })}
        {travelDocs.length === 0 && (
          <p className="vault-empty">No travel documents yet.</p>
        )}
        {travelDocs.length > 0 &&
          !showExpiredTravelDocs &&
          travelDocs.every(
            (td) =>
              td.valid_until &&
              new Date(td.valid_until + "T00:00:00") < new Date(),
          ) && <p className="vault-empty">All travel documents are expired.</p>}
      </div>
    </div>
  );
}
