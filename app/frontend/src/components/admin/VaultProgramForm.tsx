import { useEffect, useState } from "react";
import type { VaultLoyaltyProgram, VaultUser, ProgramOption } from "./types";
import { ALLIANCE_LABELS } from "./types";

export default function ProgramFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  users,
  programOptions,
  existingPrograms,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    user_id: number;
    program_name: string;
    alliance: string;
    membership_number: string;
    notes: string;
  }) => Promise<void>;
  initialData: VaultLoyaltyProgram | null;
  users: VaultUser[];
  programOptions: ProgramOption[];
  existingPrograms: VaultLoyaltyProgram[];
}) {
  const [form, setForm] = useState({
    user_id: initialData?.user_id ?? users[0]?.id ?? 0,
    program_name: initialData?.program_name ?? "",
    alliance: initialData?.alliance ?? ("none" as string),
    membership_number: initialData?.membership_number_decrypted ?? "",
    notes: initialData?.notes_decrypted ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm({
        user_id: initialData?.user_id ?? users[0]?.id ?? 0,
        program_name: initialData?.program_name ?? "",
        alliance: initialData?.alliance ?? "none",
        membership_number: initialData?.membership_number_decrypted ?? "",
        notes: initialData?.notes_decrypted ?? "",
      });
      setError(null);
    }
  }, [isOpen, initialData, users]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.program_name.trim()) {
      setError("Program name is required");
      return;
    }
    setSaving(true);
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const isEditing = initialData && initialData.id > 0;

  // Filter out programs the selected user already has
  const usedPrograms = new Set(
    existingPrograms
      .filter((p) => p.user_id === form.user_id)
      .map((p) => p.program_name),
  );
  const availableOptions = programOptions.filter(
    (o) => !usedPrograms.has(o.program_name),
  );

  const handleProgramSelect = (programName: string) => {
    const opt = programOptions.find((o) => o.program_name === programName);
    setForm((p) => ({
      ...p,
      program_name: programName,
      alliance: opt?.alliance ?? "none",
    }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content modal-small"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>
            {isEditing ? `Edit ${form.program_name}` : "Add Loyalty Program"}
          </h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}
          <div className="form-group">
            <label>User *</label>
            <select
              value={form.user_id}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  user_id: Number(e.target.value),
                  ...(!isEditing ? { program_name: "", alliance: "none" } : {}),
                }))
              }
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nickname || u.name || `User #${u.id}`}
                </option>
              ))}
            </select>
          </div>
          {!isEditing && (
            <div className="form-group">
              <label>Program *</label>
              <select
                value={form.program_name}
                onChange={(e) => handleProgramSelect(e.target.value)}
              >
                <option value="">Select a program...</option>
                {(["star_alliance", "oneworld", "skyteam"] as const).map(
                  (alliance) => {
                    const group = availableOptions.filter(
                      (o) => o.alliance === alliance,
                    );
                    if (group.length === 0) return null;
                    return (
                      <optgroup
                        key={alliance}
                        label={ALLIANCE_LABELS[alliance] || alliance}
                      >
                        {group.map((opt) => (
                          <option
                            key={opt.program_name}
                            value={opt.program_name}
                          >
                            {opt.program_name} —{" "}
                            {opt.airlines.map((a) => a.name).join(", ")}
                          </option>
                        ))}
                      </optgroup>
                    );
                  },
                )}
              </select>
            </div>
          )}
          <div className="form-group">
            <label>Membership Number</label>
            <input
              type="text"
              value={form.membership_number}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  membership_number: e.target.value,
                }))
              }
              placeholder="Membership number"
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) =>
                setForm((p) => ({ ...p, notes: e.target.value }))
              }
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
