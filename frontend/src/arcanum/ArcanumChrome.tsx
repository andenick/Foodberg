/* =============================================================================
   Arcanum Site Kit (ASK) v1.2 — partials/ReactChrome.tsx  (vendored: Foodberg)
   <ArcanumChrome/> — header + ecosystem switcher + the MANDATED dual-anchor
   footer for React/Vite stacks: Foodberg (and Westchester, coordinated).

   v1.2 (Heterodata rebrand): Heterodata brand; Hub-first switcher rendering
   every site in manifest order (ecosystem.json v2) with detailed indented
   `pages` sub-links and an "Affiliated" tag for externally-owned sites
   (jjmuni). Synced from the shared site kit partial.

   No external/CDN calls (offline rule): import the vendored CSS, and either
   pass the ecosystem object as a prop or import the vendored ecosystem.json.

   Vendoring (Foodberg / Vite)
   ---------------------------
   1) Copy arcanum.css + ecosystem.json into the app's src (or public) tree.
   2) import "./arcanum.css"  (or wherever you vendored it)
   3) Wrap your app:

        import ArcanumChrome from "./ReactChrome";
        import ecosystem from "./ecosystem.json";

        <ArcanumChrome
          siteKey="foodberg"
          accent="#ea580c"
          accentSoft="#3a1e0c"
          nav={[
            { label: "Explore", href: "/explore" },
            { label: "Data",    href: "/data" },
            { label: "Code",    href: "/code" },
            { label: "Methodology", href: "/methodology" },
            { label: "About",   href: "/about" },
          ]}
          dprUrl="/methodology"
          ecosystem={ecosystem}
          activePath={location.pathname}
        >
          <YourRoutes />
        </ArcanumChrome>

   The accent is applied as inline CSS vars on the wrapper, so it themes every
   .ark-* component beneath it with no global CSS edit. Children render between
   <ArcanumHeader/> and <ArcanumFooter/> inside <main id="ark-main">.
   ============================================================================= */
import React from "react";
import { Moon, Sun } from "lucide-react";
import ArkTriad, { type Cdf } from "./ArkTriad";

/* ---- light/dark theme toggle ---------------------------------------------
   Toggles the `.dark` class (Tailwind darkMode:'class') AND the kit
   `data-theme` attribute (drives the --ark-* tokens) on <html>, persists to
   localStorage['ark-theme'], and dispatches `ark:themechange` so charts
   (useArkTheme) re-read. The no-FOUC inline script in index.html applies the
   saved/system theme before first paint; this just keeps React in sync.
   --------------------------------------------------------------------------- */
type ArkTheme = "light" | "dark";

function applyArkTheme(theme: ArkTheme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.setAttribute("data-theme", theme);
}

