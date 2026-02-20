import {
  BiCheck,
  BiCopy,
  BiFile,
  BiLink,
  BiNote,
  BiPaperclip,
  BiPencil,
  BiPlus,
  BiRefresh,
  BiShield,
  BiTrash,
} from "react-icons/bi";
import Flag from "../Flag";
import type { VaultDocument, VaultUser } from "./types";
import { DOC_TYPE_LABELS, expiryClass, fmtDate, fmtFileSize } from "./types";

interface Props {
  documents: VaultDocument[];
  copied: string | null;
  expandedFiles: Set<string>;
  hideHeader?: boolean;
  onEditDoc: (doc: VaultDocument) => void;
  onAddDoc: () => void;
  onDeleteDoc: (id: number) => void;
  onRestoreDoc: (id: number) => void;
  onCopy: (text: string, id: string) => void;
  onToggleFiles: (key: string) => void;
  onFileUpload: (entityType: string, entityId: number, file: File) => void;
  onViewFile: (fileId: number) => void;
  onDeleteFile: (fileId: number) => void;
  getUserName: (userId: number) => string;
  getUser: (userId: number) => VaultUser | undefined;
}

export default function VaultDocumentsSection({
  documents,
  copied,
  expandedFiles,
  hideHeader,
  onEditDoc,
  onAddDoc,
  onDeleteDoc,
  onRestoreDoc,
  onCopy,
  onToggleFiles,
  onFileUpload,
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
            <BiShield /> Documents
          </h3>
          <button className="btn-icon" onClick={onAddDoc} title="Add document">
            <BiPlus />
          </button>
        </div>
      )}
      <div className="vault-cards">
        {documents.map((doc) => {
          const ec = doc.is_archived
            ? ""
            : expiryClass(doc.expiry_date, doc.doc_type);
          return (
            <div
              key={doc.id}
              className={`vault-card${ec ? ` vault-card-${ec}` : ""}${doc.is_archived ? " vault-card-archived" : ""}`}
            >
              {ec === "expiry-warning" && (
                <div className="vault-ribbon vault-ribbon-warning">
                  Expiring soon
                </div>
              )}
              {ec === "expiry-expired" && (
                <div className="vault-ribbon vault-ribbon-expired">Expired</div>
              )}
              <div className="vault-card-header">
                <div className="vault-card-label">
                  {doc.issuing_country && (
                    <Flag code={doc.issuing_country} size={16} />
                  )}
                  {doc.label}
                </div>
                <div className="vault-card-actions">
                  {!doc.is_archived && (
                    <button
                      className="btn-icon"
                      onClick={() => onEditDoc(doc)}
                      title="Edit"
                    >
                      <BiPencil />
                    </button>
                  )}
                  {doc.is_archived ? (
                    <button
                      className="btn-icon"
                      onClick={() => onRestoreDoc(doc.id)}
                      title="Restore"
                    >
                      <BiRefresh />
                    </button>
                  ) : (
                    <button
                      className="btn-icon"
                      onClick={() => onDeleteDoc(doc.id)}
                      title="Archive"
                    >
                      <BiTrash />
                    </button>
                  )}
                </div>
              </div>
              <span className="vault-card-type">
                {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}
              </span>
              {doc.proper_name && (
                <div className="vault-card-proper-name">{doc.proper_name}</div>
              )}
              <div
                className="vault-card-avatar"
                title={getUserName(doc.user_id)}
              >
                {getUser(doc.user_id)?.picture ? (
                  <img
                    src={getUser(doc.user_id)!.picture!}
                    alt={getUserName(doc.user_id)}
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <span>{getUserName(doc.user_id).charAt(0)}</span>
                )}
              </div>
              {doc.number_masked && (
                <div className="vault-masked-row">
                  <span className="vault-masked">{doc.number_masked}</span>
                  {doc.number_decrypted && (
                    <button
                      className="vault-copy-btn"
                      onClick={() =>
                        onCopy(doc.number_decrypted!, `doc-${doc.id}`)
                      }
                      title="Copy number"
                    >
                      {copied === `doc-${doc.id}` ? <BiCheck /> : <BiCopy />}
                    </button>
                  )}
                </div>
              )}
              {doc.expiry_date && (
                <div className="vault-card-dates">
                  <span className={expiryClass(doc.expiry_date, doc.doc_type)}>
                    Expires: {fmtDate(doc.expiry_date)}
                  </span>
                </div>
              )}
              {doc.notes_masked && (
                <div className="vault-notes" title="Has notes">
                  <BiNote />
                </div>
              )}
              <div className="vault-card-file-info">
                {doc.files && doc.files.length > 0 ? (
                  <button
                    className="vault-file-badge"
                    onClick={() => onToggleFiles(`doc-${doc.id}`)}
                  >
                    <BiPaperclip /> {doc.files.length} file
                    {doc.files.length > 1 ? "s" : ""}
                  </button>
                ) : !doc.is_archived ? (
                  <label className="vault-file-badge vault-file-badge-add">
                    <BiPaperclip /> Attach
                    <input
                      type="file"
                      accept=".pdf,image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFileUpload("document", doc.id, f);
                      }}
                    />
                  </label>
                ) : null}
              </div>
              {expandedFiles.has(`doc-${doc.id}`) && doc.files && (
                <div className="vault-card-files">
                  {doc.files.map((f) => (
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
                  {!doc.is_archived && (
                    <label className="vault-file-row vault-file-add">
                      <BiPlus /> Add file
                      <input
                        type="file"
                        accept=".pdf,image/jpeg,image/png,image/webp"
                        style={{ display: "none" }}
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) onFileUpload("document", doc.id, f);
                        }}
                      />
                    </label>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {documents.length === 0 && (
          <p className="vault-empty">No documents yet.</p>
        )}
      </div>
    </div>
  );
}
