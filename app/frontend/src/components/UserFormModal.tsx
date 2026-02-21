import { useEffect, useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { BiX } from "react-icons/bi";

// Parse date string (YYYY-MM-DD) as local date
function parseLocalDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

// Format date as YYYY-MM-DD
function formatLocalDate(date: Date | null): string {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export interface UserFormData {
  email: string;
  name: string;
  nickname: string;
  birthday: string;
  role: string;
}

interface UserFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: UserFormData) => Promise<void>;
  initialData?: UserFormData | null;
  title: string;
}

const emptyFormData: UserFormData = {
  email: "",
  name: "",
  nickname: "",
  birthday: "",
  role: "",
};

export default function UserFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  title,
}: UserFormModalProps) {
  const [formData, setFormData] = useState<UserFormData>(emptyFormData);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData(initialData);
      } else {
        setFormData(emptyFormData);
      }
      setError(null);
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.email.trim()) {
      setError("Email is required");
      return;
    }

    // Basic email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError("Please enter a valid email address");
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save user");
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
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            <BiX />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="user-form">
          {error && <div className="form-error">{error}</div>}

          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, email: e.target.value }))
              }
              placeholder="user@example.com"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="Full name"
            />
          </div>

          <div className="form-group">
            <label>Nickname</label>
            <input
              type="text"
              value={formData.nickname}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, nickname: e.target.value }))
              }
              placeholder="Short name"
            />
          </div>

          <div className="form-group">
            <label>Birthday</label>
            <DatePicker
              selected={parseLocalDate(formData.birthday)}
              onChange={(date: Date | null) =>
                setFormData((prev) => ({
                  ...prev,
                  birthday: formatLocalDate(date),
                }))
              }
              dateFormat="dd.MM.yyyy"
              placeholderText="dd.mm.yyyy"
              calendarStartDay={1}
              showYearDropdown
              showMonthDropdown
              dropdownMode="select"
              isClearable
            />
          </div>

          <div className="form-group">
            <label>Role</label>
            <select
              value={formData.role}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, role: e.target.value }))
              }
            >
              <option value="">None</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
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