function readInitialTheme(): ArkTheme {
  if (typeof document === "undefined") return "dark";
  const stored = localStorage.getItem("ark-theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export const ArkThemeToggle: React.FC = () => {
  const [theme, setTheme] = React.useState<ArkTheme>(readInitialTheme);

  // Keep the DOM in sync if the value was set elsewhere (e.g. first mount).
  React.useEffect(() => {
    applyArkTheme(theme);
  }, [theme]);

  const toggle = () => {
    const next: ArkTheme = theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("ark-theme", next); } catch { /* ignore */ }
    applyArkTheme(next);
    document.dispatchEvent(new CustomEvent("ark:themechange", { detail: { theme: next } }));
    setTheme(next);
  };

  return (
    <button
      type="button"
      className="ark-theme-toggle"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
    >
      {theme === "dark" ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
    </button>
  );
};

/* ---- types ---------------------------------------------------------------- */
export interface NavItem {
  label: string;
  href: string;
}
export interface EcoPage {
  label: string;
  path: string;
}
export interface EcoSite {
  key: string;
  title?: string;
  display?: string;
  url: string;
  accent?: string;
  group?: string;
  draft?: boolean;
  roadmap?: boolean;
  /** Externally-owned but part of the ecosystem (e.g. jjmuni). Shows a tag. */
  affiliated?: boolean;
  /** Detailed in-site sub-links rendered indented under the site in the switcher. */
  pages?: EcoPage[];
}
export interface Ecosystem {
  anchors?: {
    hub?: { name: string; url: string };
    author?: { name: string; url: string };
  };
  sites?: EcoSite[];
}
export interface ArcanumChromeProps {
  siteKey: string;
  /** Display name next to the brand (defaults to the ecosystem title for siteKey). */
  siteTitle?: string;
  /** THE per-site knob. Applied as --ark-accent on the wrapper. */
  accent?: string;
  accentSoft?: string;
  nav?: NavItem[];
  dprUrl?: string;
  dprLabel?: string;
  ecosystem?: Ecosystem;
  /** Current path for nav `.active` (e.g. location.pathname). */
  activePath?: string;
  /** This site's `cdf` block — drives the action-footer (triad + repo + cite). */
  cdf?: Cdf | null;
  children?: React.ReactNode;
}

const HUB = { name: "heterodata.org", url: "https://heterodata.org" };
const AUTHOR = { name: "nickanderson.us", url: "https://nickanderson.us" };

const MarkSvg: React.FC = () => (
  <svg viewBox="0 0 32 32" width="100%" height="100%" fill="none" aria-hidden="true"
    xmlns="http://www.w3.org/2000/svg">
    <path d="M16 3 4 27h5l2.4-5h9.2l2.4 5h5L16 3Zm-2.7 14L16 11l2.7 6h-5.4Z" fill="currentColor" />
    <circle cx="16" cy="25.5" r="1.6" fill="currentColor" />
  </svg>
);

/* ---- ecosystem switcher (v1.5) -------------------------------------------
   Hub first, then live sites A-Z, then "In progress" (draft/roadmap), then
   "Affiliated", then the Architect anchor. ONE row per site; `hub_only`
   sites (Files) are skipped — they appear only in the hub's own menu.
   --------------------------------------------------------------------------- */
export const ArcanumSwitcher: React.FC<{
  ecosystem?: Ecosystem;
  siteKey: string;
  siteTitle: string;
}> = ({ ecosystem, siteKey, siteTitle }) => {
  const sites = (ecosystem?.sites ?? []).filter((s) => !(s as { hub_only?: boolean }).hub_only);
  const hub = ecosystem?.anchors?.hub ?? HUB;
  const author = ecosystem?.anchors?.author ?? AUTHOR;
  const live = sites.filter((s) => !s.draft && !s.roadmap && !s.affiliated);
  const wip = sites.filter((s) => (s.draft || s.roadmap) && !s.affiliated);
  const aff = sites.filter((s) => s.affiliated);
  const row = (s: (typeof sites)[number]) => (
    <a
      key={s.key}
      className={"ark-switcher-item" + (s.key === siteKey ? " current" : "")}
      href={s.url}
      role="menuitem"
      aria-current={s.key === siteKey ? "page" : undefined}
      style={{ ["--ark-si-accent" as string]: s.accent ?? "#1565c0" }}
    >
      <span className="ark-dot" aria-hidden="true" />
      <span className="ark-si-name">{s.title ?? s.display}</span>
      {s.draft ? <span className="ark-si-pill">Draft</span> : null}
      {!s.draft && s.roadmap ? <span className="ark-si-pill">Roadmap</span> : null}
      {s.affiliated ? <span className="ark-affiliated">affiliated</span> : null}
      <span className="ark-si-host">{s.display ?? s.url}</span>
    </a>
  );
  return (
    <details className="ark-switcher">
      <summary aria-label="Switch site within the Heterodata ecosystem">
        <span>{siteTitle || "Ecosystem"}</span>
        <span className="ark-caret" aria-hidden="true">&#9662;</span>
      </summary>
      <div className="ark-switcher-menu" role="menu">
        {/* Hub first. */}
        <div className="ark-switcher-group">Hub</div>
        <a className="ark-switcher-item" href={hub.url} role="menuitem">
          <span className="ark-dot" aria-hidden="true" />
          <span className="ark-si-name">{hub.name}</span>
          <span className="ark-si-host">heterodata.org</span>
        </a>

        <div className="ark-switcher-group">Sites</div>
        {live.map(row)}
        {wip.length ? <div className="ark-switcher-group">In progress</div> : null}
        {wip.map(row)}
        {aff.length ? <div className="ark-switcher-group">Affiliated</div> : null}
        {aff.map(row)}

        {/* Architect apex. */}
        <div className="ark-switcher-group">Architect</div>
        <a className="ark-switcher-item" href={author.url} role="menuitem">
          <span className="ark-dot" aria-hidden="true" />
          <span className="ark-si-name">Architect</span>
          <span className="ark-si-host">{author.name}</span>
        </a>
      </div>
    </details>
  );
};

/* ---- header --------------------------------------------------------------- */
export const ArcanumHeader: React.FC<ArcanumChromeProps> = (props) => {
  const { siteKey, ecosystem, nav = [], activePath } = props;
  const current = ecosystem?.sites?.find((s) => s.key === siteKey);
  const siteTitle = props.siteTitle ?? current?.title ?? current?.display ?? "";
  const hubUrl = ecosystem?.anchors?.hub?.url ?? HUB.url;
  const norm = (p: string) => p.replace(/\/$/, "");
  return (
    <header className="ark-header">
      <div className="ark-header-inner">
        <a className="ark-brand" href={hubUrl} aria-label="Heterodata — hub (heterodata.org)">
          <span className="ark-mark" aria-hidden="true"><MarkSvg /></span>
          <span className="ark-brand-text">
            <span className="ark-brand-name">Heterodata</span>
            <span className="ark-brand-sub">An Arcanum Research project</span>
          </span>
        </a>
        {siteTitle ? (
          <a className="ark-site-title" href={current?.url ?? "/"}>{siteTitle}</a>
        ) : null}
        <ArcanumSwitcher ecosystem={ecosystem} siteKey={siteKey} siteTitle={siteTitle} />
        {nav.length ? (
          <nav className="ark-nav" aria-label="Site sections">
            {nav.map((n) => {
              const active = activePath != null && norm(activePath) === norm(n.href);
              return (
                <a key={n.href} className={"ark-nav-a" + (active ? " active" : "")}
                  href={n.href} aria-current={active ? "page" : undefined}>
                  {n.label}
                </a>
              );
            })}
          </nav>
        ) : null}
        {/* v1.5: theme toggle pinned to the far right of the header row
            (it previously sat mid-header between the switcher and nav). */}
        <ArkThemeToggle />
      </div>
    </header>
  );
};

/* ---- cite control: copies cdf.citation to the clipboard (graceful fallback) --- */
const ArkCiteButton: React.FC<{ citation?: string }> = ({ citation }) => {
  const [copied, setCopied] = React.useState(false);
  if (!citation) return null;
  const copy = () => {
    const done = () => { setCopied(true); window.setTimeout(() => setCopied(false), 1800); };
    try {
      if (navigator.clipboard?.writeText) { navigator.clipboard.writeText(citation).then(done).catch(done); }
      else { done(); }
    } catch { done(); }
  };
  return (
    <button type="button" className="ark-action-btn" data-cdf-cite onClick={copy}
      aria-label="Copy the citation for this site" title={citation}>
      {copied ? "Citation copied" : "Cite this site"}
    </button>
  );
};

/* ---- footer v2: action bar (triad + repo + cite) ABOVE the MANDATED dual anchors */
export const ArcanumFooter: React.FC<Pick<ArcanumChromeProps,
  "ecosystem" | "dprUrl" | "dprLabel" | "cdf">> = ({ ecosystem, dprUrl, dprLabel = "Provenance", cdf }) => {
    const hub = ecosystem?.anchors?.hub ?? HUB;
    const author = ecosystem?.anchors?.author ?? AUTHOR;
    const siteRepo = cdf?.site_repo ?? null;
    return (
      <footer className="ark-footer ark-action-footer">
        {cdf ? (
          <div className="ark-action-bar" aria-label="Get the data, the code, and cite this site">
            <ArkTriad cdf={cdf} className="ark-triad-compact"
              track={{ site: "foodberg", endpoint: "/__track" }} />
            <div className="ark-action-tools">
              {siteRepo ? (
                <a className="ark-action-btn" data-cdf-repo href={siteRepo}
                  aria-label="View this website's source code">Website source</a>
              ) : null}
              <ArkCiteButton citation={cdf.citation} />
            </div>
          </div>
        ) : null}
        <div className="ark-footer-inner">
          <span><strong>Heterodata</strong> &mdash; an Arcanum Research project</span>
          <span className="ark-sep" aria-hidden="true">&middot;</span>
          <span>Hub: <a href={hub.url}>{hub.name}</a></span>
          <span className="ark-sep" aria-hidden="true">&middot;</span>
          <span>Architect: <a href={author.url}>{author.name}</a></span>
          <span className="ark-sep" aria-hidden="true">&middot;</span>
          <span className="ark-foot-badges">
            <span className="ark-badge reproducible">Reproducible</span>
            <span className="ark-badge offline">Offline</span>
            <span className="ark-badge real-data">Real data</span>
          </span>
          {dprUrl ? (
            <>
              <span className="ark-sep" aria-hidden="true">&middot;</span>
              <a href={dprUrl}>{dprLabel}</a>
            </>
          ) : null}
        </div>
      </footer>
    );
  };

/* ---- the wrapper ---------------------------------------------------------- */
const ArcanumChrome: React.FC<ArcanumChromeProps> = (props) => {
  const { accent, accentSoft, children } = props;
  const style: React.CSSProperties = {};
  if (accent) (style as Record<string, string>)["--ark-accent"] = accent;
  if (accentSoft) (style as Record<string, string>)["--ark-accent-soft"] = accentSoft;
  return (
    <div className="ark-app" style={style}>
      <a className="ark-skip-link" href="#ark-main">Skip to content</a>
      <ArcanumHeader {...props} />
      <main id="ark-main" className="ark-main">
        <div className="ark-wrap">{children}</div>
      </main>
      <ArcanumFooter ecosystem={props.ecosystem} dprUrl={props.dprUrl} dprLabel={props.dprLabel} cdf={props.cdf} />
    </div>
  );
};

export default ArcanumChrome;
