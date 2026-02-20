import { useCallback, useEffect, useState } from "react";
import { BiCake, BiPencil, BiPlus, BiTrash } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import UserFormModal, { UserFormData } from "../UserFormModal";
import type { CloseOneUser } from "./types";

export default function CloseOnesTab() {
  const [users, setUsers] = useState<CloseOneUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<CloseOneUser | null>(null);

  const fetchUsers = useCallback(() => {
    apiFetch("/api/v1/admin/users/")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch users");
        return res.json();
      })
      .then((data) => {
        setUsers(data.users || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleAddUser = () => {
    setEditingUser(null);
    setModalOpen(true);
  };

  const handleEditUser = (user: CloseOneUser) => {
    setEditingUser(user);
    setModalOpen(true);
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("Are you sure you want to remove this user?")) return;

    try {
      const res = await apiFetch(`/api/v1/admin/users/${userId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete user");
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  const handleSaveUser = async (data: UserFormData) => {
    const url = editingUser
      ? `/api/v1/admin/users/${editingUser.id}`
      : "/api/v1/admin/users/";
    const method = editingUser ? "PUT" : "POST";

    // Convert empty strings to null for optional fields
    const payload = {
      ...data,
      birthday: data.birthday || null,
    };

    const res = await apiFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      let message = "Failed to save user";
      if (typeof errorData.detail === "string") {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        message = errorData.detail
          .map((e: { msg: string }) => e.msg)
          .join(", ");
      }
      throw new Error(message);
    }

    fetchUsers();
  };

  const getInitialFormData = (): UserFormData | null => {
    if (!editingUser) return null;
    return {
      email: editingUser.email,
      name: editingUser.name || "",
      nickname: editingUser.nickname || "",
      birthday: editingUser.birthday || "",
    };
  };

  if (loading) {
    return <p>Loading users...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  return (
    <div className="close-ones-tab">
      <div className="close-ones-header">
        <button className="btn-add-user" onClick={handleAddUser}>
          <BiPlus /> Add User
        </button>
      </div>

      <div className="users-grid">
        {users.length === 0 ? (
          <p className="no-users">No close ones added yet.</p>
        ) : (
          users.map((user) => (
            <div key={user.id} className="user-card">
              <div className="user-card-avatar">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.nickname || user.name || ""}
                  />
                ) : (
                  <span className="avatar-initial">
                    {(user.nickname ||
                      user.name ||
                      user.email)[0].toUpperCase()}
                  </span>
                )}
              </div>
              <div className="user-card-info">
                <div className="user-card-name">
                  {user.nickname || user.name || "—"}
                  {user.is_admin && <span className="admin-badge">Admin</span>}
                  <span
                    className={`status-badge ${user.is_active ? "active" : "pending"}`}
                  >
                    {user.is_active ? "Active" : "Pending"}
                  </span>
                </div>
                <div className="user-card-email">{user.email}</div>
                <div className="user-card-meta">
                  {user.birthday && (
                    <span className="birthday-badge">
                      <BiCake />{" "}
                      {new Date(user.birthday + "T00:00:00").toLocaleDateString(
                        "en-GB",
                        { day: "numeric", month: "short" },
                      )}
                    </span>
                  )}
                  {user.trips_count > 0 && (
                    <span className="trips-badge">
                      {user.trips_count} trip{user.trips_count !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <div className="user-card-actions">
                <button
                  className="user-action-btn"
                  onClick={() => handleEditUser(user)}
                  title="Edit"
                >
                  <BiPencil />
                </button>
                <button
                  className="user-action-btn delete"
                  onClick={() => handleDeleteUser(user.id)}
                  title="Remove"
                >
                  <BiTrash />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <UserFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveUser}
        initialData={getInitialFormData()}
        title={editingUser ? "Edit User" : "Add User"}
      />
    </div>
  );
}
