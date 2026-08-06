/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { useEffect, useRef, useState } from "react";
import {
  attachmentDownloadUrl,
  deleteAttachment,
  listAttachments,
  uploadAttachment,
} from "../api";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function EvidenceAttachments({ caseId, evidenceId, canEdit }) {
  const [attachments, setAttachments] = useState([]);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const fileInputRef = useRef(null);

  async function refresh() {
    try {
      setAttachments(await listAttachments(caseId, evidenceId));
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId, evidenceId]);

  async function handleFileChosen(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // let the same file be picked again later
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await uploadAttachment(caseId, evidenceId, file);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(attachmentId) {
    setDeletingId(attachmentId);
    setError(null);
    try {
      await deleteAttachment(caseId, evidenceId, attachmentId);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  if (attachments.length === 0 && !canEdit) return null;

  return (
    <div className="evidence-attachments">
      {attachments.length > 0 && (
        <ul className="attachment-list">
          {attachments.map((a) => (
            <li key={a.id} className="attachment-row">
              <a
                href={attachmentDownloadUrl(caseId, evidenceId, a.id)}
                target="_blank"
                rel="noreferrer"
              >
                {a.filename}
              </a>
              <span className="attachment-meta">{formatSize(a.size_bytes)}</span>
              {canEdit && (
                <button
                  type="button"
                  className="chip-remove"
                  onClick={() => handleDelete(a.id)}
                  disabled={deletingId === a.id}
                  aria-label={`Remove ${a.filename}`}
                >
                  &times;
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {canEdit && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChosen}
            disabled={uploading}
            aria-label="Attach file"
          />
          {uploading && <span className="empty-state">Uploading...</span>}
        </>
      )}

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default EvidenceAttachments;
