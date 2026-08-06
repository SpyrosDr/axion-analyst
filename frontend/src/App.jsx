/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { useEffect, useState } from "react";
import "./App.css";
import Logo from "./components/Logo";
import Login from "./components/Login";
import ManageUsers from "./components/ManageUsers";
import Profile from "./components/Profile";
import Avatar from "./components/Avatar";
import Dashboard from "./components/Dashboard";
import CasesTab from "./components/CasesTab";
import ToolsTab from "./components/ToolsTab";
import { getMe, logout, setUnauthorizedHandler } from "./api";

function App() {
  const [tab, setTab] = useState("dashboard");
  const [initialCaseId, setInitialCaseId] = useState(null);
  const [initialStatusFilter, setInitialStatusFilter] = useState(null);
  // undefined = checking session, null = logged out, object = logged in
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));

    // Session lives in an httpOnly cookie the browser sends automatically
    // -- just ask the backend who (if anyone) it belongs to.
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  function handleLoggedIn() {
    getMe().then(setUser);
  }

  function handleLogout() {
    logout();
    setUser(null);
    setTab("dashboard");
  }

  function handleOpenCase(caseId) {
    setInitialCaseId(caseId);
    setInitialStatusFilter(null);
    setTab("cases");
  }

  function handleFilterStatus(status) {
    setInitialCaseId(null);
    setInitialStatusFilter(status);
    setTab("cases");
  }

  if (user === undefined) {
    return null;
  }

  if (!user) {
    return <Login onLoggedIn={handleLoggedIn} />;
  }

  return (
    <main className="page">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">
            <Logo size={36} />
          </span>
          <div>
            <h1 className="app-title">Axion Analyst</h1>
            <p className="eyebrow">Investigation Workbench</p>
          </div>
        </div>

        <div className="tabs-row">
          <div className="tabs">
            <button
              type="button"
              className={"tab-button" + (tab === "dashboard" ? " active" : "")}
              onClick={() => setTab("dashboard")}
            >
              Dashboard
            </button>
            <button
              type="button"
              className={"tab-button" + (tab === "cases" ? " active" : "")}
              onClick={() => setTab("cases")}
            >
              Cases
            </button>
            <button
              type="button"
              className={"tab-button" + (tab === "tools" ? " active" : "")}
              onClick={() => setTab("tools")}
            >
              Tools
            </button>
            {user.is_admin && (
              <button
                type="button"
                className={"tab-button" + (tab === "users" ? " active" : "")}
                onClick={() => setTab("users")}
              >
                Manage Users
              </button>
            )}
            <button
              type="button"
              className={"tab-button" + (tab === "profile" ? " active" : "")}
              onClick={() => setTab("profile")}
            >
              Profile
            </button>
          </div>

          <div className="account-line">
            <button
              type="button"
              className="account-button"
              onClick={() => setTab("profile")}
            >
              <Avatar user={user} size={26} />
              {user.display_name || user.username}
            </button>
            <button
              type="button"
              className="btn-ghost btn-ghost-muted"
              onClick={handleLogout}
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="app-shell">
        {tab === "dashboard" && (
          <Dashboard onOpenCase={handleOpenCase} onFilterStatus={handleFilterStatus} />
        )}
        {tab === "cases" && (
          <CasesTab
            currentUser={user}
            initialCaseId={initialCaseId}
            initialStatusFilter={initialStatusFilter}
          />
        )}
        {tab === "tools" && <ToolsTab />}
        {tab === "users" && user.is_admin && <ManageUsers />}
      </div>

      {tab === "profile" && (
        <div className="app-shell narrow-shell">
          <Profile user={user} onUpdated={setUser} />
        </div>
      )}
    </main>
  );
}

export default App;
