import { useEffect, useState } from "react";
import {
  addCollaborator,
  listCollaborators,
  listUsers,
  removeCollaborator,
  updateCollaboratorRole,
} from "../api";
import { CASE_ROLES, roleLabel } from "../roles";
import Avatar from "./Avatar";
import RoleOptions from "./RoleOptions";

function Collaborators({ caseId, canManage, onChanged }) {
  const [collaborators, setCollaborators] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [selected, setSelected] = useState("");
  const [newRole, setNewRole] = useState("viewer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function refreshCollaborators() {
    try {
      setCollaborators(await listCollaborators(caseId));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refreshCollaborators();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  // The user list only changes via Manage Users, not via anything this
  // component does -- fetch it once instead of after every mutation.
  useEffect(() => {
    listUsers()
      .then(setAllUsers)
      .catch((err) => setError(err.message));
  }, []);

  async function runMutation(mutate) {
    setLoading(true);
    setError(null);
    try {
      await mutate();
      await refreshCollaborators();
      if (onChanged) {
        // Let the parent refetch the case: my_role (and with it the
        // edit/manage UI) may have changed -- including for ourselves.
        await onChanged();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    if (!selected) return;
    await runMutation(async () => {
      await addCollaborator(caseId, selected, newRole);
      setSelected("");
      setNewRole("viewer");
    });
  }

  function handleRoleChange(userId, role) {
    return runMutation(() => updateCollaboratorRole(caseId, userId, role));
  }

  function handleRemove(userId) {
    return runMutation(() => removeCollaborator(caseId, userId));
  }

  const collaboratorIds = new Set(collaborators.map((c) => c.user.id));
  const addableUsers = allUsers.filter((u) => !collaboratorIds.has(u.id));

  return (
    <div className="section-block">
      <h3>Collaborators</h3>

      {collaborators.length === 0 ? (
        <p className="empty-state">No collaborators yet.</p>
      ) : (
        <div className="chip-row">
          {collaborators.map((c) => (
            <span className="chip" key={c.user.id}>
              <Avatar user={c.user} size={18} />
              {c.user.display_name || c.user.username}
              {canManage ? (
                <select
                  className="chip-role-select"
                  value={c.role}
                  disabled={loading}
                  onChange={(e) => handleRoleChange(c.user.id, e.target.value)}
                >
                  <RoleOptions roles={CASE_ROLES} />
                </select>
              ) : (
                <span className="chip-role-label">{roleLabel(c.role)}</span>
              )}
              {canManage && (
                <button
                  type="button"
                  className="chip-remove"
                  onClick={() => handleRemove(c.user.id)}
                  disabled={loading}
                  aria-label={`Remove ${c.user.username}`}
                >
                  &times;
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {canManage && (
        <div className="item-editor item-editor-inline">
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="">Add collaborator...</option>
            {addableUsers.map((u) => (
              <option key={u.id} value={u.username}>
                {u.display_name || u.username}
              </option>
            ))}
          </select>
          <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
            <RoleOptions roles={CASE_ROLES} />
          </select>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleAdd}
            disabled={loading || !selected}
          >
            Add
          </button>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default Collaborators;
