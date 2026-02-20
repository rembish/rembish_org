import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { AdminTab } from "../components/admin/types";
import TripsTab from "../components/admin/TripsTab";
import CloseOnesTab from "../components/admin/CloseOnesTab";
import InstagramTab from "../components/admin/InstagramTab";
import VaultTab from "../components/admin/VaultTab";

export default function Admin() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { tab, year } = useParams();
  const activeTab = (tab as AdminTab) || "trips";
  // For trips tab, 'year' is the year number
  // For instagram tab, 'year' is the ig_id (Instagram ID string)
  const selectedYear = tab === "instagram" ? null : year ? Number(year) : null;
  const instagramIgId = tab === "instagram" && year ? year : null;

  const setActiveTab = (newTab: AdminTab) => {
    if (newTab === "trips" && selectedYear) {
      navigate(`/admin/${newTab}/${selectedYear}`);
    } else {
      navigate(`/admin/${newTab}`);
    }
  };

  const setSelectedYear = (newYear: number) => {
    navigate(`/admin/${activeTab}/${newYear}`);
  };

  const setInstagramIgId = (igId: string | null) => {
    if (igId) {
      navigate(`/admin/instagram/${igId}`, { replace: true });
    } else {
      navigate(`/admin/instagram`, { replace: true });
    }
  };

  // Redirect non-admin users
  if (!authLoading && !user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  // Remove year from URL for close-ones and vault tabs
  if (activeTab === "close-ones" && year) {
    return <Navigate to="/admin/close-ones" replace />;
  }
  if (activeTab === "vault" && year) {
    return <Navigate to="/admin/vault" replace />;
  }

  if (authLoading) {
    return (
      <section id="admin" className="admin">
        <div className="container">
          <p>Loading...</p>
        </div>
      </section>
    );
  }

  return (
    <section id="admin" className="admin">
      <div className="container">
        <div className="admin-header">
          <h1>Admin</h1>
        </div>

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "trips" ? "active" : ""}`}
            onClick={() => setActiveTab("trips")}
          >
            Trips
          </button>
          <button
            className={`admin-tab ${activeTab === "instagram" ? "active" : ""}`}
            onClick={() => setActiveTab("instagram")}
          >
            Instagram
          </button>
          <button
            className={`admin-tab ${activeTab === "close-ones" ? "active" : ""}`}
            onClick={() => setActiveTab("close-ones")}
          >
            Close Ones
          </button>
          <button
            className={`admin-tab ${activeTab === "vault" ? "active" : ""}`}
            onClick={() => setActiveTab("vault")}
          >
            Vault
          </button>
        </div>

        <div className="admin-content">
          {activeTab === "trips" && (
            <TripsTab
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />
          )}
          {activeTab === "close-ones" && <CloseOnesTab />}
          {activeTab === "instagram" && (
            <InstagramTab
              key={instagramIgId ?? "latest"}
              initialIgId={instagramIgId}
              onIgIdChange={setInstagramIgId}
            />
          )}
          {activeTab === "vault" && <VaultTab />}
        </div>
      </div>
    </section>
  );
}
