/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Collaborators from "./Collaborators";
import * as api from "../api";

vi.mock("../api");

const COLLABORATORS = [
  { user: { id: 2, username: "bob", display_name: "" }, role: "viewer" },
];
const ALL_USERS = [
  { id: 2, username: "bob", display_name: "" },
  { id: 3, username: "carol", display_name: "Carol C" },
];

beforeEach(() => {
  vi.resetAllMocks();
  api.listCollaborators.mockResolvedValue(COLLABORATORS);
  api.listUsers.mockResolvedValue(ALL_USERS);
});

describe("Collaborators", () => {
  // Permission-sensitive: a viewer/editor without manage rights must not
  // get an editable role control, a remove button, or the add-collaborator
  // form -- those are the actions "manager" access gates server-side too.
  it("renders read-only role labels and no management controls when canManage is false", async () => {
    render(<Collaborators caseId={1} canManage={false} />);

    expect(await screen.findByText("bob")).toBeInTheDocument();
    expect(screen.getByText("Viewer")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/remove bob/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Add collaborator...")).not.toBeInTheDocument();
  });

  it("renders editable role selects, remove buttons, and the add form when canManage is true", async () => {
    render(<Collaborators caseId={1} canManage={true} />);

    expect(await screen.findByText("bob")).toBeInTheDocument();
    expect(screen.getAllByRole("combobox").length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/remove bob/i)).toBeInTheDocument();
    expect(screen.getByText("Add collaborator...")).toBeInTheDocument();
  });

  it("excludes existing collaborators from the addable-user list", async () => {
    render(<Collaborators caseId={1} canManage={true} />);
    await screen.findByText("bob");

    const addSelect = screen.getByText("Add collaborator...").closest("select");
    expect(within(addSelect).queryByText("bob")).not.toBeInTheDocument();
    expect(within(addSelect).getByText("Carol C")).toBeInTheDocument();
  });

  it("adds a collaborator with the chosen role and notifies the parent", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue();
    api.addCollaborator.mockResolvedValue({});
    render(<Collaborators caseId={1} canManage={true} onChanged={onChanged} />);
    await screen.findByText("bob");

    const addSelect = screen.getByText("Add collaborator...").closest("select");
    await user.selectOptions(addSelect, "carol");
    await user.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() => {
      expect(api.addCollaborator).toHaveBeenCalledWith(1, "carol", "viewer");
    });
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it("removes a collaborator when the remove button is clicked", async () => {
    const user = userEvent.setup();
    api.removeCollaborator.mockResolvedValue({});
    render(<Collaborators caseId={1} canManage={true} />);
    await screen.findByText("bob");

    await user.click(screen.getByLabelText(/remove bob/i));

    await waitFor(() => {
      expect(api.removeCollaborator).toHaveBeenCalledWith(1, 2);
    });
  });

  it("shows an error and does not crash if a mutation fails", async () => {
    const user = userEvent.setup();
    api.removeCollaborator.mockRejectedValue(new Error("cannot remove owner"));
    render(<Collaborators caseId={1} canManage={true} />);
    await screen.findByText("bob");

    await user.click(screen.getByLabelText(/remove bob/i));

    expect(await screen.findByText("cannot remove owner")).toBeInTheDocument();
  });
});
