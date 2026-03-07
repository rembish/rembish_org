import type { MediaSubTab } from "./types";
import { MEDIA_SUB_TABS } from "./types";
import CosplayTab from "./CosplayTab";
import InstagramTab from "./InstagramTab";
import MemesTab from "./MemesTab";

interface Props {
  activeSubTab: MediaSubTab;
  onSubTabChange: (sub: MediaSubTab) => void;
  instagramIgId: string | null;
  onIgIdChange: (igId: string | null) => void;
}

export default function MediaTab({
  activeSubTab,
  onSubTabChange,
  instagramIgId,
  onIgIdChange,
}: Props) {
  return (
    <div className="media-tab">
      <div className="vault-sub-tabs">
        {MEDIA_SUB_TABS.map((st) => (
          <button
            key={st.key}
            className={`vault-sub-tab${activeSubTab === st.key ? " active" : ""}`}
            onClick={() => onSubTabChange(st.key)}
          >
            {st.label}
          </button>
        ))}
      </div>

      {activeSubTab === "instagram" && (
        <InstagramTab
          key={instagramIgId ?? "latest"}
          initialIgId={instagramIgId}
          onIgIdChange={onIgIdChange}
        />
      )}
      {activeSubTab === "memes" && <MemesTab />}
      {activeSubTab === "cosplay" && <CosplayTab />}
    </div>
  );
}
