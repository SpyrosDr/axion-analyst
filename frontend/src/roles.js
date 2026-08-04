/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

export const GLOBAL_ROLES = ["none", "viewer", "editor", "manager"];
export const CASE_ROLES = ["viewer", "editor", "manager"];

const RANK = { none: 0, viewer: 1, editor: 2, manager: 3 };

export function roleLabel(role) {
  if (!role) return "None";
  return role.charAt(0).toUpperCase() + role.slice(1);
}

export function canEditWithRole(role) {
  return (RANK[role] || 0) >= RANK.editor;
}

export function canManageWithRole(role) {
  return (RANK[role] || 0) >= RANK.manager;
}
