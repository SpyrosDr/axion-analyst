/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

export const STATUSES = ["open", "in_review", "closed"];

const LABELS = { open: "Open", in_review: "In Review", closed: "Closed" };

export function statusLabel(status) {
  return LABELS[status] || status;
}

export function statusBadgeClass(status) {
  if (status === "closed") return "status-badge status-closed";
  if (status === "in_review") return "status-badge status-in-review";
  return "status-badge status-open";
}
