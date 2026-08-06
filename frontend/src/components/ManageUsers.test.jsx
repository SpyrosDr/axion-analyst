/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ManageUsers from "./ManageUsers";
import * as api from "../api";

vi.mock("../api");

const USERS = [
  {
    id: 1,
    username: "alice",
    display_name: "Alice Admin",
    is_admin: true,
    global_role: null,
  },
  {
    id: 2,
    username: "bob",
    display_name: "",
    is_admin: false,
    global_role: "viewer",
  },
];

beforeEach(() => {
  vi.resetAllMocks();
  api.listUsersDetailed.mockResolvedValue(USERS);
});

describe("ManageUsers", () => {
  it("renders every user with their current global role", async () => {
    render(<ManageUsers />);

    expect(await screen.findByText("Alice Admin")).toBeInTheDocument();
    expect(screen.getByText("bob")).toBeInTheDocument();

    const aliceRow = screen.getByText("Alice Admin").closest("li");
    expect(within(aliceRow).getByText("Admin")).toBeInTheDocument();

    const bobRow = screen.getByText("bob").closest("li");
    expect(within(bobRow).getByRole("combobox")).toHaveValue("viewer");
  });

  // Permission-sensitive: an admin's global-access level can't be edited
  // away via this dropdown -- admins always have full access regardless
  // of the stored global_role, so the control must stay disabled for them.
  it("disables the role select for admin users", async () => {
    render(<ManageUsers />);
    await screen.findByText("Alice Admin");

    const aliceRow = screen.getByText("Alice Admin").closest("li");
    expect(within(aliceRow).getByRole("combobox")).toBeDisabled();
  });

  it("leaves the role select enabled for non-admin users", async () => {
    render(<ManageUsers />);
    await screen.findByText("bob");

    const bobRow = screen.getByText("bob").closest("li");
    expect(within(bobRow).getByRole("combobox")).toBeEnabled();
  });

  it("submits a role change for the edited user only and refreshes the list", async () => {
    const user = userEvent.setup();
    api.updateUserRole.mockResolvedValue({});
    render(<ManageUsers />);
    await screen.findByText("bob");

    const bobRow = screen.getByText("bob").closest("li");
    await user.selectOptions(within(bobRow).getByRole("combobox"), "editor");

    await waitFor(() => {
      expect(api.updateUserRole).toHaveBeenCalledWith(2, "editor");
    });
    expect(api.updateUserRole).toHaveBeenCalledTimes(1);
    // Refetches to reflect the server's actual state rather than trusting
    // the optimistic UI value.
    expect(api.listUsersDetailed).toHaveBeenCalledTimes(2);
  });

  it("snaps the select back to the server value if the role change fails", async () => {
    const user = userEvent.setup();
    api.updateUserRole.mockRejectedValue(new Error("not allowed"));
    render(<ManageUsers />);
    await screen.findByText("bob");

    const bobRow = screen.getByText("bob").closest("li");
    await user.selectOptions(within(bobRow).getByRole("combobox"), "manager");

    expect(await screen.findByText("not allowed")).toBeInTheDocument();
    expect(within(bobRow).getByRole("combobox")).toHaveValue("viewer");
  });

  it("creates a user with the entered fields and clears the form", async () => {
    const user = userEvent.setup();
    api.createUser.mockResolvedValue({ username: "carol" });
    render(<ManageUsers />);
    await screen.findByText("bob");

    await user.type(screen.getByLabelText("Username"), "carol");
    await user.type(screen.getByLabelText("Password"), "carolpass1");
    await user.click(screen.getByLabelText("Admin"));
    await user.click(screen.getByRole("button", { name: /create user/i }));

    await waitFor(() => {
      expect(api.createUser).toHaveBeenCalledWith({
        username: "carol",
        password: "carolpass1",
        is_admin: true,
      });
    });
    expect(await screen.findByText(/created user 'carol'/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toHaveValue("");
  });

  it("keeps the create button disabled until both fields are filled", async () => {
    const user = userEvent.setup();
    render(<ManageUsers />);
    await screen.findByText("bob");

    const createButton = screen.getByRole("button", { name: /create user/i });
    expect(createButton).toBeDisabled();

    await user.type(screen.getByLabelText("Username"), "carol");
    expect(createButton).toBeDisabled();

    await user.type(screen.getByLabelText("Password"), "carolpass1");
    expect(createButton).toBeEnabled();
  });
});
