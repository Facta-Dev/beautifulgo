# BeautifulGo lints

This directory holds the drop-in golangci-lint v2 config for the facta
backend-go stack, plus a proof module that shows every rule firing.

- `lints/.golangci.yml` — the config users copy to their repo root, next to
  go.mod. Requires golangci-lint v2.x (`go install
  github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest` or the
  install script). `default: standard` keeps errcheck, govet, ineffassign,
  staticcheck, and unused; the `enable` list adds contextcheck, depguard,
  errname, errorlint, and noctx; `formatters` enables gofmt.
- `lints/check/` — the "every rule fires" proof. A throwaway Go module
  (`github.com/beautifulgo/check`) with a clean reference slice (domain,
  ports, usecase) that must produce zero findings, and one deliberately
  violating file per rule, each violation on a line ending with a
  `// want <linter>` marker.
- `scripts/check-lints.sh` — runs the proof: `golangci-lint run` over
  `lints/check/` with the config (machine-readable output), failing if a
  marker stays quiet, if anything unmarked reports, if the clean slice
  reports, or if the check directory's table drifts from the config's rule
  names. Exit 1 on failure, 2 if golangci-lint v2, go, or python3 are missing.

## Copying it

1. Copy `lints/.golangci.yml` to your repository root, next to `go.mod`.
2. Substitute the module path once. Internal-package rules must name the real
   module path because depguard's `pkg` patterns prefix-match import paths:

   ```sh
   sed -i '' 's|github.com/<scope>/<app>|github.com/real/module|g' .golangci.yml
   ```

   On the facta `backend-go` template this step is a no-op before
   `scripts/rename.sh` runs: the template's module path is
   `github.com/<scope>/<app>` verbatim. The `files:` globs use `**/internal/...`
   forms, so they match any module without substitution.
3. Run `golangci-lint run`. Stack projects also run `gofmt -l` and
   `go vet ./...` first; thresholds live inline in this one file, so there is
   no separate settings file to keep in sync — the analogue of the lint tables
   other plugins ship beside their config.

The four depguard rules are the architecture law. They keep the same names as
the stack overlay (`skills/go-best-practices/references/backend-go-stack.md`)
and the facta handbook's doc 04: domain-pure, usecase-transport-free,
slice-isolation, platform-no-features.

## What each rule enforces

| Rule | Linter | Fires on | Backs |
| --- | --- | --- | --- |
| gofmt | formatters (gofmt) | files that differ from gofmt output | go-best-practices §3 (run the gates) |
| errcheck | default standard | unchecked error returns | §5 errors and panics |
| govet | default standard | suspicious constructs, printf verbs | §3, §10 |
| ineffassign | default standard | assignments that are never used | §3 |
| staticcheck | default standard | SA/ST findings | §3, §4 |
| unused | default standard | unexported code nothing reaches | §4 types and interfaces |
| contextcheck | enable | a context dropped mid-call-chain, callee starts fresh | §6 context propagation |
| errname | enable | sentinels not named `ErrX`, error types not named `XError` | §5 |
| errorlint | enable | `%s` wrapping an error, type assertion on an error, `==` on errors | §5 |
| noctx | enable | `http.Get`/`NewRequest`/`Client.Get` without a context | §6 |
| depguard: domain-pure | enable, files `**/internal/features/**/domain.go` | allow-list: the standard library ($gostd) plus `internal/shared` only — so domain.go importing net/http, database/sql, pgx, chi, a third-party package, internal/gen, internal/platform, or another slice all fail | §2 architecture contract |
| depguard: usecase-transport-free | enable, files `**/internal/features/**/usecase.go` + `ports.go` | use case or ports files importing net/http, database/sql, pgx, chi, internal/gen, internal/platform | §2 (mechanism names belong to adapters, doc 04) |
| depguard: slice-isolation | enable, files `**/internal/features/**` | any file under a slice importing another slice's package | §2 (slices sealed; composition in cmd/api) |
| depguard: platform-no-features | enable, files `**/internal/platform/**` | platform code importing a feature slice | §2 (platform serves features, never consumes) |

Test files keep errcheck quiet via the config's exclusions, where a checked
failure is the assertion. Silence a deliberate finding with a reason on the
narrowest line (`//nolint:depguard // why`); the skills say to never use it to
sneak a forbidden edge — fix the shape, or fix the rule in review.

## The check directory

`lints/check/` is written like a project the rules would protect:

- `internal/features/widgets/` — the clean reference slice (domain, ports,
  usecase). It must lint with zero findings, proving the drop-in never
  penalizes the six-file shape the skills teach.
- `internal/features/violations/` — one violating file per rule, plus its
  `doc.go` table of rule -> linter -> file that `scripts/check-lints.sh`
  cross-checks against the config.
- `internal/platform/roguehub/`, `internal/shared/kernel.go`,
  `internal/platform/stub/stub.go`, `internal/gen/api/api.go` — stubs the
  violations import.

Two notes for running it locally:

- The module pins `go 1.25` in its `go.mod`. It is a proof, not a stack
  project — the older language version lets every current golangci-lint v2.x
  build (some are built with an earlier Go than 1.27) typecheck the module and
  the stdlib it pulls in.
- `go.sum` is committed so the pgx dependency resolves without network on the
  first CI run.