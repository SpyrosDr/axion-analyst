/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { useState } from "react";
import { createCase } from "../api";
import { CASE_CONTEXTS } from "../constants";

function CaseForm({ onCaseCreated }) {
  const [context, setContext] = useState(CASE_CONTEXTS[0]);
  const [description, setDescription] = useState("");
  const [evidenceItems, setEvidenceItems] = useState([
    { title: "", content: "", type: "" }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function addEvidenceItem() {
    setEvidenceItems([...evidenceItems, { title: "", content: "", type: "" }]);
  }

  function updateEvidence(index, field, value) {
    const updated = [...evidenceItems];
    updated[index][field] = value;
    setEvidenceItems(updated);
  }

  async function handleCreate() {
    setLoading(true);
    setError(null);

    try {
      const evidence_items = evidenceItems
        .map((e) => `${e.title} ${e.content} ${e.type}`.trim())
        .filter((text) => text.length > 0);

      const newCase = await createCase({ context, description, evidence_items });

      setDescription("");
      setEvidenceItems([{ title: "", content: "", type: "" }]);
      onCaseCreated(newCase);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>New Case</h2>

      <label>
        Case context
        <select value={context} onChange={(e) => setContext(e.target.value)}>
          {CASE_CONTEXTS.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>

      <label>
        Case description
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Example: Several invoices were submitted by a new vendor with similar bank details to an employee."
        />
      </label>

      <h3>Evidence Items (optional)</h3>

      {evidenceItems.map((item, index) => (
        <div className="item-editor" key={index}>
          <input
            placeholder="Title"
            value={item.title}
            onChange={(e) => updateEvidence(index, "title", e.target.value)}
          />
          <input
            placeholder="Type (optional)"
            value={item.type}
            onChange={(e) => updateEvidence(index, "type", e.target.value)}
          />
          <textarea
            placeholder="Evidence details"
            value={item.content}
            onChange={(e) => updateEvidence(index, "content", e.target.value)}
          />
        </div>
      ))}

      <button type="button" className="btn-secondary" onClick={addEvidenceItem}>
        + Add Evidence Item
      </button>

      <button onClick={handleCreate} disabled={loading || !description}>
        {loading ? "Creating..." : "Create Case"}
      </button>

      {error && <p className="error-text">{error}</p>}
    </section>
  );
}

export default CaseForm;
