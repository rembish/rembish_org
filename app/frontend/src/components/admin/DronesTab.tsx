import { useState } from "react";
import { BiPlus } from "react-icons/bi";
import type { DroneSubTab } from "./types";
import { DRONE_SUB_TABS } from "./types";
import DroneFlightsList from "./DroneFlightsList";
import MyDrones from "./MyDrones";
import DroneStats from "./DroneStats";

export default function DronesTab({
  activeSubTab,
  onSubTabChange,
  readOnly,
}: {
  activeSubTab: DroneSubTab;
  onSubTabChange: (sub: DroneSubTab) => void;
  readOnly?: boolean;
}) {
  const [addTrigger, setAddTrigger] = useState(0);

  return (
    <div className="drones-tab">
      <div className="vault-sub-tabs">
        {DRONE_SUB_TABS.map((t) => (
          <button
            key={t.key}
            className={`admin-tab ${activeSubTab === t.key ? "active" : ""}`}
            onClick={() => onSubTabChange(t.key)}
          >
            {t.label}
          </button>
        ))}
        {!readOnly && activeSubTab === "my-drones" && (
          <div className="vault-sub-tabs-actions">
            <button
              className="btn-icon"
              onClick={() => setAddTrigger((n) => n + 1)}
              title="Add drone"
            >
              <BiPlus />
            </button>
          </div>
        )}
      </div>

      {activeSubTab === "flights" && <DroneFlightsList readOnly={readOnly} />}
      {activeSubTab === "my-drones" && (
        <MyDrones readOnly={readOnly} addTrigger={addTrigger} />
      )}
      {activeSubTab === "stats" && <DroneStats />}
    </div>
  );
}
