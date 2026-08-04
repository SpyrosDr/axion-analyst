/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { roleLabel } from "../roles";

function RoleOptions({ roles }) {
  return roles.map((role) => (
    <option key={role} value={role}>
      {roleLabel(role)}
    </option>
  ));
}

export default RoleOptions;
