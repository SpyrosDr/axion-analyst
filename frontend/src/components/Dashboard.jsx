/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { useEffect, useState } from "react";
import { listCases } from "../api";
import { riskBadgeClass } from "../riskLevel";
import { statusBadgeClass, statusLabel } from "../caseStatus";
import RiskPieChart from "./RiskPieChart";

function Dashboard({ onOpenCase, onFilterStatus }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");

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

  const statusCounts = { open: 0, in_review: 0, closed: 0 };
  for (const c of cases) {
    if (statusCounts[c.status] !== undefined) {
      statusCounts[c.status] += 1;
    }
  }

  const visibleCases =
    statusFilter === "all" ? cases : cases.filter((c) => c.status === statusFilter);

  const counts = { low: 0, medium: 0, high: 0, awaiting: 0 };
  for (const c of visibleCases) {
    if (c.latest_risk_level && counts[c.latest_risk_level] !== undefined) {
      counts[c.latest_risk_level] += 1;
    } else if (c.status !== "closed") {
      // A closed case with no risk assessment isn't "awaiting" anything --
      // the investigation is done, so it's excluded rather than counted.
      counts.awaiting += 1;
    }
  }

  const recent = [...visibleCases]
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
            className={
              "stat-card stat-card-clickable" +
              (statusFilter === "all" ? " stat-card-active" : "")
            }
            onClick={() => setStatusFilter("all")}
          >
            <span className="stat-value">{cases.length}</span>
            <span className="empty-state">Total cases</span>
          </button>
          <button
            type="button"
            className={
              "stat-card stat-card-clickable" +
              (statusFilter === "open" ? " stat-card-active" : "")
            }
            onClick={() => setStatusFilter("open")}
          >
            <span className="stat-value">{statusCounts.open}</span>
            <span className="empty-state">Open</span>
          </button>
          <button
            type="button"
            className={
              "stat-card stat-card-clickable" +
              (statusFilter === "in_review" ? " stat-card-active" : "")
            }
            onClick={() => setStatusFilter("in_review")}
          >
            <span className="stat-value">{statusCounts.in_review}</span>
            <span className="empty-state">In review</span>
          </button>
          <button
            type="button"
            className={
              "stat-card stat-card-clickable" +
              (statusFilter === "closed" ? " stat-card-active" : "")
            }
            onClick={() => setStatusFilter("closed")}
          >
            <span className="stat-value">{statusCounts.closed}</span>
            <span className="empty-state">Closed</span>
          </button>
        </div>

        <div className="risk-overview">
          <RiskPieChart counts={counts} total={visibleCases.length} />
          <div className="stat-grid risk-legend-grid">
            <div className="stat-card">
              <span className={"stat-value risk-awaiting"}>{counts.awaiting}</span>
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
        </div>
      </section>

      <section className="card">
        <div className="sidebar-header">
          <h3>Recent Cases</h3>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onFilterStatus(statusFilter)}
          >
            View all in Cases tab &rarr;
          </button>
        </div>
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
