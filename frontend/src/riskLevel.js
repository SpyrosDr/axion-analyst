/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

export function riskBadgeClass(riskLevel) {
  const level = (riskLevel || "").toLowerCase();
  if (level === "high") return "risk-badge risk-high";
  if (level === "medium") return "risk-badge risk-medium";
  return "risk-badge risk-low";
}
