/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { riskBadgeClass } from "../riskLevel";

function latestById(items) {
  if (!items || items.length === 0) return null;
  return items.reduce((a, b) => (b.id > a.id ? b : a));
}

function groupByType(entities) {
  const groups = {};
  for (const entity of entities) {
    if (!groups[entity.entity_type]) groups[entity.entity_type] = [];
    groups[entity.entity_type].push(entity);
  }
  return groups;
}

function formatTimelineDate(event) {
  if (event.event_date) {
    const parsed = new Date(event.event_date);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    }
  }
  return event.event_date_raw ?? "Undated";
}

function ResultsSections({ caseData }) {
  const timelineEvents = [...caseData.timeline_events].sort(
    (a, b) => a.sequence_order - b.sequence_order
  );
  const riskAssessment = latestById(caseData.risk_assessments);
  const report = latestById(caseData.reports);
  const entityGroups = groupByType(caseData.entities);

  return (
    <>
      <div className="card result section-block">
        <h3>Entities</h3>
        {caseData.entities.length === 0 && (
          <p className="empty-state">No entities extracted.</p>
        )}
        {caseData.entities.length > 0 && (
          <div className="entity-groups">
            {Object.entries(entityGroups).map(([type, items]) => (
              <div className="entity-group" key={type}>
                <h4>{type.replace(/_/g, " ")}</h4>
                <div className="chip-row">
                  {items.map((entity) => (
                    <span className="chip" key={entity.id}>
                      {entity.value}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card result section-block">
        <h3>Timeline</h3>
        {timelineEvents.length === 0 && (
          <p className="empty-state">No timeline events extracted.</p>
        )}
        {timelineEvents.length > 0 && (
          <ul className="timeline">
            {timelineEvents.map((event) => (
              <li key={event.id}>
                <span className="timeline-date">{formatTimelineDate(event)}</span>
                {event.description}
              </li>
            ))}
          </ul>
        )}
      </div>

      {riskAssessment && (
        <div className="card result section-block">
          <h3>Risk Assessment</h3>
          <span className={riskBadgeClass(riskAssessment.risk_level)}>
            {riskAssessment.risk_level} risk
          </span>

          <h4 style={{ marginTop: 20 }}>Risk indicators</h4>
          <ul>
            {riskAssessment.risk_indicators.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
          <h4>Next steps</h4>
          <ul>
            {riskAssessment.next_steps.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {report && (
        <div className="card result section-block" id="printable-report">
          <div className="report-header">
            <h3>Report</h3>
            <button
              type="button"
              className="btn-secondary no-print"
              style={{ marginTop: 0 }}
              onClick={() => window.print()}
            >
              Print / Save as PDF
            </button>
          </div>
          <p className="report-print-title">
            {caseData.context} — Case #{caseData.id}
          </p>
          {Object.entries(report.sections).map(([name, text]) => (
            <div className="report-section" key={name}>
              <h4>{name.replace(/_/g, " ")}</h4>
              <p>{text}</p>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export default ResultsSections;
