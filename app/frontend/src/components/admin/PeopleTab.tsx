import { useRef, useState } from "react";
import { BiPlus, BiSearch } from "react-icons/bi";
import type { PeopleSection } from "./types";
import { PEOPLE_SECTIONS } from "./types";
import CloseOnesTab from "./CloseOnesTab";
import AddressesTab from "./AddressesTab";
import FixersTab from "./FixersTab";

interface Props {
  activeSection: PeopleSection;
  onSectionChange: (section: PeopleSection) => void;
  readOnly?: boolean;
}

export default function PeopleTab({
  activeSection,
  onSectionChange,
  readOnly,
}: Props) {
  const [addTrigger, setAddTrigger] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 200);
  };

  const visibleSections = readOnly
    ? PEOPLE_SECTIONS.filter((s) => s.key === "fixers")
    : PEOPLE_SECTIONS;

  const addTitle =
    activeSection === "close-ones"
      ? "Add user"
      : activeSection === "addresses"
        ? "Add address"
        : "Add fixer";

  return (
    <div className="vault-content">
      <div className="vault-sub-tabs">
        {visibleSections.map((s) => (
          <button
            key={s.key}
            className={`vault-sub-tab${activeSection === s.key ? " active" : ""}`}
            onClick={() => onSectionChange(s.key)}
          >
            {s.label}
          </button>
        ))}
        <div className="vault-sub-tabs-actions">
          {(activeSection === "addresses" || activeSection === "fixers") && (
            <div className="addresses-search">
              <BiSearch />
              <input
                type="text"
                placeholder={
                  activeSection === "addresses"
                    ? "Search address..."
                    : "Search fixer..."
                }
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>
          )}
          {!readOnly && (
            <button
              className="btn-icon"
              onClick={() => setAddTrigger((n) => n + 1)}
              title={addTitle}
            >
              <BiPlus />
            </button>
          )}
        </div>
      </div>

      {!readOnly && activeSection === "close-ones" && (
        <CloseOnesTab addTrigger={addTrigger} />
      )}
      {!readOnly && activeSection === "addresses" && (
        <AddressesTab addTrigger={addTrigger} search={debouncedSearch} />
      )}
      {activeSection === "fixers" && (
        <FixersTab
          addTrigger={addTrigger}
          search={debouncedSearch}
          readOnly={readOnly}
        />
      )}
    </div>
  );
}
