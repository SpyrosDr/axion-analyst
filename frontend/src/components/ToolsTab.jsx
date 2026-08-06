/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { useState } from "react";
import EntitySearchTool from "./EntitySearchTool";

const TOOLS = [{ id: "entity-search", label: "Entity Search" }];

function ToolsTab() {
  const [selectedTool, setSelectedTool] = useState(TOOLS[0].id);

  return (
    <div className="cases-layout">
      <aside className="sidebar">
        <section className="card">
          <div className="sidebar-header">
            <h2>Tools</h2>
          </div>
          <ul className="evidence-list">
            {TOOLS.map((tool) => (
              <li key={tool.id}>
                <button
                  type="button"
                  className={
                    "btn-ghost" + (selectedTool === tool.id ? " active" : "")
                  }
                  onClick={() => setSelectedTool(tool.id)}
                >
                  {tool.label}
                </button>
              </li>
            ))}
          </ul>
        </section>
      </aside>

      <div className="main-panel">
        <section className="card">
          {selectedTool === "entity-search" && <EntitySearchTool />}
        </section>
      </div>
    </div>
  );
}

export default ToolsTab;
