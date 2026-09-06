import { render } from "preact";
import { useEffect, useId, useMemo, useState } from "preact/hooks";
import { initializePalette } from "./palette";
import type { SyncStatus } from "./types";

initializePalette();

type SortKey =
  | "name"
  | "lastSuccess"
  | "exitCode"
  | "prevRun"
  | "nextRun"
  | "upstream"
  | "size"
  | "syncing";
const errors: Record<number, string> = {
  5: "Server reached max connections",
  10: "Error in socket I/O",
  11: "Error in socket I/O",
  12: "Error in rsync protocol data stream",
  23: "Partial transfer due to error",
  24: "Partial transfer due to vanished source files",
  25: "The --max-delete limit stopped deletions",
  30: "Timeout in data send/receive",
  137: "The syncing container was terminated by SIGKILL signal",
  143: "The syncing container was terminated by SIGTERM signal",
  [-2]: "The syncing container timed out and was thus terminated",
};

function usePreferredColorScheme() {
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light",
  );
  useEffect(() => {
    const preference = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setTheme(preference.matches ? "dark" : "light");
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);
  return theme;
}

function dateTime(timestamp: number) {
  if (!Number.isFinite(timestamp) || timestamp <= 0) return "-";
  const date = new Date(timestamp * 1000);
  const part = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${part(date.getMonth() + 1)}-${part(date.getDate())} ${part(date.getHours())}:${part(date.getMinutes())}:${part(date.getSeconds())}`;
}

function fileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes < 0) return "Unknown";
  if (bytes === 0) return "0.00 bytes";
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 8);
  return `${(bytes / 1024 ** exp).toFixed(2)} ${exp === 0 ? "bytes" : `${"KMGTPEZY"[exp - 1]}B`}`;
}

function StatusDetail({
  children,
  comment,
}: {
  children: preact.ComponentChildren;
  comment: string;
}) {
  const [open, setOpen] = useState(false);
  const commentId = useId();
  return (
    <button
      class="status-detail"
      type="button"
      aria-expanded={open}
      aria-describedby={commentId}
      onClick={() => setOpen((current) => !current)}
      onBlur={() => setOpen(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          event.currentTarget.blur();
        }
      }}
    >
      {children}
      <span id={commentId} class="comment" role="tooltip">
        {comment}
      </span>
    </button>
  );
}

function ErrorStatus({ code }: { code: number }) {
  if (code === 0) return <span>✅</span>;
  const label = (
    <>
      {code === 25 ? "🧹" : "❌"} ({code})
    </>
  );
  if (!errors[code]) return <span>{label}</span>;
  return <StatusDetail comment={errors[code]}>{label}</StatusDetail>;
}

function isSyncStatus(value: unknown): value is SyncStatus {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.name === "string" &&
    typeof item.upstream === "string" &&
    typeof item.syncing === "boolean" &&
    [
      "size",
      "exitCode",
      "lastSuccess",
      "updatedAt",
      "prevRun",
      "nextRun",
    ].every(
      (key) => typeof item[key] === "number" && Number.isFinite(item[key]),
    )
  );
}

function StatusTable({ rows }: { rows: SyncStatus[] }) {
  const [sort, setSort] = useState<{ key: SortKey; ascending: boolean } | null>(
    null,
  );
  const sorted = useMemo(() => {
    if (!sort) return rows;
    return [...rows].sort((left, right) => {
      const a = left[sort.key];
      const b = right[sort.key];
      const result =
        typeof a === "string"
          ? a.localeCompare(String(b))
          : Number(a) - Number(b);
      return sort.ascending ? result : -result;
    });
  }, [rows, sort]);
  const headings: Array<[string, SortKey]> = [
    ["Archive name", "name"],
    ["Last success", "lastSuccess"],
    ["Last status", "exitCode"],
    ["Last sync", "prevRun"],
    ["Next sync", "nextRun"],
    ["Upstream", "upstream"],
    ["Size", "size"],
    ["Syncing", "syncing"],
  ];
  return (
    <div class="status-table-scroll">
      <table id="status">
        <thead>
          <tr>
            {headings.map(([label, key]) => (
              <th
                aria-sort={
                  sort?.key === key
                    ? sort.ascending
                      ? "ascending"
                      : "descending"
                    : undefined
                }
              >
                <button
                  class="sort-button"
                  type="button"
                  onClick={() =>
                    setSort((old) => ({
                      key,
                      ascending: old?.key === key ? !old.ascending : true,
                    }))
                  }
                >
                  <span>{label}</span>
                  <span class="sort-indicator" aria-hidden="true">
                    {sort?.key === key ? (sort.ascending ? "▲" : "▼") : "↕"}
                  </span>
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((item) => (
            <tr
              class={`${item.exitCode !== 0 && item.exitCode !== 25 ? "failedSync" : ""} ${item.syncing ? "ongoingSync" : ""}`.trim()}
            >
              <td>{item.name}</td>
              <td>{dateTime(item.lastSuccess)}</td>
              <td class="withComment">
                <ErrorStatus code={item.exitCode} />
              </td>
              <td>{dateTime(item.prevRun)}</td>
              <td>{dateTime(item.nextRun)}</td>
              <td>{item.upstream}</td>
              <td class="withComment">
                <StatusDetail comment={`${item.size} bytes`}>
                  {fileSize(item.size)}
                </StatusDetail>
              </td>
              <td>{item.syncing ? "🔄" : "⏸️ "}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [rows, setRows] = useState<SyncStatus[] | null>(null);
  const [error, setError] = useState(false);
  const theme = usePreferredColorScheme();
  useEffect(() => {
    fetch("/status/json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data: unknown) => {
        if (!Array.isArray(data) || !data.every(isSyncStatus))
          throw new Error("Invalid status response");
        setRows(data);
      })
      .catch((reason) => {
        console.error("Fetch error:", reason);
        setError(true);
      });
  }, []);
  const panels = [1, 4, 16, 3, 36, 55, 7, 8];
  return (
    <>
      <div id="nav">
        <a href="#sync">Sync Status</a>
        <a href="#server">Server Status</a>
        <a href="/">Mirrors Index</a>
      </div>
      <div id="sync">
        <h2>Sync Status</h2>
        {error ? (
          <p>Load sync status failed</p>
        ) : rows ? (
          <StatusTable rows={rows} />
        ) : (
          <p>Loading sync status…</p>
        )}
      </div>
      <div id="server">
        <h2>Server Status</h2>
        <div class="monitor-grid">
          {panels.map((id, index) => (
            <iframe
              src={`https://monitor.ustclug.org/d-solo/000000001/mirrors?theme=${theme}&panelId=${id}`}
              height={index >= 6 ? "400" : "300"}
              frameborder="0"
              loading="lazy"
              title={`Mirrors server status panel ${id}`}
            ></iframe>
          ))}
        </div>
      </div>
    </>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("Root element is missing");
root.replaceChildren();
render(<App />, root);
