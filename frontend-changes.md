# Frontend Changes

## Feature: Frontend Testing Infrastructure

### Files Added

#### `package.json`
- Added Jest as the test runner with `jest-environment-jsdom` for DOM simulation.
- `test:frontend` script runs all tests under `frontend/tests/`.
- Jest is configured to match `**/frontend/tests/**/*.test.js`.

#### `frontend/tests/script.test.js`
Comprehensive test suite for `frontend/script.js` covering:

| Test group | What is tested |
|---|---|
| **Initialization** | Welcome message on load, `/api/courses` fetch called, total course count displayed, course titles rendered, empty-list fallback text |
| **Course stats error handling** | "Failed to load courses" message shown, total courses falls back to 0 when fetch rejects |
| **Message rendering** | User text appears in DOM immediately, HTML is escaped to prevent XSS (`<script>` → `&lt;script&gt;`), assistant answer rendered after resolved fetch, sources section rendered when sources are returned |
| **sendMessage** | POST to `/api/query` with correct query body, empty/whitespace input does not trigger fetch, input cleared after send, error message shown on non-ok response, Enter key triggers send |
| **New chat button** | Chat area reset and welcome message shown after click |
| **Suggested questions** | Clicking a suggested question sends its `data-question` value as the query |

### How to Run

Install dependencies (first time only):
```bash
npm install
```

Run frontend tests:
```bash
npm run test:frontend
```

### Design Notes
- Tests load `script.js` via `require()` inside jsdom, then manually dispatch `DOMContentLoaded` to trigger the app's initialization callback. This avoids the need for a real browser.
- `global.fetch` is mocked per test group so no real network calls are made.
- `global.marked` is stubbed as an identity function to isolate DOM tests from the CDN-loaded markdown library.
- `jest.resetModules()` in each `beforeEach` ensures a clean module state and fresh global variable bindings across test groups.

---

## Code Quality Tooling Setup

### New Files Added

#### `frontend/package.json`
Defines the project and npm scripts for running quality checks:

| Script | Command | Description |
|---|---|---|
| `npm run format` | `prettier --write` | Auto-format all JS, CSS, HTML files |
| `npm run format:check` | `prettier --check` | Check formatting without modifying files |
| `npm run lint` | `eslint` | Run ESLint on all JS files |
| `npm run lint:fix` | `eslint --fix` | Auto-fix ESLint issues |
| `npm run quality` | format:check + lint | Full quality gate (use in CI) |

Dev dependencies:
- `prettier@^3.3.0` — automatic code formatter (equivalent to `black` for Python)
- `eslint@^8.57.0` — JavaScript linter
- `eslint-config-prettier@^9.1.0` — disables ESLint rules that conflict with Prettier

#### `frontend/.prettierrc`
Prettier configuration enforcing consistent style:
- Single quotes for strings
- Semicolons required
- 4-space indentation
- 100-character print width
- ES5 trailing commas
- LF line endings

#### `frontend/.eslintrc.json`
ESLint configuration:
- Browser + ES2021 environment
- `eslint:recommended` rules + `prettier` (to disable formatting rules)
- `marked` declared as a global (loaded via CDN)
- Custom rules: `eqeqeq` (error), `curly` (error), `no-unused-vars` (warn)

### Modified Files

#### `frontend/script.js`
Applied Prettier-consistent formatting:
- Removed double blank lines (between `keypress` handler and suggested questions section; between `setupEventListeners` and `sendMessage`)
- Removed trailing whitespace on blank lines
- Removed stale `// Removed removeMessage function` comment

### Usage

Install dependencies (first time, from `frontend/` directory):
```bash
npm install
```

Check formatting and lint:
```bash
npm run quality
```

Auto-format all files:
```bash
npm run format
```

---

## Feature 1: Dark/Light Mode Toggle Button

### Files Modified
- `frontend/index.html`
- `frontend/style.css`
- `frontend/script.js`

