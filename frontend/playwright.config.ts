import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests", fullyParallel: false, workers: 1, retries: 0,
  timeout: 60000, expect: {timeout: 15000},
  use: {baseURL: "http://127.0.0.1:3000", browserName: "chromium", headless: true},
  reporter: "list",
});
