/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Testing Library doesn't unmount components between tests on its own --
// without this, a later test can still see DOM nodes a previous test
// rendered, causing spurious multiple-match failures.
afterEach(() => {
  cleanup();
});
