import { useCallback, useEffect, useRef, useState } from "react";
import {
  BiPlus,
  BiTrash,
  BiPencil,
  BiUpload,
  BiStar,
  BiSolidStar,
} from "react-icons/bi";
import { apiFetch } from "../../lib/api";

interface CosplayPhoto {
  id: number;
  filename: string;
  width: number | null;
  height: number | null;
  sort_order: number;
}

interface CosplayCostume {
  id: number;
  name: string;
  description: string | null;
  sort_order: number;
  cover_photo_id: number | null;
  photos: CosplayPhoto[];
}

export default function CosplayTab() {
  const [costumes, setCostumes] = useState<CosplayCostume[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formOrder, setFormOrder] = useState(0);
  const [uploading, setUploading] = useState<number | null>(null);
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});

  const fetchCostumes = useCallback(async () => {
    const res = await apiFetch("/api/v1/admin/cosplay");
    if (res.ok) setCostumes(await res.json());
  }, []);

  useEffect(() => {
    fetchCostumes();
  }, [fetchCostumes]);

  const resetForm = () => {
    setShowForm(false);
    setEditId(null);
    setFormName("");
    setFormDesc("");
    setFormOrder(0);
  };

  const handleSave = async () => {
    const body = {
      name: formName,
      description: formDesc || null,
      sort_order: formOrder,
    };
    const url = editId
      ? `/api/v1/admin/cosplay/${editId}`
      : "/api/v1/admin/cosplay";
    const method = editId ? "PUT" : "POST";
    const res = await apiFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      resetForm();
      fetchCostumes();
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this costume and all its photos?")) return;
    const res = await apiFetch(`/api/v1/admin/cosplay/${id}`, {
      method: "DELETE",
    });
    if (res.ok) fetchCostumes();
  };

  const handleEdit = (c: CosplayCostume) => {
    setEditId(c.id);
    setFormName(c.name);
    setFormDesc(c.description || "");
    setFormOrder(c.sort_order);
    setShowForm(true);
  };

  const handleUpload = async (costumeId: number, files: FileList) => {
    setUploading(costumeId);
    for (const file of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", file);
      await apiFetch(`/api/v1/admin/cosplay/${costumeId}/photos`, {
        method: "POST",
        body: fd,
      });
    }
    setUploading(null);
    fetchCostumes();
  };

  const handleSetCover = async (costumeId: number, photoId: number) => {
    const res = await apiFetch(
      `/api/v1/admin/cosplay/${costumeId}/cover/${photoId}`,
      { method: "PUT" },
    );
    if (res.ok) fetchCostumes();
  };

  const handleDeletePhoto = async (costumeId: number, photoId: number) => {
    const res = await apiFetch(
      `/api/v1/admin/cosplay/${costumeId}/photos/${photoId}`,
      {
        method: "DELETE",
      },
    );
    if (res.ok) fetchCostumes();
  };

  return (
    <div className="cosplay-admin">
      <div className="cosplay-admin-header">
        <h3>Cosplay Costumes ({costumes.length})</h3>
        <button
          className="cosplay-btn-add"
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
        >
          <BiPlus /> Add Costume
        </button>
      </div>

      {showForm && (
        <div className="cosplay-admin-form">
          <input
            type="text"
            placeholder="Costume name"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={formDesc}
            onChange={(e) => setFormDesc(e.target.value)}
          />
          <input
            type="number"
            placeholder="Sort order"
            value={formOrder}
            onChange={(e) => setFormOrder(parseInt(e.target.value) || 0)}
          />
          <div className="cosplay-admin-form-actions">
            <button className="btn-save" onClick={handleSave}>
              {editId ? "Update" : "Create"}
            </button>
            <button className="btn-cancel" onClick={resetForm}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {costumes.map((c) => (
        <div key={c.id} className="cosplay-admin-costume">
          <div className="cosplay-admin-costume-header">
            <span className="cosplay-admin-costume-name">
              {c.name}
              {c.description && (
                <span className="cosplay-admin-costume-desc">
                  {" "}
                  &mdash; {c.description}
                </span>
              )}
              <span className="cosplay-admin-costume-count">
                {" "}
                ({c.photos.length} photos)
              </span>
            </span>
            <span className="cosplay-admin-costume-actions">
              <button
                className="cosplay-btn-icon"
                onClick={() => handleEdit(c)}
                title="Edit"
              >
                <BiPencil />
              </button>
              <button
                className="cosplay-btn-icon cosplay-btn-icon-danger"
                onClick={() => handleDelete(c.id)}
                title="Delete"
              >
                <BiTrash />
              </button>
              <button
                className="cosplay-btn-upload"
                onClick={() => fileRefs.current[c.id]?.click()}
                disabled={uploading === c.id}
              >
                <BiUpload /> {uploading === c.id ? "Uploading..." : "Upload"}
              </button>
              <input
                ref={(el) => {
                  fileRefs.current[c.id] = el;
                }}
                type="file"
                accept="image/*"
                multiple
                style={{ display: "none" }}
                onChange={(e) => {
                  if (e.target.files?.length)
                    handleUpload(c.id, e.target.files);
                  e.target.value = "";
                }}
              />
            </span>
          </div>
          {c.photos.length > 0 && (
            <div className="cosplay-admin-photos">
              {c.photos.map((p) => (
                <div
                  key={p.id}
                  className={`cosplay-admin-photo${c.cover_photo_id === p.id ? " is-cover" : ""}`}
                >
                  <img
                    src={`/api/v1/travels/cosplay/photos/${p.id}`}
                    alt={c.name}
                    loading="lazy"
                  />
                  <button
                    className="cosplay-admin-photo-cover"
                    onClick={() => handleSetCover(c.id, p.id)}
                    title={
                      c.cover_photo_id === p.id
                        ? "Current cover"
                        : "Set as cover"
                    }
                  >
                    {c.cover_photo_id === p.id ? <BiSolidStar /> : <BiStar />}
                  </button>
                  <button
                    className="cosplay-admin-photo-delete"
                    onClick={() => handleDeletePhoto(c.id, p.id)}
                    title="Delete photo"
                  >
                    <BiTrash />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
