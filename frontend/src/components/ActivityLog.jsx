/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { useEffect, useState } from "react";
import { listActivity } from "../api";
import Avatar from "./Avatar";

function ActivityLog({ caseId, refreshKey }) {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    listActivity(caseId)
      .then(setEntries)
      .catch((err) => setError(err.message));
    // refreshKey is the caseData object: every mutation refetches the case,
    // so its new identity retriggers this fetch automatically.
  }, [caseId, refreshKey]);

  return (
    <div className="section-block">
      <h3>Activity</h3>

      {entries.length === 0 ? (
        <p className="empty-state">No activity recorded yet.</p>
      ) : (
        <ul className="activity-list">
          {entries.map((entry, index) => (
            <li key={index} className="activity-item">
              {entry.actor ? (
                <Avatar user={entry.actor} size={22} />
              ) : (
                <span className="avatar avatar-initials activity-unknown-actor">?</span>
              )}
              <span className="activity-text">
                <strong>
                  {entry.actor
                    ? entry.actor.display_name || entry.actor.username
                    : "Unknown user"}
                </strong>{" "}
                {entry.detail || entry.action}
              </span>
              <span className="activity-time">
                {new Date(entry.created_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default ActivityLog;
