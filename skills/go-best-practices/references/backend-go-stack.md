# backend-go stack (digest)

Sources: the backend-go template handbook (docs 00-14 of the backend-go
template) and the shipped skeleton (its `.golangci.yml` and `CLAUDE.md`).
Synthesized digest; every rule below is the handbook's, condensed. Read this
FIRST when a repo has `internal/features/` and a `.golangci.yml` — the facta
backend-go stack — before writing or regenerating anything in a slice. "Where
does X live?" is answerable by file kind here, not by grep.

## The one rule

**Dependencies point inward.** Composition root (`cmd/`) -> slices
(`internal/features/<slice>/`) -> ports (`ports.go`) -> domain (`domain.go`).
The outward *call* is fine at runtime; the outward *import* is forbidden in
source. An inner file must never name an outer one. Go package cycles cannot
compile; depguard supplies the file-level edges the package graph cannot see.

## The four depguard rules

These four names are the shared vocabulary between this digest and the
beautifulgo `lints/.golangci.yml` drop-in. SKILL.md section 2 reproduces the
same table; drift between the two is a checklist failure.

| depguard rule | Files governed | Forbidden imports |
|---|---|---|
| `domain-pure` | `**/internal/features/**/domain.go` | everything outside the allow-list: the standard library plus `<app>/internal/shared` only — notably `net/http`, `database/sql`, `github.com/jackc/pgx/v5`, `internal/gen`, `internal/platform`, other slices |
| `usecase-transport-free` | `**/internal/features/**/usecase.go`, `**/internal/features/**/ports.go` | `net/http`, `database/sql`, `github.com/jackc/pgx/v5`, `internal/gen`, `internal/platform` |
| `slice-isolation` | `**/internal/features/**` | any other `internal/features` package |
| `platform-no-features` | `**/internal/platform/**` | `internal/features` |

The shipped config spells internal-package patterns with the absolute
placeholder `github.com/<scope>/<app>/internal/...`: depguard's `pkg` patterns
prefix-match import paths (pattern + every subpackage, `$` exact), so those
rules must carry the real module path. The table above shortens them to the
`/internal/...` tail for readability. Only the config's `files:` globs use
`**/internal/...` forms, and they match any module verbatim; every project
other than the facta template substitutes `github.com/<scope>/<app>` once (a
one-line `sed`, see `lints/README.md`).

## The six-file slice

```
internal/features/widgets/
├── domain.go    pure types + rules + errors (stdlib + shared only)
├── ports.go     the interfaces this feature needs (consumer-defined)
├── usecase.go   orchestration: rules first, I/O last
├── http.go      ServeMux adapters; edge validation; envelope via httpx
├── postgres.go  pgx/gen-db adapter; rows to domain; errors inward
├── queries.sql  sqlc source for this slice (schema = migrations/)
└── module.go    Register(mux, Deps) — the wiring contract
```

- "Where does X live?" is answerable by file kind: a business rule change is a
  `domain.go` change; a new query is `queries.sql` + `postgres.go`; a new
  endpoint is an `http.go` route registered in `module.go`; a new vendor is a
  new `platform/<x>` port + adapter; a wiring change is `cmd/api/main.go` only.
- The same six files always; tests ride alongside (`*_test.go`). A slice whose
  `domain.go` passes ~200 lines is usually two features sharing a directory —
  split by behavior, not by file count.

## Allowed and forbidden edges

| From | To | OK? |
|---|---|---|
| `cmd/api`, `cmd/worker` | any internal package | yes — roots know everything |
| slice `http.go` / `postgres.go` / `module.go` | own slice's files, `platform/`, `shared/` | yes |
| `usecase.go` | `ports.go`, `domain.go` | yes |
| `ports.go` | `domain.go` | yes |
| `domain.go` | stdlib + `internal/shared` | yes, only that |
| slice `postgres.go` | `internal/gen/db` | yes |
| adapters | `gen/api` models only from `http.go` | wire types stop at the edge |
| `internal/platform/**` | stdlib, `gen/db`, `shared/` | yes, never `internal/features/**` |
| anything | `cmd/**` | NO — nothing depends on the root |

## Ports: consumer-defined, one or two methods

The counter-intuitive part, and the important one: **the use case writes the
interface**, in its own `ports.go`, shaped exactly to its needs. The adapter
satisfies it implicitly — Go's structural interfaces mean the adapter need not
import the port package. No port without a consumer; no "repository interface
next to the adapter"; one method is enough. Two slices that keep reaching for
the same need is the signature of a missing shared port, not an import to add.

```go
// internal/features/widgets/ports.go
package widgets

// The use case wrote this; the postgres.go adapter satisfies it implicitly.
type WidgetStore interface {
    ByID(ctx context.Context, id WidgetID) (Widget, error)
    Save(ctx context.Context, w Widget) error
}
```

