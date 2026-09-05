import { render } from "preact";
import { useMemo, useState } from "preact/hooks";
import { readBootstrap } from "./bootstrap";
import { DownloadModal, Footer, Header, Sidebar } from "./index-components";
import type { IndexBootstrapV1 } from "./types";

function App({ data }: { data: IndexBootstrapV1 }) {
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<"os" | "app" | null>(null);
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
              {repositories.map((repo) => (
                <tr>
                  <td class="filename">
                    <a href={`${repo.name}/`}>{repo.name}</a>
                  </td>
                  <td class="filetime">{repo.updatedAt}</td>
                  <td class="help">
                    {repo.helpUrl && <a href={repo.helpUrl}>Help</a>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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

try {
  const data = readBootstrap();
  const root = document.getElementById("root");
  if (!root) throw new Error("Root element is missing");
  root.replaceChildren();
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
} catch (error) {
  console.error(
    "Unable to start mirrors index; keeping fallback content",
    error,
  );
}
