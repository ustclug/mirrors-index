import { expect, test } from "@playwright/test";

test("homepage enhances fallback and keeps its interactions", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('link[rel="stylesheet"]')).toHaveAttribute(
    "href",
    /\/static\/css\/style-[A-Z0-9]+\.css$/,
  );
  await expect(page.locator("#filelist .filename a")).toHaveText([
    "alpha",
    "beta",
  ]);
  await expect(page.getByText("无法加载完整页面")).toHaveCount(0);
  await expect
    .poll(() =>
      page
        .locator("#announcement img")
        .evaluate((image: HTMLImageElement) => image.naturalWidth),
    )
    .toBeGreaterThan(0);
  await page.locator("#search").fill("ALP");
  await expect(page.locator("#filelist .filename a")).toHaveText(["alpha"]);
  await page.locator("#search").fill("[");
  await expect(page.locator("#filelist .filename a")).toHaveCount(0);
  await page.locator("#search").fill("");
  await page.locator("body").press("s");
  await expect(page.locator("#search")).toBeFocused();
  const isoTrigger = page.getByRole("button", { name: "获取安装镜像 >" });
  await isoTrigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator(".modalpanel h3")).toHaveText("Test OS");
  await expect(page.locator(".modalfile")).toHaveCount(2);
  await expect(page.locator(".modalfile").first()).not.toContainText(
    "请确认设备支持",
  );
  await expect(page.locator(".modalfile").last()).toContainText(
    "请确认设备支持 arm64",
  );
  await expect(page.getByRole("button", { name: "Test OS" })).toBeFocused();
  await page.getByRole("dialog").press("Escape");
  await expect(page.locator(".modal")).toHaveCount(0);
  await expect(isoTrigger).toBeFocused();

  await page.getByRole("button", { name: "获取开源软件 >" }).click();
  await expect(page.locator(".modalpanel h3")).toHaveText("Test App");
  await expect(page.getByRole("button", { name: "Test App" })).toBeFocused();
  await expect(page.locator(".modalfile")).toHaveCount(1);
  await expect(page.locator(".modalfile")).toContainText("test-app.zip");
});

test("homepage follows the system color scheme", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto("/");
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(24, 26, 27)",
  );
  await page.getByRole("button", { name: "获取安装镜像 >" }).click();
  await expect(page.getByRole("dialog")).toHaveCSS(
    "background-color",
    "rgb(31, 34, 35)",
  );

  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(253, 255, 253)",
  );
  await expect(page.locator("#welcome")).toHaveCSS(
    "background-image",
    "linear-gradient(rgb(64, 189, 151) 0%, rgb(7, 168, 120) 100%)",
  );
  await expect(page.locator(".btn").first()).toHaveCSS(
    "background-color",
    "rgb(7, 168, 120)",
  );
  await expect(page.getByRole("dialog")).toHaveCSS(
    "background-color",
    "rgb(255, 255, 255)",
  );
});

test("invalid index data keeps fallback content", async ({ page }) => {
  await page.route("**/static/index.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.schemaVersion = 2;
    await route.fulfill({ response, json: data });
  });
  await page.goto("/");
  await expect(page.locator("#root a")).toHaveAttribute(
    "href",
    "/index-nojs.html",
  );
  await expect(page.locator("#filelist")).toHaveCount(0);
});

test("download buttons report empty download data", async ({ page }) => {
  await page.route("**/static/index.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.downloads = [];
    await route.fulfill({ response, json: data });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "获取安装镜像 >" }).click();
  await expect(page.locator(".modalbody")).toContainText(
    "暂无可用的安装镜像下载",
  );
  await page.getByRole("button", { name: "关闭" }).click();
  await page.getByRole("button", { name: "获取开源软件 >" }).click();
  await expect(page.locator(".modalbody")).toContainText(
    "暂无可用的开源软件下载",
  );
});

test("failed index data request keeps fallback content", async ({ page }) => {
  await page.route("**/static/index.json", (route) => route.abort());
  await page.goto("/");
  await expect(page.locator("#root a")).toHaveAttribute(
    "href",
    "/index-nojs.html",
  );
  await expect(page.locator("#filelist")).toHaveCount(0);
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });
  test("homepage links to the basic repository list", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    await expect(page.locator("#root")).toContainText("无法加载完整页面");
    await page.locator("#root a").click();
    await expect(page).toHaveURL(/\/index-nojs\.html$/);
    await expect(page.locator("head style")).toHaveCount(1);
    await expect(page.locator('link[rel="stylesheet"]')).toHaveCount(0);
    await expect(page.locator("body")).toHaveCSS(
      "background-color",
      "rgb(24, 26, 27)",
    );
    await expect(page.locator("li a")).toHaveText(["alpha", "beta"]);
    await page.emulateMedia({ colorScheme: "light" });
    await expect(page.locator("body")).toHaveCSS(
      "background-color",
      "rgb(255, 255, 255)",
    );
    await expect(page.locator("a").first()).toHaveCSS(
      "color",
      "rgb(0, 0, 238)",
    );
  });
});

test("status renders, sorts, and treats remote markup as text", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) =>
    route.fulfill({
      json: [
        {
          name: "zeta",
          upstream: "<img src=x onerror=alert(1)>",
          syncing: false,
          size: 1024,
          exitCode: 10,
          lastSuccess: 1,
          updatedAt: 1,
          prevRun: 2,
          nextRun: 3,
        },
        {
          name: "alpha",
          upstream: "safe",
          syncing: true,
          size: 2048,
          exitCode: 0,
          lastSuccess: 2,
          updatedAt: 2,
          prevRun: 3,
          nextRun: 4,
        },
      ],
    }),
  );
  await page.goto("/status/");
  await expect(page.locator('link[rel="stylesheet"]')).toHaveAttribute(
    "href",
    /\/static\/css\/status-[A-Z0-9]+\.css$/,
  );
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(24, 26, 27)",
  );
  await expect(page.locator("iframe").first()).toHaveAttribute(
    "src",
    /theme=dark/,
  );
  await expect(page.getByText("此页面需要 JavaScript")).toHaveCount(0);
  await expect(page.locator("#status tbody tr")).toHaveCount(2);
  await expect(page.locator("#status tbody img")).toHaveCount(0);
  await expect(page.locator("#status tbody tr").first()).toHaveClass(
    /failedSync/,
  );
  await page.getByRole("columnheader", { name: "Archive name" }).click();
  await expect(
    page.locator("#status tbody tr").first().locator("td").first(),
  ).toHaveText("alpha");
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(255, 255, 255)",
  );
  await expect(page.locator("#nav")).toHaveCSS(
    "background-color",
    "rgb(242, 242, 242)",
  );
  await expect(page.locator("#status th").nth(1)).toHaveCSS(
    "background-color",
    "rgb(238, 238, 238)",
  );
  await expect(page.locator(".failedSync")).toHaveCSS(
    "background-color",
    "rgb(255, 244, 227)",
  );
  await expect(page.locator("iframe").first()).toHaveAttribute(
    "src",
    /theme=light/,
  );
});

test("status reports an invalid response", async ({ page }) => {
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) =>
    route.fulfill({ json: [{ name: "incomplete" }] }),
  );
  await page.goto("/status/");
  await expect(page.getByText("Load sync status failed")).toBeVisible();
});