## Request lifecycle (handbook doc 07)

- **Routes are declared per-slice.** Each slice's `module.go` exposes
  `Register(mux *http.ServeMux, d Deps)` — the whole wiring contract — using
  stdlib method+wildcard patterns:

  ```go
  // internal/features/widgets/module.go
  package widgets

  import (
      "net/http"

      "github.com/<scope>/<app>/internal/platform/httpx"
  )

  func Register(mux *http.ServeMux, d Deps) {
      chain := httpx.Chain(httpx.RequestID, httpx.Logger, httpx.Recover, d.Auth)
      mux.Handle("POST /api/v1/widgets", chain(d.Handler.Create))
      mux.Handle("GET /api/v1/widgets/{id}", chain(d.Handler.ByID))
  }
  ```

  (The exact `httpx` helper names vary by project; the contract is the pattern
  shape — method prefix, `{id}` wildcard, `PathValue` on the handler side, and
  `Register` as the single mount point the root calls.)
- **The middleware chain** (`httpx.Chain`): RequestID -> Logger(slog) ->
  Recover -> RequireAuth -> RequireRole -> handler. `authx.RequireAuth` parses
  the token with the HS256 verifier, builds `authx.Identity`, stores it in
  context, and answers 401 with the `{detail, code}` envelope on failure.
- **Identity in context**: use cases never re-parse tokens and never see
  `*http.Request` — the handler passes `r.Context()` plus the parsed input.
  That boundary is why the same use case can serve HTTP, a WS handshake, or a
  CLI.
- **Streaming aside (WS/SSE)**: read from `r.Context()`; the client disconnect
  *is* the cancellation; never hold a database row while streaming. WS
  authentication failure closes with code 4001; SSE flushes per event.
- **The worker** (`cmd/worker`) runs two loops — email outbox and janitor —
  exiting on SIGTERM via the same context discipline. Migrations never run at
  server startup.

## Persistence rules (handbook doc 08)

- The pool is built once at the root. Nothing else names `pgxpool`; adapters
  receive a narrow store interface, not `*pgxpool.Pool`.
- **Per-slice `queries.sql`**: names only the tables the slice's migration
  created; sqlc's schema is pointed at `migrations/`; output is the committed
  `internal/gen/db` (package db); the `postgres.go` adapter is the only
  consumer. `make generate` / `make gen-check` keep it honest; never hand-edit
  `internal/gen/**`.
- **Goose migrations**: paired Up/Down sections in timestamped files
  (`make migrate-add NAME=add_orders`), applied with `go tool goose` as a
  deploy step — **never at server startup**. The integration suite walks
  apply -> down -> apply so reversal stays honest.
- **The adapter is dumb**: call gen/db, map rows to domain, translate driver
  errors inward. No SQL outside the slice's `queries.sql`; no pgx types leak
  past `postgres.go`.

## Error envelope and slog policy (handbook doc 10)

- Every non-2xx body is `{"detail": string, "code": STABLE_CODE}`. Codes are
  constants in `internal/shared/apperr`; adapters never invent codes; use
  cases return sentinel-wrapped errors; `httpx` maps code to HTTP status in
  exactly one place. Clients key on the code, not the message.
- Wrap with `%w`, match with `errors.Is`/`errors.As`. `httpx.Recover` turns
  panics into a 500 envelope, stack logged once at the recovery point.
- **`slog` with the JSON handler is the only logger**; `request_id` from
  middleware on every per-request log. Log at the boundary where context
  exists; never log inside `domain.go`; never log-and-return the same error.
- OpenTelemetry is deliberately cut; context propagation is real, so adding
  `otelhttp` at the chain head later touches no slice code.

## Testing shape and the gate

- **Fakes, not mocks**: port interfaces are 1-2 methods, so unit tests write
  plain in-memory fakes over `ports.go` — no mocking framework, no database,
  no network. Integration (testcontainers Postgres) runs under
  `-tags=integration`; godog acceptance runs over the real mux wired with
  fakes.
- The gate: `make ci` = gofmt check + `go vet ./...` + `golangci-lint run` +
  gen-check + `go test ./...`.

## Enforcement notes

- depguard violations fail `make ci` red. **Fix the shape, not the lint** —
  never `//nolint:depguard` an edge away; if the edge is needed, the topology
  is wrong (or the rule is — argue the rule in review, never at the call
  site).
- The "depends on the port but reaches for the adapter" smell is a constructor
  argument, not an import — review catches it; depguard cannot.
- **Don't create `internal/utils`.** Anything "util" is either a mechanism
  (move to `platform/`) or a domain concept (move to the slice that owns it).

Full source: the backend-go template's docs tree (00-14) and its
`skeleton/.golangci.yml`; the facta template lives at
`facta/package_builder/templates/backend-go/`.