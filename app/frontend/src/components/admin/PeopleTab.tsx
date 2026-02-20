import { useRef, useState } from "react";
import { BiPlus, BiSearch } from "react-icons/bi";
import type { PeopleSection } from "./types";
import { PEOPLE_SECTIONS } from "./types";
import CloseOnesTab from "./CloseOnesTab";
import AddressesTab from "./AddressesTab";

interface Props {
  activeSection: PeopleSection;
  onSectionChange: (section: PeopleSection) => void;
}

export default function PeopleTab({ activeSection, onSectionChange }: Props) {
  const [addTrigger, setAddTrigger] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 200);
  };

  return (
    <div className="vault-content">
      <div className="vault-sub-tabs">
        {PEOPLE_SECTIONS.map((s) => (
          <button
            key={s.key}
            className={`vault-sub-tab${activeSection === s.key ? " active" : ""}`}
            onClick={() => onSectionChange(s.key)}
          >
            {s.label}
          </button>
        ))}
        <div className="vault-sub-tabs-actions">
          {activeSection === "addresses" && (
            <div className="addresses-search">
              <BiSearch />
              <input
                type="text"
                placeholder="Search address..."
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>
          )}
          <button
            className="btn-icon"
            onClick={() => setAddTrigger((n) => n + 1)}
            title={activeSection === "close-ones" ? "Add user" : "Add address"}
          >
            <BiPlus />
          </button>
        </div>
      </div>

      {activeSection === "close-ones" && (
        <CloseOnesTab addTrigger={addTrigger} />
      )}
      {activeSection === "addresses" && (
        <AddressesTab addTrigger={addTrigger} search={debouncedSearch} />
      )}
    </div>
  );
}
