import { useEffect, useState } from "react";
import { deleteCase, getCase, listCases, runAnalysis } from "../api";
import CaseForm from "./CaseForm";
import CaseList from "./CaseList";
import CaseDetail from "./CaseDetail";

function CasesTab({ currentUser, initialCaseId, initialStatusFilter }) {
  const [cases, setCases] = useState([]);
  const [casesLoading, setCasesLoading] = useState(true);
  const [casesError, setCasesError] = useState(null);

  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState(initialStatusFilter || "all");
  const [search, setSearch] = useState("");

  async function refreshCases() {
    setCasesLoading(true);
    setCasesError(null);
    try {
      const data = await listCases();
      setCases(data);
    } catch (err) {
      setCasesError(err.message);
    } finally {
      setCasesLoading(false);
    }
  }

  async function selectCase(id) {
    setSelectedCaseId(id);
    setDetailLoading(true);
    setDetailError(null);
    setAnalysisError(null);
    try {
      const data = await getCase(id);
      setSelectedCase(data);
    } catch (err) {
      // Don't keep showing a stale case we can no longer load (e.g. access
      // was just revoked) -- clear it alongside the error message.
      setSelectedCase(null);
      setDetailError(err.message);
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    refreshCases();
  }, []);

  useEffect(() => {
    if (initialCaseId) {
      selectCase(initialCaseId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCaseId]);

  useEffect(() => {
    if (initialStatusFilter) {
      setStatusFilter(initialStatusFilter);
    }
  }, [initialStatusFilter]);

  async function handleCaseCreated(newCase) {
    setShowForm(false);
    await refreshCases();
    await selectCase(newCase.id);
  }

  async function handleEvidenceAdded() {
    await selectCase(selectedCaseId);
  }

  async function handleCollaboratorsChanged() {
    // Roles may have changed for the current user too (e.g. self-demotion),
    // so refetch both the sidebar list and the open case's my_role.
    await refreshCases();
    await selectCase(selectedCaseId);
  }

  async function handleRunAnalysis() {
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      await runAnalysis(selectedCaseId);
      const data = await getCase(selectedCaseId);
      setSelectedCase(data);
    } catch (err) {
      setAnalysisError(err.message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleDeleteCase() {
    if (!window.confirm("Delete this case and all its evidence, analysis, and reports? This cannot be undone.")) {
      return;
    }
    try {
      await deleteCase(selectedCaseId);
      setSelectedCaseId(null);
      setSelectedCase(null);
      await refreshCases();
    } catch (err) {
      setDetailError(err.message);
    }
  }

  return (
    <div className="cases-layout">
      <aside className="sidebar">
        <section className="card">
          <div className="sidebar-header">
            <h2>Cases</h2>
            <button
              type="button"
              className="btn-secondary"
              style={{ marginTop: 0 }}
              onClick={() => setShowForm((v) => !v)}
            >
              {showForm ? "Cancel" : "+ New Case"}
            </button>
          </div>

          <CaseList
            cases={cases}
            selectedCaseId={selectedCaseId}
            onSelect={selectCase}
            loading={casesLoading}
            error={casesError}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
            search={search}
            onSearchChange={setSearch}
          />
        </section>

        {showForm && <CaseForm onCaseCreated={handleCaseCreated} />}
      </aside>

      <div className="main-panel">
        {detailLoading && (
          <section className="card">
            <p>Loading case...</p>
          </section>
        )}

        {detailError && (
          <section className="card">
            <p className="error-text">{detailError}</p>
          </section>
        )}

        {!detailLoading && !detailError && !selectedCase && (
          <section className="card">
            <p className="empty-state">
              Select a case from the list, or create a new one to get started.
            </p>
          </section>
        )}

        {!detailLoading && selectedCase && (
          <CaseDetail
            caseData={selectedCase}
            currentUser={currentUser}
            onEvidenceAdded={handleEvidenceAdded}
            onCollaboratorsChanged={handleCollaboratorsChanged}
            onRunAnalysis={handleRunAnalysis}
            onDeleteCase={handleDeleteCase}
            analysisLoading={analysisLoading}
            analysisError={analysisError}
          />
        )}
      </div>
    </div>
  );
}

export default CasesTab;
