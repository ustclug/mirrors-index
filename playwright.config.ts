import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:8765",
    browserName: "chromium",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? "/usr/bin/chromium",
    },
  },
  webServer: {
    command: "python3 -m http.server 8765 --directory dist",
    url: "http://127.0.0.1:8765/",
    reuseExistingServer: false,
  },
});
