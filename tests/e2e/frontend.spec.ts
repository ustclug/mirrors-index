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
  const alpha = page.getByRole("link", { name: "alpha", exact: true });
  await alpha.hover();
  const repositoryTooltip = page.getByRole("tooltip");
  await expect(repositoryTooltip).toBeVisible();
  await expect(repositoryTooltip).toHaveText("Alpha repository description");
  await expect(repositoryTooltip).toHaveCSS("border-radius", "4px");
  const [nameBox, tooltipBox] = await Promise.all([
    alpha.boundingBox(),
    repositoryTooltip.boundingBox(),
  ]);
  expect(nameBox).not.toBeNull();
  expect(tooltipBox).not.toBeNull();
  expect(tooltipBox!.x).toBeGreaterThan(nameBox!.x + nameBox!.width);
  await alpha.focus();
  await expect(repositoryTooltip).toBeVisible();
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

test("palette picker persists and is shared with the status page", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");

  const picker = page.getByRole("group", { name: "选择配色" });
  const classic = picker.getByRole("button", { name: "经典绿" });
  const blue = picker.getByRole("button", { name: "科大蓝" });
  const pink = picker.getByRole("button", { name: "安静粉" });
  const red = picker.getByRole("button", { name: "朝霞红" });
  const yellow = picker.getByRole("button", { name: "夏麦黄" });
  const rainbow = picker.getByRole("button", { name: "七彩虹" });
  await expect(picker.getByRole("button")).toHaveCount(6);
  await expect(classic).toHaveAttribute("aria-pressed", "true");
  await expect(pink.locator(".palette-swatch")).toHaveCSS(
    "background-color",
    "rgb(242, 201, 213)",
  );
  await expect(red.locator(".palette-swatch")).toHaveCSS(
    "background-color",
    "rgb(180, 62, 68)",
  );
  await expect(yellow.locator(".palette-swatch")).toHaveCSS(
    "background-color",
    "rgb(250, 223, 146)",
  );
  await expect(rainbow.locator(".palette-swatch")).toHaveCSS(
    "background-image",
    /linear-gradient\(124deg/,
  );

  for (const [button, id, color, gradient, textColor] of [
    [
      pink,
      "quiet-pink",
      "rgb(242, 201, 213)",
      "linear-gradient(rgb(242, 201, 213) 0%, rgb(233, 176, 192) 100%)",
      "rgb(66, 40, 50)",
    ],
    [
      red,
      "sunrise-red",
      "rgb(169, 54, 60)",
      "linear-gradient(rgb(200, 91, 97) 0%, rgb(180, 62, 68) 100%)",
      "rgb(241, 241, 241)",
    ],
    [
      yellow,
      "summer-wheat",
      "rgb(250, 223, 146)",
      "linear-gradient(rgb(250, 223, 146) 0%, rgb(242, 198, 93) 100%)",
      "rgb(60, 43, 9)",
    ],
    [
      rainbow,
      "rainbow",
      "rgb(7, 168, 120)",
      /linear-gradient\(124deg, rgb\(255, 36, 0\)/,
      "rgb(241, 241, 241)",
    ],
  ] as const) {
    await button.click();
    await expect(page.locator("html")).toHaveAttribute("data-palette", id);
    await expect(page.locator(".btn").first()).toHaveCSS(
      "background-color",
      color,
    );
    await expect(page.locator("#announcement")).toHaveCSS(
      "background-color",
      color,
    );
    await expect(page.locator("#welcome")).toHaveCSS(
      "background-image",
      gradient,
    );
    await expect(page.locator("#intro")).toHaveCSS("color", textColor);
  }
  await expect(page.locator("#welcome")).toHaveCSS(
    "background-size",
    "1800% 1800%",
  );
  await expect(page.locator("#welcome")).toHaveCSS("animation-name", "rainbow");

  for (const [button, textColor] of [
    [pink, "rgb(66, 40, 50)"],
    [yellow, "rgb(60, 43, 9)"],
  ] as const) {
    await button.click();
    await expect(page.locator(".btn").first()).toHaveCSS("color", textColor);
    await expect(page.locator("#announcement a")).toHaveCSS("color", textColor);
  }

  await page.emulateMedia({ colorScheme: "dark" });
  for (const [button, buttonColor, gradient] of [
    [
      pink,
      "rgb(207, 130, 153)",
      "linear-gradient(rgb(192, 107, 134) 0%, rgb(157, 74, 99) 100%)",
    ],
    [
      yellow,
      "rgb(223, 189, 100)",
      "linear-gradient(rgb(228, 176, 53) 0%, rgb(169, 125, 30) 100%)",
    ],
  ] as const) {
    await button.click();
    await expect(page.locator(".btn").first()).toHaveCSS(
      "background-color",
      buttonColor,
    );
    await expect(page.locator("#welcome")).toHaveCSS(
      "background-image",
      gradient,
    );
  }
  await page.emulateMedia({ colorScheme: "light" });

  await blue.hover();
  await expect(blue.getByRole("tooltip")).toBeVisible();
  await expect(blue.getByRole("tooltip")).toHaveText("科大蓝");
  await expect(blue.getByRole("tooltip")).toHaveCSS("border-radius", "4px");

  await blue.click();
  await expect(blue).toHaveAttribute("aria-pressed", "true");
  await expect(classic).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator("html")).toHaveAttribute(
    "data-palette",
    "ustc-blue",
  );
  expect(
    await page.evaluate(() => localStorage.getItem("mirrors-index-palette")),
  ).toBe("ustc-blue");
  await expect(page.locator("#welcome")).toHaveCSS(
    "background-image",
    "linear-gradient(rgb(36, 113, 173) 0%, rgb(0, 77, 148) 100%)",
  );
  await expect(page.locator(".btn").first()).toHaveCSS(
    "background-color",
    "rgb(0, 77, 148)",
  );

  await page.reload();
  await expect(blue).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("html")).toHaveAttribute(
    "data-palette",
    "ustc-blue",
  );

  await page.route("https://monitor.ustclug.org/**", (route) => route.abort());
  await page.goto("/status/");
  await expect(page.locator("html")).toHaveAttribute(
    "data-palette",
    "ustc-blue",
  );
  await expect(page.locator("#nav")).toHaveCSS(
    "background-image",
    "linear-gradient(rgb(36, 113, 173) 0%, rgb(0, 77, 148) 100%)",
  );

  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(24, 26, 27)",
  );
  await expect(page.locator("#nav")).toHaveCSS(
    "background-image",
    "linear-gradient(rgb(37, 101, 143) 0%, rgb(24, 79, 117) 100%)",
  );
});

