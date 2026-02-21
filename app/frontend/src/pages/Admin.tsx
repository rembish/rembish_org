import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useViewAs } from "../hooks/useViewAs";
import type {
  AdminTab,
  DocSection,
  PeopleSection,
} from "../components/admin/types";
import { DOC_SECTIONS, PEOPLE_SECTIONS } from "../components/admin/types";
import TripsTab from "../components/admin/TripsTab";
import InstagramTab from "../components/admin/InstagramTab";
import PeopleTab from "../components/admin/PeopleTab";
import DocumentsTab from "../components/admin/DocumentsTab";
import LoyaltyTab from "../components/admin/LoyaltyTab";

const validDocSections = new Set<string>(DOC_SECTIONS.map((s) => s.key));
const validPeopleSections = new Set<string>(PEOPLE_SECTIONS.map((s) => s.key));

export default function Admin() {
  const { user, loading: authLoading } = useAuth();
  const { viewAsUser, setViewAsUser } = useViewAs();
  const navigate = useNavigate();
  const { tab, year } = useParams();
  const activeTab = (tab as AdminTab) || "trips";
  // For trips tab, 'year' is the year number
  // For instagram tab, 'year' is the ig_id (Instagram ID string)
  // For documents tab, 'year' is the doc section (ids/vaccinations/visas)
  // For people tab, 'year' is the people section (close-ones/addresses)
  const selectedYear =
    tab === "instagram" || tab === "documents" || tab === "people"
      ? null
      : year
        ? Number(year)
        : null;
  const instagramIgId = tab === "instagram" && year ? year : null;
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

  const setActiveTab = (newTab: AdminTab) => {
    if (newTab === "trips" && selectedYear) {
      navigate(`/admin/${newTab}/${selectedYear}`);
    } else if (newTab === "documents") {
      navigate(`/admin/documents/ids`);
    } else if (newTab === "people") {
      navigate(`/admin/people/${readOnly ? "fixers" : "close-ones"}`);
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

  const setDocSection = (section: DocSection) => {
    navigate(`/admin/documents/${section}`, { replace: true });
  };

  const setPeopleSection = (section: PeopleSection) => {
    navigate(`/admin/people/${section}`, { replace: true });
  };

  // Redirect users without any role
  if (!authLoading && !user?.role) {
    return <Navigate to="/" replace />;
  }

  // Viewers can only see Trips and People tabs
  if (
    readOnly &&
    activeTab !== "trips" &&
    activeTab !== "people" &&
    !authLoading
  ) {
    return <Navigate to="/admin/trips" replace />;
  }

  // Remove year from URL for tabs that don't use it
  if (activeTab === "loyalty" && year) {
    return <Navigate to="/admin/loyalty" replace />;
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
          {!readOnly && (
            <>
              <button
                className={`admin-tab ${activeTab === "instagram" ? "active" : ""}`}
                onClick={() => setActiveTab("instagram")}
              >
                Instagram
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
          {activeTab === "instagram" && (
            <InstagramTab
              key={instagramIgId ?? "latest"}
              initialIgId={instagramIgId}
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
        </div>
      </div>
    </section>
  );
}
