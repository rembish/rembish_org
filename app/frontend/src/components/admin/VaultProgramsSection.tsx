import {
  BiCheck,
  BiCopy,
  BiCreditCard,
  BiNote,
  BiPencil,
  BiPlus,
  BiSearch,
  BiStar,
  BiTrash,
} from "react-icons/bi";
import type { VaultLoyaltyProgram, VaultUser, ProgramOption } from "./types";
import { ALLIANCE_LABELS } from "./types";

interface Props {
  programs: VaultLoyaltyProgram[];
  programOptions: ProgramOption[];
  selectedUserId: number | null;
  myUserId: number | null;
  users: VaultUser[];
  copied: string | null;
  expandedAlliances: Set<string>;
  airlineSearch: string;
  onAirlineSearchChange: (value: string) => void;
  onExpandedAlliancesChange: React.Dispatch<React.SetStateAction<Set<string>>>;
  onEditProg: (prog: VaultLoyaltyProgram) => void;
  onAddProg: () => void;
  onDeleteProg: (id: number) => void;
  onToggleFavorite: (id: number) => void;
  onCopy: (text: string, id: string) => void;
  getUserName: (userId: number) => string;
  getUser: (userId: number) => VaultUser | undefined;
}

export default function VaultProgramsSection({
  programs,
  programOptions,
  selectedUserId,
  myUserId,
  copied,
  expandedAlliances,
  airlineSearch,
  onAirlineSearchChange,
  onExpandedAlliancesChange,
  onEditProg,
  onAddProg,
  onDeleteProg,
  onToggleFavorite,
  onCopy,
  getUserName,
  getUser,
}: Props) {
  const searchQuery = airlineSearch.toLowerCase().trim();
  const matchedAlliances = searchQuery
    ? new Set(
        programOptions
          .filter(
            (o) =>
              o.alliance !== "none" &&
              o.airlines.some((a) =>
                a.name.toLowerCase().includes(searchQuery),
              ),
          )
          .map((o) => o.alliance),
      )
    : null;

  return (
    <div className="vault-section">
      <div className="vault-section-header">
        <h3>
          <BiCreditCard /> Loyalty Programs
        </h3>
        <div className="vault-airline-search">
          <BiSearch />
          <input
            type="text"
            placeholder="Search airline..."
            value={airlineSearch}
            onChange={(e) => onAirlineSearchChange(e.target.value)}
          />
        </div>
        <button className="btn-icon" onClick={onAddProg} title="Add program">
          <BiPlus />
        </button>
      </div>
      {matchedAlliances && matchedAlliances.size > 0 && (
        <div className="vault-search-hints">
          {[...matchedAlliances].map((al) => {
            const matched = programOptions
              .filter(
                (o) =>
                  o.alliance === al &&
                  o.airlines.some((a) =>
                    a.name.toLowerCase().includes(searchQuery),
                  ),
              )
              .flatMap((o) =>
                o.airlines.filter((a) =>
                  a.name.toLowerCase().includes(searchQuery),
                ),
              );
            return (
              <div key={al} className="vault-search-hint">
                <span className={`alliance-badge alliance-${al}`}>
                  {ALLIANCE_LABELS[al]}
                </span>{" "}
                {matched.map((a) => a.name).join(", ")}
              </div>
            );
          })}
        </div>
      )}
      <div className="vault-alliances-row">
        {(["star_alliance", "oneworld", "skyteam"] as const).map((alliance) => {
          const group = programs
            .filter(
              (p) =>
                p.alliance === alliance &&
                (!matchedAlliances || matchedAlliances.has(alliance)),
            )
            .sort((a, b) => {
              const aMe = a.user_id === myUserId && a.is_favorite ? 1 : 0;
              const bMe = b.user_id === myUserId && b.is_favorite ? 1 : 0;
              if (aMe !== bMe) return bMe - aMe;
              if (a.is_favorite !== b.is_favorite)
                return a.is_favorite ? -1 : 1;
              return 0;
            });
          if (group.length === 0) return null;
          const isExpanded = expandedAlliances.has(alliance);
          const usersWithFavorite = new Set(
            group.filter((p) => p.is_favorite).map((p) => p.user_id),
          );
          const collapsed = group.filter(
            (p) => p.is_favorite || !usersWithFavorite.has(p.user_id),
          );
          const canCollapse = collapsed.length < group.length;
          const visible = isExpanded ? group : collapsed;
          const hiddenCount = group.length - collapsed.length;
          return (
            <div key={alliance} className="vault-alliance-group">
              <div className="vault-alliance-header">
                <span className={`alliance-badge alliance-${alliance}`}>
                  {ALLIANCE_LABELS[alliance]}
                </span>
                {canCollapse && (
                  <button
                    className="btn-icon vault-expand-btn"
                    onClick={() =>
                      onExpandedAlliancesChange((prev) => {
                        const next = new Set(prev);
                        if (next.has(alliance)) next.delete(alliance);
                        else next.add(alliance);
                        return next;
                      })
                    }
                    title={
                      isExpanded
                        ? "Show only favorite"
                        : `Show ${hiddenCount} more`
                    }
                  >
                    {isExpanded ? "−" : `+${hiddenCount}`}
                  </button>
                )}
              </div>
              <div className="vault-alliance-cards">
                {visible.map((prog) => {
                  const option = programOptions.find(
                    (o) => o.program_name === prog.program_name,
                  );
                  return (
                    <div
                      key={prog.id}
                      className={`vault-card${prog.is_favorite ? " vault-card-favorite" : ""}`}
                    >
                      <div className="vault-card-header">
                        <div className="vault-card-label">
                          {prog.program_name}
                        </div>
                        <div className="vault-card-actions">
                          <button
                            className={`btn-icon${prog.is_favorite ? " favorite-active" : ""}`}
                            onClick={() => onToggleFavorite(prog.id)}
                            title={
                              prog.is_favorite
                                ? "Remove favorite"
                                : "Set as favorite for this alliance"
                            }
                          >
                            <BiStar />
                          </button>
                          <button
                            className="btn-icon"
                            onClick={() => onEditProg(prog)}
                            title="Edit"
                          >
                            <BiPencil />
                          </button>
                          <button
                            className="btn-icon"
                            onClick={() => onDeleteProg(prog.id)}
                            title="Delete"
                          >
                            <BiTrash />
                          </button>
                        </div>
                      </div>
                      {!selectedUserId && (
                        <div
                          className="vault-card-avatar"
                          title={getUserName(prog.user_id)}
                        >
                          {getUser(prog.user_id)?.picture ? (
                            <img
                              src={getUser(prog.user_id)!.picture!}
                              alt={getUserName(prog.user_id)}
                              referrerPolicy="no-referrer"
                            />
                          ) : (
                            <span>{getUserName(prog.user_id).charAt(0)}</span>
                          )}
                        </div>
                      )}
                      {prog.membership_number_masked && (
                        <div className="vault-masked-row">
                          <span className="vault-masked">
                            {prog.membership_number_masked}
                          </span>
                          {prog.membership_number_decrypted && (
                            <button
                              className="vault-copy-btn"
                              onClick={() =>
                                onCopy(
                                  prog.membership_number_decrypted!,
                                  `prog-${prog.id}`,
                                )
                              }
                              title="Copy number"
                            >
                              {copied === `prog-${prog.id}` ? (
                                <BiCheck />
                              ) : (
                                <BiCopy />
                              )}
                            </button>
                          )}
                        </div>
                      )}
                      {option &&
                        prog.user_id === myUserId &&
                        option.airlines.some((a) => a.flights_count > 0) && (
                          <div className="vault-prog-airlines">
                            {option.airlines
                              .filter((a) => a.flights_count > 0)
                              .map((a) => (
                                <span
                                  key={a.name}
                                  className="vault-prog-airline-tag own"
                                >
                                  {a.name} <small>({a.flights_count})</small>
                                </span>
                              ))}
                          </div>
                        )}
                      {prog.notes_masked && (
                        <div className="vault-notes" title="Has notes">
                          <BiNote />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      {programs.length === 0 && (
        <p className="vault-empty">No loyalty programs yet.</p>
      )}
    </div>
  );
}
