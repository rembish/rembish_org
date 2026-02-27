import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { MemeItem, MemeStats, MemeStatus } from "./types";
import { fmtDate, MEME_CATEGORY_LABELS, MEME_LANGUAGE_LABELS } from "./types";

const STATUS_FILTERS: { key: MemeStatus | "all"; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "all", label: "All" },
];

const CATEGORIES = ["dev", "math", "internet", "life", "edge"];
const LANGUAGES = ["en", "ru", "cs", "uk", "pl", "other"];

export default function MemesTab() {
  const [memes, setMemes] = useState<MemeItem[]>([]);
  const [stats, setStats] = useState<MemeStats | null>(null);
  const [filter, setFilter] = useState<MemeStatus | "all">("pending");
  const [total, setTotal] = useState(0);
  const [editing, setEditing] = useState<Record<number, Partial<MemeItem>>>({});

  const fetchStats = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/admin/memes/stats");
      if (res.ok) setStats(await res.json());
    } catch {
      /* stats are best-effort */
    }
  }, []);

  const fetchMemes = useCallback(async () => {
    const params = new URLSearchParams();
    if (filter !== "all") params.set("status", filter);
    params.set("limit", "100");
    try {
      const res = await apiFetch(`/api/v1/admin/memes?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setMemes(data.memes);
        setTotal(data.total);
      }
    } catch {
      /* fail silently */
    }
  }, [filter]);

  useEffect(() => {
    fetchStats();
    fetchMemes();
  }, [fetchStats, fetchMemes]);

  const handleApprove = async (id: number) => {
    const overrides = editing[id] || {};
    const body: Record<string, string | null> = {};
    if (overrides.category !== undefined) body.category = overrides.category;
    if (overrides.language !== undefined) body.language = overrides.language;
    if (overrides.description_en !== undefined)
      body.description_en = overrides.description_en;

    const res = await apiFetch(`/api/v1/admin/memes/${id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      setEditing((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      fetchMemes();
      fetchStats();
    }
  };

  const handleReject = async (id: number) => {
    const res = await apiFetch(`/api/v1/admin/memes/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (res.ok) {
      setEditing((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      fetchMemes();
      fetchStats();
    }
  };

  const setField = (
    id: number,
    field: keyof MemeItem,
    value: string | boolean | null,
  ) => {
    setEditing((prev) => ({
      ...prev,
      [id]: { ...prev[id], [field]: value },
    }));
  };

  const getVal = (meme: MemeItem, field: keyof MemeItem) => {
    const override = editing[meme.id];
    if (override && field in override)
      return override[field as keyof typeof override];
    return meme[field];
  };

  return (
    <div className="memes-tab">
      {stats && (
        <div className="memes-stats">
          <span className="memes-stat pending">
            Pending: <strong>{stats.pending}</strong>
          </span>
          <span className="memes-stat approved">
            Approved: <strong>{stats.approved}</strong>
          </span>
          <span className="memes-stat rejected">
            Rejected: <strong>{stats.rejected}</strong>
          </span>
          <span className="memes-stat total">
            Total: <strong>{stats.total}</strong>
          </span>
        </div>
      )}

      <div className="memes-filters">
        {STATUS_FILTERS.map((sf) => (
          <button
            key={sf.key}
            className={`memes-filter-btn ${filter === sf.key ? "active" : ""}`}
            onClick={() => setFilter(sf.key)}
          >
            {sf.label}
          </button>
        ))}
      </div>

      {memes.length === 0 && (
        <p className="memes-empty">
          No {filter !== "all" ? filter : ""} memes.
        </p>
      )}

      <div className="memes-grid">
        {memes.map((meme) => (
          <div key={meme.id} className={`meme-card meme-${meme.status}`}>
            <div className="meme-image-wrap">
              <img
                src={`/api/v1/admin/memes/${meme.id}/media`}
                alt={meme.description_en || `Meme #${meme.id}`}
                loading="lazy"
              />
            </div>

            <div className="meme-meta">
              <div className="meme-badges">
                <span
                  className={`meme-badge meme-badge-status meme-badge-${meme.status}`}
                >
                  {meme.status}
                </span>
                {meme.is_site_worthy !== null && (
                  <span
                    className={`meme-badge ${meme.is_site_worthy ? "meme-badge-worthy" : "meme-badge-unworthy"}`}
                  >
                    {meme.is_site_worthy ? "Site-worthy" : "Not worthy"}
                  </span>
                )}
              </div>

              <div className="meme-fields">
                <label>
                  Category
                  <select
                    value={(getVal(meme, "category") as string) || ""}
                    onChange={(e) =>
                      setField(meme.id, "category", e.target.value || null)
                    }
                  >
                    <option value="">—</option>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {MEME_CATEGORY_LABELS[c] || c}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Language
                  <select
                    value={(getVal(meme, "language") as string) || ""}
                    onChange={(e) =>
                      setField(meme.id, "language", e.target.value || null)
                    }
                  >
                    <option value="">—</option>
                    {LANGUAGES.map((l) => (
                      <option key={l} value={l}>
                        {MEME_LANGUAGE_LABELS[l] || l}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="meme-desc-label">
                Description
                <textarea
                  rows={2}
                  value={(getVal(meme, "description_en") as string) || ""}
                  onChange={(e) =>
                    setField(meme.id, "description_en", e.target.value)
                  }
                />
              </label>

              <div className="meme-info">
                <span>{fmtDate(meme.created_at.split("T")[0])}</span>
                {meme.width && meme.height && (
                  <span>
                    {meme.width}&times;{meme.height}
                  </span>
                )}
                <span>#{meme.id}</span>
              </div>

              {meme.status === "pending" && (
                <div className="meme-actions">
                  <button
                    className="meme-btn meme-btn-approve"
                    onClick={() => handleApprove(meme.id)}
                  >
                    Approve
                  </button>
                  <button
                    className="meme-btn meme-btn-reject"
                    onClick={() => handleReject(meme.id)}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {total > memes.length && (
        <p className="memes-more">
          Showing {memes.length} of {total}
        </p>
      )}
    </div>
  );
}
