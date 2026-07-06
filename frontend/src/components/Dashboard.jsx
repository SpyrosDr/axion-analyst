import { useEffect, useState } from "react";
import { listCases } from "../api";
import { riskBadgeClass } from "../riskLevel";
import { statusBadgeClass, statusLabel } from "../caseStatus";

function Dashboard({ onOpenCase, onFilterStatus }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listCases()
      .then(setCases)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="card">
        <p>Loading...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card">
        <p className="error-text">{error}</p>
      </section>
    );
  }

  const counts = { low: 0, medium: 0, high: 0 };
  let awaiting = 0;
  const statusCounts = { open: 0, in_review: 0, closed: 0 };
  for (const c of cases) {
    if (c.latest_risk_level && counts[c.latest_risk_level] !== undefined) {
      counts[c.latest_risk_level] += 1;
    } else {
      awaiting += 1;
    }
    if (statusCounts[c.status] !== undefined) {
      statusCounts[c.status] += 1;
    }
  }

  const recent = [...cases]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  return (
    <>
      <section className="card">
        <h2>Dashboard</h2>
        <p className="intro">Overview across all your cases.</p>

        <div className="stat-grid">
          <button
            type="button"
            className="stat-card stat-card-clickable"
            onClick={() => onFilterStatus("all")}
          >
            <span className="stat-value">{cases.length}</span>
            <span className="empty-state">Total cases</span>
          </button>
          <div className="stat-card">
            <span className="stat-value">{awaiting}</span>
            <span className="empty-state">Awaiting analysis</span>
          </div>
          <div className="stat-card">
            <span className={"stat-value risk-high"}>{counts.high}</span>
            <span className="empty-state">High risk</span>
          </div>
          <div className="stat-card">
            <span className={"stat-value risk-medium"}>{counts.medium}</span>
            <span className="empty-state">Medium risk</span>
          </div>
          <div className="stat-card">
            <span className={"stat-value risk-low"}>{counts.low}</span>
            <span className="empty-state">Low risk</span>
          </div>
        </div>

        <div className="stat-grid">
          <button
            type="button"
            className="stat-card stat-card-clickable"
            onClick={() => onFilterStatus("open")}
          >
            <span className="stat-value">{statusCounts.open}</span>
            <span className="empty-state">Open</span>
          </button>
          <button
            type="button"
            className="stat-card stat-card-clickable"
            onClick={() => onFilterStatus("in_review")}
          >
            <span className="stat-value">{statusCounts.in_review}</span>
            <span className="empty-state">In review</span>
          </button>
          <button
            type="button"
            className="stat-card stat-card-clickable"
            onClick={() => onFilterStatus("closed")}
          >
            <span className="stat-value">{statusCounts.closed}</span>
            <span className="empty-state">Closed</span>
          </button>
        </div>
      </section>

      <section className="card">
        <h3>Recent Cases</h3>
        {recent.length === 0 ? (
          <p className="empty-state">No cases yet.</p>
        ) : (
          <ul className="case-list">
            {recent.map((c) => (
              <li
                className="case-list-item"
                key={c.id}
                onClick={() => onOpenCase(c.id)}
              >
                <h4>{c.context}</h4>
                <p>
                  {c.description.slice(0, 140)}
                  {c.description.length > 140 ? "..." : ""}
                </p>
                <div className="case-meta">
                  <p className="empty-state">
                    {new Date(c.created_at).toLocaleString()}
                  </p>
                  <span className={statusBadgeClass(c.status)}>
                    {statusLabel(c.status)}
                  </span>
                  {c.latest_risk_level && (
                    <span className={riskBadgeClass(c.latest_risk_level)}>
                      {c.latest_risk_level} risk
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

export default Dashboard;
