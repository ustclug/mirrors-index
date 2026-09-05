import { expect, test } from "@playwright/test";

test("homepage enhances fallback and keeps its interactions", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#filelist .filename a")).toHaveText(["alpha", "beta"]);
  await page.locator("#search").fill("ALP");
  await expect(page.locator("#filelist .filename a")).toHaveText(["alpha"]);
  await page.locator("#search").fill("[");
  await expect(page.locator("#filelist .filename a")).toHaveCount(0);
  await page.locator("#search").fill("");
  await page.locator("body").press("s");
  await expect(page.locator("#search")).toBeFocused();
  await page.getByText("获取安装镜像 >").click();
  await expect(page.locator(".modal select").first()).toHaveValue("0");
  await page.locator(".modaltitle span").last().click();
  await expect(page.locator(".modal")).toHaveCount(0);
});

test("invalid bootstrap keeps fallback content", async ({ page }) => {
  await page.goto("/invalid.html");
  await expect(page.locator("#root li a")).toHaveText(["alpha", "beta"]);
  await expect(page.locator("#filelist")).toHaveCount(0);
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });
  test("repository links remain available", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#root li a")).toHaveText(["alpha", "beta"]);
  });
});

test("status renders, sorts, and treats remote markup as text", async ({ page }) => {
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) => route.fulfill({ json: [
    { name: "zeta", upstream: "<img src=x onerror=alert(1)>", syncing: false, size: 1024, exitCode: 10, lastSuccess: 1, updatedAt: 1, prevRun: 2, nextRun: 3 },
    { name: "alpha", upstream: "safe", syncing: true, size: 2048, exitCode: 0, lastSuccess: 2, updatedAt: 2, prevRun: 3, nextRun: 4 },
  ] }));
  await page.goto("/status/");
  await expect(page.locator("#status tbody tr")).toHaveCount(2);
  await expect(page.locator("#status tbody img")).toHaveCount(0);
  await expect(page.locator("#status tbody tr").first()).toHaveClass(/failedSync/);
  await page.getByRole("columnheader", { name: "Archive name" }).click();
  await expect(page.locator("#status tbody tr").first().locator("td").first()).toHaveText("alpha");
});

test("status reports an invalid response", async ({ page }) => {
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) => route.fulfill({ json: [{ name: "incomplete" }] }));
  await page.goto("/status/");
  await expect(page.getByText("Load sync status failed")).toBeVisible();
});
