import { useState } from "react";
import { BiPlus } from "react-icons/bi";
import type { DroneSubTab } from "./types";
import { DRONE_SUB_TABS } from "./types";
import DroneFlightsList from "./DroneFlightsList";
import MyDrones from "./MyDrones";
import BatteriesList from "./BatteriesList";

export default function DronesTab({
  activeSubTab,
  onSubTabChange,
  readOnly,
}: {
  activeSubTab: DroneSubTab;
  onSubTabChange: (sub: DroneSubTab) => void;
  readOnly?: boolean;
}) {
  const [addDroneTrigger, setAddDroneTrigger] = useState(0);
  const [addBatteryTrigger, setAddBatteryTrigger] = useState(0);
  const [batteryRefresh, setBatteryRefresh] = useState(0);

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
      </div>

      {activeSubTab === "flights" && <DroneFlightsList readOnly={readOnly} />}
      {activeSubTab === "hardware" && (
        <div className="hardware-sections">
          <div className="hardware-section">
            <div className="hardware-section-header">
              <h3>Drones</h3>
              {!readOnly && (
                <button
                  className="btn-icon"
                  onClick={() => setAddDroneTrigger((n) => n + 1)}
                  title="Add drone"
                >
                  <BiPlus />
                </button>
              )}
            </div>
            <MyDrones
              readOnly={readOnly}
              addTrigger={addDroneTrigger}
              onRetire={() => setBatteryRefresh((n) => n + 1)}
            />
          </div>
          <div className="hardware-section">
            <div className="hardware-section-header">
              <h3>Batteries</h3>
              {!readOnly && (
                <button
                  className="btn-icon"
                  onClick={() => setAddBatteryTrigger((n) => n + 1)}
                  title="Add battery"
                >
                  <BiPlus />
                </button>
              )}
            </div>
            <BatteriesList
              readOnly={readOnly}
              addTrigger={addBatteryTrigger}
              refreshTrigger={batteryRefresh}
            />
          </div>
        </div>
      )}
    </div>
  );
}
