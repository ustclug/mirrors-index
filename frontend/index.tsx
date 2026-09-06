import { render } from "preact";
import { useEffect, useMemo, useState } from "preact/hooks";
import { fetchIndexData } from "./bootstrap";
import { DownloadModal, Footer, Header, Sidebar } from "./index-components";
import { initializePalette } from "./palette";
import type { IndexDataV1 } from "./types";

initializePalette();

function App({ data }: { data: IndexDataV1 }) {
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<"os" | "app" | null>(null);
  const [openRepository, setOpenRepository] = useState<string | null>(null);
  const repositories = useMemo(
    () =>
      data.repositories.filter((repo) =>
        repo.name.toLowerCase().includes(query.trim().toLowerCase()),
      ),
    [data, query],
  );
  const groups = modal
    ? data.downloads.filter((group) => group.category === modal)
    : [];

  useEffect(() => {
    if (!openRepository) return;
    const close = () => setOpenRepository(null);
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("click", close);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", close);
    return () => {
      document.removeEventListener("click", close);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", close);
    };
  }, [openRepository]);

  return (
    <>
      <Header />
      <div id="wrapper">
        <div id="filelist">
          <marquee id="announcement" behavior="alternate">
            <a href="https://servers.ustclug.org/2026/08/mirrorz/">
              <span>MirrorZ 震撼发布</span>{" "}
              <img src="/static/img/new4.gif" alt="New!" />
            </a>
          </marquee>
          <div class="revproxy-section">
            <input id="revproxy" type="checkbox" />
            <h3>
              <label for="revproxy">
                反向代理列表 <span>+</span>
                <span>-</span>
              </label>
            </h3>
            <div class="table-scroll">
              <table>
                <tbody>
                  {data.reverseProxies.map((entry) => (
                    <tr>
                      <td>{entry.source}</td>
                      <td>{entry.destination}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <h3 id="filetitle">文件列表</h3>
            <input
              placeholder="按 S 过滤"
              id="search"
              type="search"
              autocomplete="off"
              value={query}
              onInput={(event) => setQuery(event.currentTarget.value)}
            />
          </div>
          <table class="filelist">
            <thead>
              <tr id="firstline">
                <th id="name">Folder</th>
                <th class="update">Last Update</th>
                <th id="help">Help</th>
              </tr>
            </thead>
            <tbody>
              {repositories.map((repo, index) => (
                <tr
                  onClick={(event) => {
                    if (!repo.desc) return;
                    const link = (event.target as Element).closest("a");
                    if (link && !link.closest(".filename")) return;
                    if (link && openRepository === repo.name) return;
                    event.preventDefault();
                    event.stopPropagation();
                    const name = event.currentTarget.querySelector(
                      ".repo-name",
                    ) as HTMLElement;
                    const availableWidth =
                      window.innerWidth -
                      name.getBoundingClientRect().right -
                      16;
                    name.style.setProperty(
                      "--repo-tooltip-max-width",
                      `${Math.max(1, Math.min(190, availableWidth))}px`,
                    );
                    setOpenRepository((current) =>
                      current === repo.name ? null : repo.name,
                    );
                  }}
                >
                  <td class="filename">
                    <span
                      class={`repo-name ${openRepository === repo.name ? "tooltip-open" : ""}`}
                    >
                      <a
                        href={`${repo.name}/`}
                        aria-describedby={
                          repo.desc ? `repo-description-${index}` : undefined
                        }
                      >
                        {repo.name}
                      </a>
                      {repo.desc && (
                        <span
                          id={`repo-description-${index}`}
                          class="repo-tooltip"
                          role="tooltip"
                        >
                          {repo.desc}
                        </span>
                      )}
                    </span>
                  </td>
                  <td class="filetime">{repo.updatedAt}</td>
                  <td class="help">
                    {repo.helpUrl && <a href={repo.helpUrl}>Help</a>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p class="data-updated-at">数据更新时间：{data.generatedAt}</p>
        </div>
        <Sidebar data={data} open={setModal} />
      </div>
      <Footer />
      {modal && (
        <DownloadModal
          kind={modal}
          groups={groups}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}

async function main() {
  const root = document.getElementById("root");
  if (!root) throw new Error("Root element is missing");
  const fallback = document.getElementById("fallback");
  root.replaceChildren();
  document.documentElement.classList.remove("index-loading");

  let data: IndexDataV1;
  try {
    data = await fetchIndexData();
  } catch (error) {
    if (fallback) {
      root.replaceChildren(fallback);
    }
    throw error;
  }

  render(<App data={data} />, root);
  document.addEventListener("keydown", (event) => {
    const input = document.getElementById("search") as HTMLInputElement | null;
    if (
      event.key.toLowerCase() === "s" &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey &&
      document.activeElement?.tagName !== "INPUT"
    ) {
      input?.scrollIntoView({ block: "center" });
      input?.focus();
      event.preventDefault();
    }
  });
}

main().catch((error) => {
  console.error(
    "Unable to load mirrors index; showing fallback content",
    error,
  );
});
