/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Separate from vite.config.js (rather than merging via `test:` there) so
// the dev/build config stays free of test-only concerns -- vitest picks up
// this file automatically because it's named vitest.config.js.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.js"],
    globals: false,
  },
});
