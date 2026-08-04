import { useEffect, useState } from "react";
import { listCases, listEntitySearches, runEntitySearch } from "../api";

const ENTITY_TYPES = [
  { value: "", label: "Type (optional)" },
  { value: "person", label: "Person" },
  { value: "company", label: "Company" },
  { value: "other", label: "Other" },
];

function EntitySearchTool({ caseId = null, embedded = false }) {
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState("");
  const [cases, setCases] = useState([]);
  const [linkedCaseId, setLinkedCaseId] = useState(caseId ? String(caseId) : "");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  async function refreshHistory() {
    setHistoryLoading(true);
    try {
      const data = await listEntitySearches(caseId ? { case_id: caseId } : {});
      setHistory(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    refreshHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  useEffect(() => {
    if (embedded) return;
    listCases()
      .then(setCases)
      .catch(() => setCases([]));
  }, [embedded]);

  async function handleSearch() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const targetCaseId = caseId || (linkedCaseId ? Number(linkedCaseId) : null);
      const data = await runEntitySearch({
        query,
        entity_type: entityType || null,
        case_id: targetCaseId,
      });
      setResult(data);
      await refreshHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="section-block">
      {!embedded && <h3>Entity Search</h3>}
      {embedded && <h3>Web Research</h3>}
      <p className="empty-state">
        Search the web for background information on a person, company, or other entity.
      </p>

      <div className="item-editor">
        <input
          placeholder="Entity name"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={entityType} onChange={(e) => setEntityType(e.target.value)}>
          {ENTITY_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        {!embedded && (
          <select
            value={linkedCaseId}
            onChange={(e) => setLinkedCaseId(e.target.value)}
          >
            <option value="">Not linked to a case</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                Case #{c.id} — {c.context}
              </option>
            ))}
          </select>
        )}
      </div>

      <button onClick={handleSearch} disabled={loading || !query.trim()}>
        {loading ? "Searching..." : "Search"}
      </button>

      {error && <p className="error-text">{error}</p>}

      {result && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h4>{result.query}</h4>
          <p>{result.summary}</p>
          {result.sources.length > 0 && (
            <ul>
              {result.sources.map((s, i) => (
                <li key={i}>
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.title}
                  </a>
                  {s.snippet && <p className="empty-state">{s.snippet}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <h4 style={{ marginTop: "1.5rem" }}>History</h4>
      {historyLoading && <p className="empty-state">Loading history...</p>}
      {!historyLoading && history.length === 0 && (
        <p className="empty-state">No searches yet.</p>
      )}
      {!historyLoading && history.length > 0 && (
        <ul className="evidence-list">
          {history.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="btn-ghost"
                onClick={() =>
                  setExpandedId(expandedId === item.id ? null : item.id)
                }
              >
                <strong>{item.query}</strong>
                {item.entity_type && <em> ({item.entity_type})</em>} —{" "}
                {new Date(item.created_at).toLocaleString()}
              </button>
              {expandedId === item.id && (
                <div>
                  <p>{item.summary}</p>
                  {item.sources.length > 0 && (
                    <ul>
                      {item.sources.map((s, i) => (
                        <li key={i}>
                          <a href={s.url} target="_blank" rel="noreferrer">
                            {s.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default EntitySearchTool;