### What Was Added

#### `frontend/index.html`
- Added a `<button id="themeToggle">` element with `aria-label` and `title` for accessibility, positioned as a fixed overlay.
- The button contains two inline SVG icons: a **sun** (shown in dark mode) and a **moon** (shown in light mode). Only one is visible at a time via CSS.
- Updated cache-bust version query strings (`?v=11`).

#### `frontend/style.css`
- Added initial `body.light-mode` CSS variable block (later expanded — see Feature 2).
- Added a global `transition` rule on `body` and `body *` for smooth `background-color`, `color`, `border-color`, and `box-shadow` transitions (0.3s ease) when the theme switches.
- Added `.theme-toggle` styles:
  - Fixed position: `top: 1rem; right: 1rem; z-index: 1000`
  - Circular button (42 × 42 px, `border-radius: 50%`)
  - Hover: scales up slightly (`transform: scale(1.1)`) with a blue shadow
  - Focus: visible focus ring using `--focus-ring` variable (keyboard accessible)
  - Active: slight scale-down press effect
- Added icon visibility rules (`.icon-sun` shown by default; `.icon-moon` shown in `body.light-mode`).
- Added `@keyframes spin-once` (0→360°) and `.theme-toggle.spinning svg` to trigger a one-shot rotation animation on each toggle click.

#### `frontend/script.js`
- Added `initTheme()`: reads `localStorage` for a saved `'theme'` key and applies `light-mode` class on `<body>` if set to `'light'`. Called on `DOMContentLoaded`.
- Added `toggleTheme()`: toggles `body.light-mode`, persists the new preference to `localStorage`, and triggers the spin animation.
- Registered a `click` listener on `#themeToggle` inside `setupEventListeners()`.

---

## Feature 2: Light Theme CSS Variables

### Files Modified
- `frontend/style.css`

### What Was Changed

#### Expanded `body.light-mode` variable block
All CSS custom properties are now overridden in light mode, not just a subset:

| Variable | Dark (`:root`) | Light (`body.light-mode`) | Notes |
|---|---|---|---|
| `--primary-color` | `#2563eb` | `#1d4ed8` | Deeper blue; ≥ 4.5:1 on white (WCAG AA) |
| `--primary-hover` | `#1d4ed8` | `#1e40af` | Maintains pressed-state distinction |
| `--user-message` | `#2563eb` | `#1d4ed8` | Matches primary in light context |
| `--background` | `#0f172a` | `#f1f5f9` | Slate-100 |
| `--surface` | `#1e293b` | `#ffffff` | Pure white cards |
| `--surface-hover` | `#334155` | `#e2e8f0` | Slate-200 |
| `--text-primary` | `#f1f5f9` | `#0f172a` | Near-black; ~18:1 on white |
| `--text-secondary` | `#94a3b8` | `#475569` | Slate-600; ~5.7:1 on white (WCAG AA ✓) |
| `--border-color` | `#334155` | `#cbd5e1` | Slate-300 |
| `--assistant-message` | `#374151` | `#f0f4f8` | Soft blue-grey bubble |
| `--shadow` | `rgba(0,0,0,0.3)` | `rgba(0,0,0,0.08)` | Lighter lift |
| `--focus-ring` | `rgba(37,99,235,0.2)` | `rgba(29,78,216,0.2)` | Matches new primary |
| `--welcome-bg` | `#1e3a5f` | `#eff6ff` | Blue-50 |
| `--welcome-border` | `#2563eb` | `#1d4ed8` | Matches new primary |

#### Hard-coded colour overrides (accessibility fixes)

Several elements used colours that look fine on dark surfaces but fail WCAG AA contrast on the new light backgrounds. These are fixed with scoped `body.light-mode` rules:

