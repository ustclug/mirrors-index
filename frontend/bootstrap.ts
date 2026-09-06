import type { IndexDataV1 } from "./types";

export async function fetchIndexData(): Promise<IndexDataV1> {
  const response = await fetch("/static/json/index.json", {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(`Unable to load index data: HTTP ${response.status}`);
  const value: unknown = await response.json();
  if (!isIndexData(value)) throw new Error("Unsupported or invalid index data");
  return value;
}

function isIndexData(value: unknown): value is IndexDataV1 {
  if (!value || typeof value !== "object") return false;
  const data = value as Record<string, unknown>;
  return (
    data.schemaVersion === 1 &&
    typeof data.generatedAt === "string" &&
    isArrayOf(
      data.repositories,
      (item) => isObject(item) && strings(item, "name", "updatedAt", "helpUrl"),
    ) &&
    isArrayOf(
      data.reverseProxies,
      (item) => isObject(item) && strings(item, "source", "destination"),
    ) &&
    isArrayOf(
      data.news,
      (item) => isObject(item) && strings(item, "title", "url"),
    ) &&
    isArrayOf(
      data.downloads,
      (item) =>
        isObject(item) &&
        strings(item, "distro", "category") &&
        (item.category === "os" || item.category === "app") &&
        isArrayOf(
          item.urls,
          (url) => isObject(url) && strings(url, "name", "url"),
        ),
    )
  );
}

function isObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object";
}

function strings(value: Record<string, unknown>, ...keys: string[]) {
  return keys.every((key) => typeof value[key] === "string");
}

function isArrayOf(
  value: unknown,
  predicate: (item: unknown) => boolean,
): value is unknown[] {
  return Array.isArray(value) && value.every(predicate);
}
