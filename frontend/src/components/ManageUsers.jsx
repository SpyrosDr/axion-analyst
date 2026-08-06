/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { useEffect, useState } from "react";
import { createUser, listUsersDetailed, updateUserRole } from "../api";
import { GLOBAL_ROLES } from "../roles";
import Avatar from "./Avatar";
import RoleOptions from "./RoleOptions";

function ManageUsers() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [users, setUsers] = useState([]);
  const [usersError, setUsersError] = useState(null);
  const [savingUserId, setSavingUserId] = useState(null);

  async function refreshUsers() {
    try {
      const data = await listUsersDetailed();
      setUsers(data);
      setUsersError(null);
    } catch (err) {
      setUsersError(err.message);
    }
  }

  useEffect(() => {
    refreshUsers();
  }, []);

  async function handleCreate() {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const user = await createUser({ username, password, is_admin: isAdmin });
      setSuccess(`Created user '${user.username}'.`);
      setUsername("");
      setPassword("");
      setIsAdmin(false);
      await refreshUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRoleChange(userId, globalRole) {
    setSavingUserId(userId);
    let changeError = null;
    try {
      await updateUserRole(userId, globalRole);
    } catch (err) {
      changeError = err.message;
    }
    // Refresh either way so a failed change snaps the select back to the
    // server's actual value instead of showing an unsaved one. Apply the
    // failure message *after* the refresh, not before -- refreshUsers()
    // clears usersError on its own success path, which would otherwise
    // wipe out the error we just set before it ever renders.
    await refreshUsers();
    if (changeError) setUsersError(changeError);
    setSavingUserId(null);
  }

  return (
    <>
      <section className="card">
        <h2>Create User</h2>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={isAdmin}
            onChange={(e) => setIsAdmin(e.target.checked)}
          />
          Admin
        </label>
        <button onClick={handleCreate} disabled={loading || !username || !password}>
          {loading ? "Creating..." : "Create User"}
        </button>
        {error && <p className="error-text">{error}</p>}
        {success && <p className="empty-state">{success}</p>}
      </section>

      <section className="card">
        <h2>Existing Users</h2>
        <p className="empty-state">
          Case access controls whether a user can view, edit, or manage
          collaborators on every case in the system. Leave as "None" to rely
          on per-case sharing instead. Admins always have full access.
        </p>

        {users.length === 0 ? (
          <p className="empty-state">No users yet.</p>
        ) : (
          <ul className="user-role-list">
            {users.map((u) => (
              <li key={u.id} className="user-role-row">
                <span className="user-role-identity">
                  <Avatar user={u} size={28} />
                  {u.display_name || u.username}
                  {u.is_admin && <span className="role-badge">Admin</span>}
                </span>
                <select
                  value={u.global_role || "none"}
                  disabled={savingUserId === u.id || u.is_admin}
                  onChange={(e) => handleRoleChange(u.id, e.target.value)}
                >
                  <RoleOptions roles={GLOBAL_ROLES} />
                </select>
              </li>
            ))}
          </ul>
        )}
        {usersError && <p className="error-text">{usersError}</p>}
      </section>
    </>
  );
}

export default ManageUsers;
