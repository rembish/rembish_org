import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useViewAs } from "../hooks/useViewAs";
import type {
  AdminTab,
  DocSection,
  DroneSubTab,
  MediaSubTab,
  PeopleSection,
} from "../components/admin/types";
import {
  DOC_SECTIONS,
  DRONE_SUB_TABS,
  MEDIA_SUB_TABS,
  PEOPLE_SECTIONS,
} from "../components/admin/types";
import TripsTab from "../components/admin/TripsTab";
import MediaTab from "../components/admin/MediaTab";
import PeopleTab from "../components/admin/PeopleTab";
import DocumentsTab from "../components/admin/DocumentsTab";
import LoyaltyTab from "../components/admin/LoyaltyTab";
import DronesTab from "../components/admin/DronesTab";

const validDocSections = new Set<string>(DOC_SECTIONS.map((s) => s.key));
const validPeopleSections = new Set<string>(PEOPLE_SECTIONS.map((s) => s.key));
const validDroneSubTabs = new Set<string>(DRONE_SUB_TABS.map((s) => s.key));
const validMediaSubTabs = new Set<string>(MEDIA_SUB_TABS.map((s) => s.key));

export default function Admin() {
  const { user, loading: authLoading } = useAuth();
  const { viewAsUser, setViewAsUser } = useViewAs();
  const navigate = useNavigate();
  const { tab, year } = useParams();
  const activeTab = (tab as AdminTab) || "trips";
  // For trips tab, 'year' is the year number
  // For media tab, 'year' is the sub-tab (instagram/memes) or ig_id
  // For documents tab, 'year' is the doc section (ids/vaccinations/visas)
  // For people tab, 'year' is the people section (close-ones/addresses)
  const selectedYear =
    tab === "media" ||
    tab === "documents" ||
    tab === "people" ||
    tab === "drones"
      ? null
      : year
        ? Number(year)
        : null;

  // Media sub-tab routing: /admin/media/instagram or /admin/media/memes
  // Also supports /admin/media/instagram/<ig_id> for deep-linking to a specific post
  const mediaSubTab: MediaSubTab =
    tab === "media" && year && validMediaSubTabs.has(year)
      ? (year as MediaSubTab)
      : tab === "media" && year && !validMediaSubTabs.has(year)
        ? "instagram" // year is an ig_id, so we're on Instagram sub-tab
        : "instagram";
  // If on media tab and year is not a sub-tab name, it's an Instagram ig_id
  const instagramIgId =
    tab === "media" && year && !validMediaSubTabs.has(year) ? year : null;

  const docSection: DocSection =
    tab === "documents" && year && validDocSections.has(year)
      ? (year as DocSection)
      : "ids";
  const readOnly = user?.role === "viewer" || !!viewAsUser;
  const defaultPeopleSection: PeopleSection = readOnly
    ? "fixers"
    : "close-ones";
  const peopleSection: PeopleSection =
    tab === "people" && year && validPeopleSections.has(year)
      ? (year as PeopleSection)
      : defaultPeopleSection;
  const droneSubTab: DroneSubTab =
    tab === "drones" && year && validDroneSubTabs.has(year)
      ? (year as DroneSubTab)
      : "flights";

  const setActiveTab = (newTab: AdminTab) => {
    if (newTab === "trips" && selectedYear) {
      navigate(`/admin/${newTab}/${selectedYear}`);
    } else if (newTab === "documents") {
      navigate(`/admin/documents/ids`);
    } else if (newTab === "people") {
      navigate(`/admin/people/${readOnly ? "fixers" : "close-ones"}`);
    } else if (newTab === "drones") {
      navigate(`/admin/drones/flights`);
    } else if (newTab === "media") {
      navigate(`/admin/media/instagram`);
    } else {
      navigate(`/admin/${newTab}`);
    }
  };

  const setSelectedYear = (newYear: number) => {
    navigate(`/admin/${activeTab}/${newYear}`);
  };

  const setInstagramIgId = (igId: string | null) => {
    if (igId) {
      navigate(`/admin/media/${igId}`, { replace: true });
    } else {
      navigate(`/admin/media/instagram`, { replace: true });
    }
  };

  const setMediaSubTab = (sub: MediaSubTab) => {
    navigate(`/admin/media/${sub}`, { replace: true });
  };

  const setDocSection = (section: DocSection) => {
    navigate(`/admin/documents/${section}`, { replace: true });
  };

  const setPeopleSection = (section: PeopleSection) => {
    navigate(`/admin/people/${section}`, { replace: true });
  };

  const setDroneSubTab = (sub: DroneSubTab) => {
    navigate(`/admin/drones/${sub}`, { replace: true });
  };

  // Redirect users without any role
  if (!authLoading && !user?.role) {
    return <Navigate to="/" replace />;
  }

  // Viewers can only see Trips, People, and Drones tabs
  if (
    readOnly &&
    activeTab !== "trips" &&
    activeTab !== "people" &&
    activeTab !== "drones" &&
    !authLoading
  ) {
    return <Navigate to="/admin/trips" replace />;
  }

  // Remove year from URL for tabs that don't use it
  if (activeTab === "loyalty" && year) {
    return <Navigate to="/admin/loyalty" replace />;
  }
  // Default media to instagram sub-tab
  if (activeTab === "media" && !year) {
    return <Navigate to="/admin/media/instagram" replace />;
  }
  // Default drones to flights sub-tab
  if (activeTab === "drones" && !year) {
    return <Navigate to="/admin/drones/flights" replace />;
  }
  // Default documents to ids sub-tab
  if (activeTab === "documents" && !year) {
    return <Navigate to="/admin/documents/ids" replace />;
  }
  // Default people sub-tab
  if (activeTab === "people" && !year) {
    return (
      <Navigate
        to={`/admin/people/${readOnly ? "fixers" : "close-ones"}`}
        replace
      />
    );
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

        {viewAsUser && (
          <div className="view-as-banner">
            {viewAsUser.picture && (
              <img src={viewAsUser.picture} alt="" className="view-as-avatar" />
            )}
            <span>
              Viewing as <strong>{viewAsUser.name || "User"}</strong>
            </span>
            <button
              className="view-as-exit"
              onClick={() => setViewAsUser(null)}
            >
              Exit
            </button>
          </div>
        )}

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "trips" ? "active" : ""}`}
            onClick={() => setActiveTab("trips")}
          >
            Trips
          </button>
          <button
            className={`admin-tab ${activeTab === "people" ? "active" : ""}`}
            onClick={() => setActiveTab("people")}
          >
            People
          </button>
          <button
            className={`admin-tab ${activeTab === "drones" ? "active" : ""}`}
            onClick={() => setActiveTab("drones")}
          >
            Drones
          </button>
          {!readOnly && (
            <>
              <button
                className={`admin-tab ${activeTab === "media" ? "active" : ""}`}
                onClick={() => setActiveTab("media")}
              >
                Media
              </button>
              <button
                className={`admin-tab ${activeTab === "documents" ? "active" : ""}`}
                onClick={() => setActiveTab("documents")}
              >
                Documents
              </button>
              <button
                className={`admin-tab ${activeTab === "loyalty" ? "active" : ""}`}
                onClick={() => setActiveTab("loyalty")}
              >
                Loyalty
              </button>
            </>
          )}
        </div>

        <div className="admin-content">
          {activeTab === "trips" && (
            <TripsTab
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
              readOnly={readOnly}
            />
          )}
          {activeTab === "media" && (
            <MediaTab
              activeSubTab={mediaSubTab}
              onSubTabChange={setMediaSubTab}
              instagramIgId={instagramIgId}
              onIgIdChange={setInstagramIgId}
            />
          )}
          {activeTab === "people" && (
            <PeopleTab
              activeSection={peopleSection}
              onSectionChange={setPeopleSection}
              readOnly={readOnly}
            />
          )}
          {activeTab === "documents" && (
            <DocumentsTab
              activeSection={docSection}
              onSectionChange={setDocSection}
            />
          )}
          {activeTab === "loyalty" && <LoyaltyTab />}
          {activeTab === "drones" && (
            <DronesTab
              activeSubTab={droneSubTab}
              onSubTabChange={setDroneSubTab}
              readOnly={readOnly}
            />
          )}
        </div>
      </div>
    </section>
  );
}
