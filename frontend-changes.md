# Frontend Changes

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