test("palette picker falls back from invalid storage and fits narrow screens", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("mirrors-index-palette", "unknown");
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute(
    "data-palette",
    "classic-green",
  );
  await expect(page.getByRole("button", { name: "经典绿" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
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
  await expect(repositoryName).toHaveAttribute(
    "href",
    "packaging-gitea-act-runner/",
  );
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

test("failed application script restores fallback content", async ({
  page,
}) => {
  await page.route("**/static/js/index-*.js", (route) => route.abort());
  await page.goto("/");
  await expect(page.locator("#fallback")).toBeVisible();
  await expect(page.locator("#fallback a")).toHaveAttribute(
    "href",
    "/index-nojs.html",
  );
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
  await page.setViewportSize({ width: 1608, height: 900 });
  await page.emulateMedia({ colorScheme: "dark" });
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
  await expect(page.locator("body")).toHaveCSS("font-family", /Open Sans/);
  await expect(page.locator("iframe").first()).toHaveAttribute(
    "src",
    /theme=dark/,
  );
  await expect(page.getByText("此页面需要 JavaScript")).toHaveCount(0);
  await expect(page.locator("#status tbody tr")).toHaveCount(2);
  await expect(page.locator("#status tbody img")).toHaveCount(0);
  const longUpstream = page
    .locator("#status tbody tr")
    .first()
    .locator("td")
    .nth(5);
  await expect(longUpstream).toHaveCSS("white-space", "normal");
  expect(
    await longUpstream.evaluate(
      (element) => element.scrollWidth <= element.clientWidth,
    ),
  ).toBe(true);
  expect((await longUpstream.boundingBox())!.height).toBeGreaterThan(40);
  await expect(page.locator("#status tbody tr").first()).toHaveClass(
    /failedSync/,
  );
  await expect(page.locator("#sync")).toHaveCSS("width", "1568px");
  await expect(page.locator(".status-table-scroll")).toHaveCSS(
    "overflow-y",
    "hidden",
  );
  expect(
    await page
      .locator(".status-table-scroll")
      .evaluate((element) => element.scrollWidth === element.clientWidth),
  ).toBe(true);
  const detail = page.locator("#status .status-detail").last();
  const comment = detail.locator(".comment");
  await detail.hover();
  await expect(comment).toBeVisible();
  const detailBox = await detail.boundingBox();
  const commentBox = await comment.boundingBox();
  expect(detailBox).not.toBeNull();
  expect(commentBox).not.toBeNull();
  expect(
    Math.abs(
      commentBox!.x +
        commentBox!.width / 2 -
        (detailBox!.x + detailBox!.width / 2),
    ),
  ).toBeLessThan(1);
  expect(commentBox!.y + commentBox!.height).toBeLessThan(detailBox!.y);
  const archiveHeader = page.getByRole("columnheader", {
    name: "Archive name",
  });
  const archiveSort = page.getByRole("button", { name: "Archive name" });
  await archiveSort.focus();
  await page.keyboard.press("Enter");
  await expect(archiveHeader).toHaveAttribute("aria-sort", "ascending");
  await expect(
    page.locator("#status tbody tr").first().locator("td").first(),
  ).toHaveText("alpha");
  await archiveSort.click();
  await expect(archiveHeader).toHaveAttribute("aria-sort", "descending");
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(253, 255, 253)",
  );
  await expect(page.locator("#nav")).toHaveCSS(
    "background-image",
    "linear-gradient(rgb(64, 189, 151) 0%, rgb(7, 168, 120) 100%)",
  );
  await expect(page.locator("#status th").nth(1)).toHaveCSS(
    "background-color",
    "rgb(220, 239, 233)",
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
  await expect(page.locator(".monitor-grid")).toHaveCSS(
    "grid-template-columns",
    "360px",
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
