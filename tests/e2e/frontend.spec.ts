import { expect, test } from "@playwright/test";

test("repository search treats regex metacharacters as literal text", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator("#search").fill("ALP");
  await expect(page.locator("#filelist .filename a")).toHaveText(["alpha"]);
  await page.locator("#search").fill("[");
  await expect(page.locator("#filelist .filename a")).toHaveCount(0);
});

test("palette picker ignores an unknown stored palette", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("mirrors-index-palette", "unknown");
  });
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute(
    "data-palette",
    "classic-green",
  );
  await expect(page.getByRole("button", { name: "经典绿" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("repository and status tooltips work on touch screens", async ({
  browser,
}) => {
  const context = await browser.newContext({
    hasTouch: true,
    viewport: { width: 390, height: 844 },
  });
  const touchPage = await context.newPage();

  await touchPage.route("**/static/json/index.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.repositories[0] = {
      ...data.repositories[0],
      name: "packaging-gitea-act-runner",
      desc: "Gitea Actions Runner 的 Debian 和 Ubuntu 软件包",
    };
    await route.fulfill({ response, json: data });
  });
  await touchPage.goto("/");
  const repositoryRow = touchPage.locator(".filelist tbody tr").first();
  const repositoryName = touchPage.getByRole("link", {
    name: "packaging-gitea-act-runner",
  });
  expect(
    await touchPage.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const rowHeightBeforeTooltip = (await repositoryRow.boundingBox())!.height;
  await repositoryName.tap();
  const repositoryTooltip = touchPage.getByRole("tooltip");
  await expect(repositoryTooltip).toBeVisible();
  const [repositoryNameBox, repositoryTooltipBox] = await Promise.all([
    repositoryName.boundingBox(),
    repositoryTooltip.boundingBox(),
  ]);
  expect(repositoryTooltipBox!.x).toBeGreaterThan(
    repositoryNameBox!.x + repositoryNameBox!.width,
  );
  expect((await repositoryRow.boundingBox())!.height).toBe(
    rowHeightBeforeTooltip,
  );
  const pageWidth = await touchPage.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(pageWidth.scrollWidth, JSON.stringify(pageWidth)).toBeLessThanOrEqual(
    pageWidth.innerWidth,
  );
  await touchPage.locator("#filetitle").tap();
  await expect(repositoryTooltip).toBeHidden();

  await touchPage.route("https://monitor.ustclug.org/**", (route) =>
    route.abort(),
  );
  await touchPage.route("**/status/json", (route) =>
    route.fulfill({
      json: [
        {
          name: "alpha",
          upstream: "safe",
          syncing: false,
          size: 2048,
          exitCode: 10,
          lastSuccess: 1,
          updatedAt: 1,
          prevRun: 2,
          nextRun: 3,
        },
      ],
    }),
  );
  await touchPage.goto("/status/");
  const statusDetail = touchPage.locator("#status .status-detail").last();
  await statusDetail.tap();
  const statusTooltip = statusDetail.getByRole("tooltip");
  await expect(statusTooltip).toBeVisible();
  const [statusDetailBox, statusTooltipBox] = await Promise.all([
    statusDetail.boundingBox(),
    statusTooltip.boundingBox(),
  ]);
  expect(statusTooltipBox!.x).toBeGreaterThan(
    statusDetailBox!.x + statusDetailBox!.width,
  );
  expect(statusTooltipBox!.x + statusTooltipBox!.width).toBeLessThanOrEqual(
    390,
  );
  await statusDetail.tap();
  await expect(statusTooltip).toBeHidden();

  await context.close();
});

test("mouse clicks navigate directly on touch-capable devices", async ({
  browser,
}) => {
  const context = await browser.newContext({ hasTouch: true });
  const page = await context.newPage();

  await page.goto("/");
  await page.getByRole("link", { name: "alpha", exact: true }).click();
  await expect(page).toHaveURL(/\/alpha\/$/);

  await context.close();
});

test("invalid index data restores fallback content", async ({ page }) => {
  await page.route("**/static/json/index.json", async (route) => {
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
  await page.route("**/static/json/index.json", async (route) => {
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

test("failed index data request restores fallback content", async ({
  page,
}) => {
  let failRequest: (() => void) | undefined;
  await page.route("**/static/json/index.json", async (route) => {
    await new Promise<void>((resolve) => {
      failRequest = resolve;
    });
    await route.abort();
  });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator("#fallback")).toHaveCount(0);
  expect(failRequest).toBeDefined();
  failRequest?.();
  await expect(page.locator("#root a")).toHaveAttribute(
    "href",
    "/index-nojs.html",
  );
  await expect(page.locator("#filelist")).toHaveCount(0);
});

test("status treats remote markup as text and wraps long upstream URLs", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1608, height: 900 });
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) =>
    route.fulfill({
      json: [
        {
          name: "zeta",
          upstream:
            "<img src=x onerror=alert(1)>/" +
            "very-long-unbroken-upstream-component-".repeat(8),
          syncing: false,
          size: 1024,
          exitCode: 10,
          lastSuccess: 1,
          updatedAt: 1,
          prevRun: 2,
          nextRun: 3,
        },
      ],
    }),
  );
  await page.goto("/status/");
  await expect(page.locator("#status tbody tr")).toHaveCount(1);
  await expect(page.locator("#status tbody img")).toHaveCount(0);
  const longUpstream = page
    .locator("#status tbody tr")
    .first()
    .locator("td")
    .nth(5);
  await expect(longUpstream).toContainText("<img src=x onerror=alert(1)>/");
  expect(
    await longUpstream.evaluate(
      (element) => element.scrollWidth <= element.clientWidth,
    ),
  ).toBe(true);
  expect((await longUpstream.boundingBox())!.height).toBeGreaterThan(40);
  expect(
    await page
      .locator(".status-table-scroll")
      .evaluate((element) => element.scrollWidth === element.clientWidth),
  ).toBe(true);
});

test("status keeps wide data usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) => route.fulfill({ json: [] }));
  await page.goto("/status/");

  const tableScroll = page.locator(".status-table-scroll");
  await expect(tableScroll).toBeVisible();
  expect(
    await tableScroll.evaluate(
      (element) => element.scrollWidth > element.clientWidth,
    ),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("status reports an invalid response", async ({ page }) => {
  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.route("**/status/json", (route) =>
    route.fulfill({ json: [{ name: "incomplete" }] }),
  );
  await page.goto("/status/");
  await expect(page.getByText("Load sync status failed")).toBeVisible();
});
