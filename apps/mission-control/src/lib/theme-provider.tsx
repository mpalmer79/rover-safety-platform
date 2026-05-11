"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { DEFAULT_THEME, THEME_NAMES, type ThemeName } from "@/styles/tokens";

interface ThemeContextValue {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  toggle: () => void;
  /** ``true`` once the provider has resolved its initial preference. */
  ready: boolean;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "mc-theme-preference";

function readInitialTheme(): ThemeName {
  if (typeof window === "undefined") return DEFAULT_THEME;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // localStorage might be disabled — fall through to system pref.
  }
  if (typeof window.matchMedia === "function") {
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    return prefersLight ? "light" : "dark";
  }
  return DEFAULT_THEME;
}

function applyThemeClass(theme: ThemeName, withTransition = true): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (withTransition) root.classList.add("theme-transition");
  root.classList.remove(...THEME_NAMES);
  root.classList.add(theme);
  root.dataset.theme = theme;
  if (withTransition) {
    window.setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 240);
  }
}

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Reads the stored / system theme on mount, applies it to the
 * documentElement, and persists every subsequent change. The
 * "theme-transition" class is added briefly during change so colour
 * shifts feel intentional rather than jarring.
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemeName>(DEFAULT_THEME);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const initial = readInitialTheme();
    setThemeState(initial);
    applyThemeClass(initial, false);
    setReady(true);
  }, []);

  const setTheme = useCallback((next: ThemeName) => {
    setThemeState(next);
    applyThemeClass(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* localStorage might be disabled. */
    }
  }, []);

  const toggle = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [setTheme, theme]);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, setTheme, toggle, ready }),
    [theme, setTheme, toggle, ready],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Allow components rendered outside the provider (mostly tests)
    // to still call ``useTheme`` without crashing. They get a no-op
    // setter and the default theme.
    return {
      theme: DEFAULT_THEME,
      setTheme: () => {},
      toggle: () => {},
      ready: false,
    };
  }
  return ctx;
}

/**
 * No-FOUC inline script. Rendered inside ``<head>`` so the
 * documentElement carries the correct theme class before the page
 * paints. The script is deliberately tiny and dependency-free.
 */
export const THEME_BOOTSTRAP_SCRIPT: string = `
  (function () {
    try {
      var stored = window.localStorage.getItem(${JSON.stringify(STORAGE_KEY)});
      var theme = stored === 'light' || stored === 'dark' ? stored : null;
      if (!theme) {
        theme = window.matchMedia &&
          window.matchMedia('(prefers-color-scheme: light)').matches
            ? 'light' : 'dark';
      }
      var html = document.documentElement;
      html.classList.remove('light', 'dark');
      html.classList.add(theme);
      html.dataset.theme = theme;
    } catch (_) {
      document.documentElement.classList.add('dark');
    }
  })();
`;

export const THEME_STORAGE_KEY = STORAGE_KEY;
