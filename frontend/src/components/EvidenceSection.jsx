/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { useState } from "react";
import { addEvidence } from "../api";

function EvidenceSection({ caseId, evidenceItems, onAdded, canEdit }) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAdd() {
    setLoading(true);
    setError(null);

    try {
      await addEvidence(caseId, { title, type, content });
      setTitle("");
      setType("");
      setContent("");
      onAdded();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="section-block">
      <h3>Evidence</h3>

      {evidenceItems.length === 0 && (
        <p className="empty-state">No evidence recorded yet.</p>
      )}

      {evidenceItems.length > 0 && (
        <ul className="evidence-list">
          {evidenceItems.map((item) => (
            <li key={item.id}>
              {item.title && <strong>{item.title}: </strong>}
              {item.content}
              {item.type && <em> ({item.type})</em>}
            </li>
          ))}
        </ul>
      )}

      {canEdit && (
        <>
          <div className="item-editor">
            <input
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <input
              placeholder="Type (optional)"
              value={type}
              onChange={(e) => setType(e.target.value)}
            />
            <textarea
              placeholder="Evidence details"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>

          <button onClick={handleAdd} disabled={loading || !content}>
            {loading ? "Adding..." : "Add Evidence"}
          </button>
        </>
      )}

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default EvidenceSection;
