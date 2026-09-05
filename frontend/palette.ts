export const PALETTES = [
  { id: "classic-green", name: "经典绿" },
  { id: "ustc-blue", name: "科大蓝" },
  { id: "quiet-pink", name: "安静粉" },
  { id: "sunrise-red", name: "朝霞红" },
  { id: "summer-wheat", name: "夏麦黄" },
] as const;

export type Palette = (typeof PALETTES)[number]["id"];

export const PALETTE_STORAGE_KEY = "mirrors-index-palette";

function isPalette(value: unknown): value is Palette {
  return PALETTES.some((palette) => palette.id === value);
}

export function initializePalette(): Palette {
  let palette: Palette = "classic-green";
  try {
    const stored = localStorage.getItem(PALETTE_STORAGE_KEY);
    if (isPalette(stored)) palette = stored;
  } catch {
    // Use the default palette when persistent storage is unavailable.
  }
  document.documentElement.dataset.palette = palette;
  return palette;
}

export function currentPalette(): Palette {
  const palette = document.documentElement.dataset.palette;
  return isPalette(palette) ? palette : "classic-green";
}

export function selectPalette(palette: Palette) {
  document.documentElement.dataset.palette = palette;
  try {
    localStorage.setItem(PALETTE_STORAGE_KEY, palette);
  } catch {
    // Keep the in-page selection when persistent storage is unavailable.
  }
}
