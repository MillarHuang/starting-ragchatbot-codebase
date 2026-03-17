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