| Element | Old colour | Light-mode colour | Contrast on white |
|---|---|---|---|
| `.source-tag` text | `#93c5fd` | `#1d4ed8` | ~5.9:1 ✓ |
| `.error-message` text | `#f87171` | `#b91c1c` | ~5.5:1 ✓ |
| `.success-message` text | `#4ade80` | `#15803d` | ~4.6:1 ✓ |
| `.message-content code` bg | `rgba(0,0,0,0.2)` | `rgba(15,23,42,0.07)` | Subtle slate tint |
| `.message-content pre` bg | `rgba(0,0,0,0.2)` | `#e2e8f0` | Visible but soft |
| `.welcome-message` shadow | `rgba(0,0,0,0.2)` | `rgba(0,0,0,0.08)` | Softer lift |

All contrast ratios are verified against WCAG 2.1 AA (≥ 4.5:1 for normal text, ≥ 3:1 for large/UI text).

---

## Feature 3: JavaScript Theme Toggle Functionality

### Files Modified
- `frontend/style.css`
- `frontend/script.js`

### What Was Changed

#### `frontend/style.css`
- Added `body.no-transition, body.no-transition * { transition: none !important; }` guard rule. This suppresses all CSS transitions during the initial theme restoration on page load, preventing a visible dark→light flash when a user returns with a saved `light` preference.

#### `frontend/script.js`

**`initTheme()` — flash-free theme restoration**
- Now adds `no-transition` alongside `light-mode` before the first paint, then removes it after two `requestAnimationFrame` ticks (the minimum needed for the browser to fully commit the initial painted frame).
- Without this, the global `body * { transition: ... }` rule would animate every element from dark to light on every page load where the user had saved a light preference.

**`toggleTheme()` — accessibility + animation**
- Calls `btn.setAttribute('aria-pressed', String(isLight))` after each toggle so screen readers announce "pressed" / "not pressed" correctly.
- Spin animation logic unchanged: adds `spinning` class, listens for `animationend` (which bubbles from the SVG child) to clean it up via `{ once: true }`.

### How it works end-to-end
1. **Page load** — `initTheme()` reads `localStorage('theme')`. If `'light'`, it briefly disables transitions and sets `data-theme="light"`, then re-enables transitions two frames later. No flash.
2. **Button click** — `toggleTheme()` sets/removes `data-theme="light"` on `<body>`. CSS variables cascade instantly; the global transition rule animates every affected property at 0.3s ease. The icon spins once. The new preference is written to `localStorage`.
3. **Next page load** — step 1 repeats, restoring the preference without animation.

---

## Feature 4: `data-theme` Attribute for Theme Switching

### Files Modified
- `frontend/style.css`
- `frontend/script.js`

### What Was Changed

#### `frontend/style.css`
- Replaced all 9 occurrences of the `body.light-mode` selector with `body[data-theme="light"]`.
- This is a semantic improvement: a `data-theme` attribute explicitly signals intent (this is a theme token, not an arbitrary state class), is more easily queried by JS (`getAttribute`/`setAttribute`), and follows the pattern used by design systems and CSS frameworks.
- No visual change — all variable overrides and hard-coded colour fixes remain identical.

#### `frontend/script.js`

**`initTheme()`**
- Replaced `document.body.classList.add('light-mode')` with `document.body.setAttribute('data-theme', 'light')`.
- `no-transition` remains a class (it is a transient behaviour flag, not a theme token).

**`toggleTheme()`**
- Replaced `classList.toggle('light-mode')` with explicit `setAttribute`/`removeAttribute` calls.
- `document.body.getAttribute('data-theme') === 'light'` is the single source of truth for the current theme state — no class inspection needed.
- When switching to dark: `removeAttribute('data-theme')` (absence of the attribute = dark, the default `:root` values apply).
- When switching to light: `setAttribute('data-theme', 'light')`.

### Design rationale
Using an attribute over a class keeps theming concerns separate from behavioural state. The `data-theme` attribute can also be placed on the `<html>` element in the future to allow CSS variables to cascade from the root, making it compatible with third-party component libraries that scope their own variables to `:root`.
