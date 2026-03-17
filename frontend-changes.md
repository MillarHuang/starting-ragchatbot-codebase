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
