import { statusBadgeClass, statusLabel, STATUSES } from "../caseStatus";

const FILTERS = ["all", ...STATUSES];

function filterLabel(filter) {
  return filter === "all" ? "All" : statusLabel(filter);
}

function CaseList({
  cases,
  selectedCaseId,
  onSelect,
  loading,
  error,
  statusFilter,
  onStatusFilterChange,
  search,
  onSearchChange,
}) {
  const filtered = cases.filter((c) => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    if (!search.trim()) return true;
    const needle = search.trim().toLowerCase();
    return (
      c.context.toLowerCase().includes(needle) ||
      c.description.toLowerCase().includes(needle)
    );
  });

  return (
    <>
      <div className="case-filter-row">
        {FILTERS.map((filter) => (
          <button
            type="button"
            key={filter}
            className={
              "filter-chip" + (statusFilter === filter ? " active" : "")
            }
            onClick={() => onStatusFilterChange(filter)}
          >
            {filterLabel(filter)}
          </button>
        ))}
      </div>
      <input
        className="case-search-input"
        type="text"
        placeholder="Search cases..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && cases.length === 0 && (
        <p className="empty-state">No cases yet. Create one to get started.</p>
      )}
      {!loading && !error && cases.length > 0 && filtered.length === 0 && (
        <p className="empty-state">No cases match.</p>
      )}

      {!loading && filtered.length > 0 && (
        <ul className="case-list">
          {filtered.map((c) => (
            <li
              key={c.id}
              className={
                "case-list-item" + (c.id === selectedCaseId ? " selected" : "")
              }
              onClick={() => onSelect(c.id)}
            >
              <h4>{c.context}</h4>
              <p>{c.description.slice(0, 140)}{c.description.length > 140 ? "..." : ""}</p>
              <div className="case-meta">
                <p className="empty-state">{new Date(c.created_at).toLocaleString()}</p>
                <span className={statusBadgeClass(c.status)}>
                  {statusLabel(c.status)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default CaseList;
