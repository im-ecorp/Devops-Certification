# Refactor verification (2026-10-12)

Scope: actual `upstream/backend` and `upstream/client` source under this lab; host Node `v24.18.0`, npm `11.18.0`. The upstream revision is a provenance baseline, not current unmodified code. Old-version snapshots and validation caches were subsequently removed at the user’s request. `.env` and root Compose were not modified.

| From this directory | Result |
| --- | --- |
| `(cd upstream/backend && npm ci --include=dev --no-audit --no-fund && npm test)` | PASS: 8 suites, 12 tests including real HTTP CRUD against in-memory SQLite. |
| `(cd upstream/client && npm ci --include=dev --no-audit --no-fund && npm run lint && npm test && npm run build)` | PASS: lint zero warnings, 3 suites/10 tests, Vite 8.3.4 build 56 modules. |
| `(cd upstream/backend && npm audit --json)` | 22 findings: 19 moderate, 3 high, all in development tooling (`jest`/Istanbul and `nodemon`/Chokidar), not production. npm's suggested `--force` downgrades Jest to 25 or nodemon to 1, so do not use it blindly. |
| `(cd upstream/backend && npm audit --omit=dev --json)` | 0 findings. |
| `(cd upstream/client && npm audit --json && npm audit --omit=dev --json)` | 0 findings for both trees. |

Pre-push review added three initial-load failure/retry regressions: all failed before the fix and passed afterward. The initial GET now checks status and validates the response array, catches failures and offers Retry.

Regression tests first reproduced: MySQL `_FILE` values reaching the driver as Buffers; `MYSQL_HOST_FILE` alone selecting SQLite; removal of absent item duplicating a list element; failed POST passing error JSON into the list; failed DELETE removing an item. The new tests went red for those behaviors before the fixes and green afterward. CSS now imports Bootstrap's published CSS, so Vite build does not emit Sass `@import` warnings from Bootstrap's vendor SCSS. No vendored bundle was changed.

Remaining limitations:

- Backend install reports transitive deprecated `prebuild-install@7.1.3` (SQLite's prebuilt binary fetch) and `glob@10.5.0` (Jest/Istanbul path). It also reports install-script policy notices for `sqlite3`, `@parcel/watcher`, and `unrs-resolver`; client reports `@parcel/watcher`. The lockfile has these two deprecation markers on the backend and none on the client. `prebuild-install` itself emits Node's `fs.R_OK` deprecation warning when run explicitly.
- This host has neither Docker CLI/daemon nor `make`/C++ compiler. The new SQLite prebuilt native binary was installed by `npm ci` (confirmed by 12 passing backend tests); a separate attempt to compile via `node-gyp rebuild` failed with `not found: make`. The Dockerfile's native compilation stage was inspected but **not** image-built or runtime-tested here. The Docker Hub registry manifest digest for `node:24.18.0` was fetched and SHA-256 verified as `5711a0d445a1af54af9589066c646df387d1831a608226f4cd694fc59e745059`; that verifies the tag pin, not a Docker build.
- Parent verification also passed standalone Compose JSON rendering: two services, only loopback 8092, private database network and unchanged `todo-db-data` volume. MySQL integration, container health checks, persistent volume behavior, and browser behavior were not tested without Docker/MySQL/browser. The MySQL driver settings have an isolated boundary test; HTTP smoke test uses SQLite only. The API still lacks input validation and authentication: keep it loopback-only and do not call this production-hardening.
- `uuid@11.1.1` remains the latest 11.x for the existing CommonJS `require('uuid')` code; `uuid@14` is ESM-only and was not substituted. `typescript@6.0.3` is held to the linter peer range (<6.1); latest 7 is incompatible. These are compatibility decisions, not unaddressed deprecation warnings. The obsolete `.eslintrc.cjs` was removed; ESLint 10 uses `eslint.config.js`.

On a Docker-equipped host run `docker compose -f compose.yaml config --quiet` then `docker compose -f compose.yaml build app` to verify the unchanged Compose topology and the new image stages; only the maintained root Compose definition is retained. No deployment was attempted here.
