/** Theme state: the data-theme attribute on <html>, persisted per browser. */

const STORAGE_KEY = "pt-theme";

export type Theme = "light" | "dark";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function storedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    // Private mode and blocked site data both throw here; the system preference still works.
    return null;
  }
}

export function resolveTheme(): Theme {
  return storedTheme() ?? "light";
}

export function applyTheme(theme: Theme) {
  // The attribute drives both the palette and Tailwind's dark: variant.
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Not persisting is a lesser failure than not switching.
  }
}

/** Call once before React mounts, so the first paint is already the right theme. */
export function initTheme() {
  document.documentElement.setAttribute("data-theme", resolveTheme());
}
