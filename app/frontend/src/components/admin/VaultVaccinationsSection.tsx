import {
  BiCheck,
  BiCopy,
  BiFile,
  BiLink,
  BiNote,
  BiPaperclip,
  BiPencil,
  BiPlus,
  BiTargetLock,
  BiTrash,
} from "react-icons/bi";
import type { VaultVaccination, VaultUser } from "./types";
import { expiryClass, fmtDate, fmtFileSize } from "./types";

interface Props {
  vaccinations: VaultVaccination[];
  selectedUserId: number | null;
  copied: string | null;
  expandedFiles: Set<string>;
  onEditVax: (vax: VaultVaccination) => void;
  onAddVax: () => void;
  onDeleteVax: (id: number) => void;
  onCopy: (text: string, id: string) => void;
  onToggleFiles: (key: string) => void;
  onFileUpload: (entityType: string, entityId: number, file: File) => void;
  onViewFile: (fileId: number) => void;
  onDeleteFile: (fileId: number) => void;
  getUserName: (userId: number) => string;
  getUser: (userId: number) => VaultUser | undefined;
}

export default function VaultVaccinationsSection({
  vaccinations,
  selectedUserId,
  copied,
  expandedFiles,
  onEditVax,
  onAddVax,
  onDeleteVax,
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
      <div className="vault-section-header">
        <h3>
          <BiTargetLock /> Vaccinations
        </h3>
        <button className="btn-icon" onClick={onAddVax} title="Add vaccination">
          <BiPlus />
        </button>
      </div>
      <div className="vault-cards">
        {vaccinations.map((vax) => {
          const ec = vax.expiry_date
            ? expiryClass(vax.expiry_date, "vaccination")
            : "";
          return (
            <div
              key={vax.id}
              className={`vault-card${ec ? ` vault-card-${ec}` : ""}`}
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
                <div className="vault-card-label">{vax.vaccine_name}</div>
                <div className="vault-card-actions">
                  <button
                    className="btn-icon"
                    onClick={() => onEditVax(vax)}
                    title="Edit"
                  >
                    <BiPencil />
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => onDeleteVax(vax.id)}
                    title="Delete"
                  >
                    <BiTrash />
                  </button>
                </div>
              </div>
              {(vax.brand_name || vax.dose_type) && (
                <div className="vault-card-vax-details">
                  {vax.brand_name && (
                    <span className="vault-card-type">{vax.brand_name}</span>
                  )}
                  {vax.dose_type && (
                    <span className="vault-card-type">{vax.dose_type}</span>
                  )}
                </div>
              )}
              {!selectedUserId && (
                <div
                  className="vault-card-avatar"
                  title={getUserName(vax.user_id)}
                >
                  {getUser(vax.user_id)?.picture ? (
                    <img
                      src={getUser(vax.user_id)!.picture!}
                      alt={getUserName(vax.user_id)}
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <span>{getUserName(vax.user_id).charAt(0)}</span>
                  )}
                </div>
              )}
              {vax.batch_number_masked && (
                <div className="vault-masked-row">
                  <span className="vault-masked">
                    {vax.batch_number_masked}
                  </span>
                  {vax.batch_number_decrypted && (
                    <button
                      className="vault-copy-btn"
                      onClick={() =>
                        onCopy(vax.batch_number_decrypted!, `vax-${vax.id}`)
                      }
                      title="Copy batch number"
                    >
                      {copied === `vax-${vax.id}` ? <BiCheck /> : <BiCopy />}
                    </button>
                  )}
                </div>
              )}
              <div className="vault-card-dates">
                {vax.date_administered && (
                  <span>Given: {fmtDate(vax.date_administered)}</span>
                )}
                {vax.expiry_date ? (
                  <span className={ec}>
                    Expires: {fmtDate(vax.expiry_date)}
                  </span>
                ) : (
                  <span className="vault-lifetime">Lifetime</span>
                )}
              </div>
              {vax.notes_masked && (
                <div className="vault-notes" title="Has notes">
                  <BiNote />
                </div>
              )}
              <div className="vault-card-file-info">
                {vax.files && vax.files.length > 0 ? (
                  <button
                    className="vault-file-badge"
                    onClick={() => onToggleFiles(`vax-files-${vax.id}`)}
                  >
                    <BiPaperclip /> {vax.files.length} file
                    {vax.files.length > 1 ? "s" : ""}
                  </button>
                ) : (
                  <label className="vault-file-badge vault-file-badge-add">
                    <BiPaperclip /> Attach
                    <input
                      type="file"
                      accept=".pdf,image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFileUpload("vaccination", vax.id, f);
                      }}
                    />
                  </label>
                )}
              </div>
              {expandedFiles.has(`vax-files-${vax.id}`) && vax.files && (
                <div className="vault-card-files">
                  {vax.files.map((f) => (
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
                  <label className="vault-file-row vault-file-add">
                    <BiPlus /> Add file
                    <input
                      type="file"
                      accept=".pdf,image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFileUpload("vaccination", vax.id, f);
                      }}
                    />
                  </label>
                </div>
              )}
            </div>
          );
        })}
        {vaccinations.length === 0 && (
          <p className="vault-empty">No vaccination records yet.</p>
        )}
      </div>
    </div>
  );
}
