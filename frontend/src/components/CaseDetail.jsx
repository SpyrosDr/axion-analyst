import { useState } from "react";
import { updateCaseStatus } from "../api";
import EvidenceSection from "./EvidenceSection";
import ResultsSections from "./ResultsSections";
import Collaborators from "./Collaborators";
import ActivityLog from "./ActivityLog";
import Avatar from "./Avatar";
import { canEditWithRole, canManageWithRole } from "../roles";
import { STATUSES, statusBadgeClass, statusLabel } from "../caseStatus";

function CaseDetail({
  caseData,
  currentUser,
  onEvidenceAdded,
  onCollaboratorsChanged,
  onRunAnalysis,
  onDeleteCase,
  analysisLoading,
  analysisError,
}) {
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusError, setStatusError] = useState(null);

  const hasResults = caseData.risk_assessments.length > 0;
  const isOwner = caseData.owner?.id === currentUser?.id;
  const myRole = caseData.my_role;
  const canEdit = canEditWithRole(myRole);
  const canManage = canManageWithRole(myRole);
  const isClosed = caseData.status === "closed";

  async function handleStatusChange(status) {
    setStatusSaving(true);
    setStatusError(null);
    try {
      await updateCaseStatus(caseData.id, status);
      // Reuses the collaborators-changed handler: refetches the sidebar
      // list and the open case, so the badge and lockout update everywhere.
      await onCollaboratorsChanged();
    } catch (err) {
      setStatusError(err.message);
    } finally {
      setStatusSaving(false);
    }
  }

  return (
    <>
      <section className="card">
        <p className="eyebrow">{caseData.context}</p>
        <h2>Case #{caseData.id}</h2>
        <p className="intro">{caseData.description}</p>
        <div className="case-meta">
          {canManage ? (
            <select
              className={statusBadgeClass(caseData.status) + " status-select"}
              value={caseData.status}
              disabled={statusSaving}
              onChange={(e) => handleStatusChange(e.target.value)}
            >
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {statusLabel(status)}
                </option>
              ))}
            </select>
          ) : (
            <span className={statusBadgeClass(caseData.status)}>
              {statusLabel(caseData.status)}
            </span>
          )}
          <p className="empty-state">
            Created {new Date(caseData.created_at).toLocaleString()}
          </p>
          {caseData.owner && (
            <p className="empty-state owner-line">
              Owner:
              <Avatar user={caseData.owner} size={20} />
              {caseData.owner.display_name || caseData.owner.username}
            </p>
          )}
        </div>
        {statusError && <p className="error-text">{statusError}</p>}

        <Collaborators
          caseId={caseData.id}
          canManage={canManage}
          onChanged={onCollaboratorsChanged}
        />

        <EvidenceSection
          caseId={caseData.id}
          evidenceItems={caseData.evidence_items}
          onAdded={onEvidenceAdded}
          canEdit={canEdit && !isClosed}
        />

        {isClosed && (
          <p className="empty-state closed-notice">
            This case is closed — a manager can reopen it to make changes.
          </p>
        )}

        {canEdit && !isClosed && (
          <button onClick={onRunAnalysis} disabled={analysisLoading}>
            {analysisLoading ? "Running Analysis..." : "Run Analysis"}
          </button>
        )}

        {isOwner && (
          <button type="button" className="btn-danger" onClick={onDeleteCase}>
            Delete Case
          </button>
        )}

        {analysisError && <p className="error-text">{analysisError}</p>}

        <ActivityLog caseId={caseData.id} refreshKey={caseData} />
      </section>

      {hasResults && <ResultsSections caseData={caseData} />}
    </>
  );
}

export default CaseDetail;
