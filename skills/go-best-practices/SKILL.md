---
name: go-best-practices
description: >-
  Write idiomatic Go on the hexagonal, vertical-slice stack. Use this skill whenever you
  write, refactor, debug, or explain Go code: new packages, files, functions, structs,
  interfaces, error types, goroutines, channels, context, generics, go.mod, or
  table-driven tests. Trigger on any mention of Go, golang, .go files, gofmt, go vet,
  golangci-lint, pgx, pgxpool, sqlc, golang-migrate, goose, river, chi, wire, redis,
  validator, slog, net/http, ServeMux, context, goroutines, or channels, even when
  the user does not say "best practices" or "idiomatic" code.
  Synthesized from Effective Go, the Go Code Review Comments wiki, the Google Go Style
  Guide, Rob Pike's Go Concurrency Patterns, and the backend-go handbook. For auditing
  existing code use go-review; for translating C, Python, or JavaScript into Go use
  go-port.
---

# Go best practices

Distilled from five Go style and design sources, with a digest of each in
`references/`. Where they disagree, this file says which to follow and why.

## 1. Mindset

- **Write Go-shaped code.** Don't transliterate Python, Java, TypeScript, or C.
  Errors are values you wrap and return, not exceptions; absence is `nil`, not
  `Option` or a null object; polymorphism is small interfaces satisfied
  implicitly, not class hierarchies; concurrency is goroutines plus channels, not
  threads sharing locks everywhere. A Go developer reading the diff should not be
  able to tell which language the code came from.
- **Zero-I/O domain.** Business rules live in code that imports the standard
  library and nothing that talks to the world. If a rule needs data, it receives
  it as an argument. On the stack this is law, not taste (§2).
- **Application code favors directness.** Concrete types, plain `string` and
  `int64` parameters, `error` values returned plain. Speculative interfaces,
  generic wrappers, and "repository patterns" with one implementation are smells,
  except where §2 mandates a port — and there the port exists because a consumer
  needs it and an adapter implements it, never "for the future".
- **Let the tools carry the rules.** gofmt owns formatting, go vet and
  golangci-lint own the checkable rules, the compiler owns most everything else.
  Every rule below that a tool can check is phrased so the tool catches it.

## 2. Architecture contract (the backend-go stack)

When the repo has `internal/features/` slices, this is a MUST/MUST NOT contract,
not style. The contract is **unbreakable and non-waivable**: developers cannot opt
out, and neither can you. When a depguard rule fires, the fix is to re-cut the
layout — never to weaken, rename, or delete the rule, and never to silence it with
`//nolint` (that nolint is itself a review finding in `go-review`). Enforcement:
the `lints/.golangci.yml` drop-in (depguard) plus `go vet`. The depguard law,
reproduced — the four rule names are the shared vocabulary between this skill and
the lints config:

| Rule | Files it governs | Forbidden imports |
|---|---|---|
| `domain-pure` | `**/internal/features/**/domain.go` | everything outside the allow-list: the standard library plus `<app>/internal/shared` only — notably `net/http`, `github.com/go-chi/chi/v5`, `database/sql`, `github.com/jackc/pgx/v5`, `github.com/riverqueue/river`, `github.com/redis/go-redis/v9`, `go.opentelemetry.io/*`, `github.com/prometheus/client_golang`, `internal/gen`, `internal/platform`, other slices |
| `usecase-transport-free` | `**/internal/features/**/usecase.go`, `**/internal/features/**/ports.go` | `net/http`, `github.com/go-chi/chi/v5`, `database/sql`, `pgx/v5`, `internal/gen`, `internal/platform` |
| `slice-isolation` | `**/internal/features/**` | any other `internal/features` package |
| `platform-no-features` | `**/internal/platform/**` | `internal/features` |

The shipped config spells internal-package patterns with the absolute
placeholder `github.com/<scope>/<app>/internal/...`: depguard's `pkg` patterns
prefix-match import paths (pattern + every subpackage, `$` exact), so those
rules must carry the real module path. The table shortens them to the
`/internal/...` tail for readability, and the config header says how to
substitute the placeholder once (see `lints/README.md` in the repo). Only the
`files:` globs use `**/internal/...` forms and they match any module verbatim.

MUST rules:

- **MUST keep `domain.go` zero-I/O.** It imports the standard library +
  `internal/shared` only. No `net/http`, no chi, no `database/sql`, no pgx, no
  river, no redis, no generated
  code, no platform packages, no cross-slice imports. A rule that needs data from
  the world receives it as an argument.

  ```go
  // WRONG: a domain type carrying a pgx dependency
  package widgets

  import "github.com/jackc/pgx/v5"

  type Widget struct {
      ID    WidgetID
      Row   pgx.Row // domain must not know pgx
  }
  ```

  ```go
  // RIGHT: pure types and rules; rows are mapped in the adapter
  package widgets

  type Widget struct {
      ID    WidgetID
      Name  string
      Size  Size
  }
  ```

- **MUST define ports where they are consumed.** `usecase.go` declares the
  interfaces it needs in `ports.go`, shaped to its needs — 1–2 methods, no port
  without a consumer. Adapters satisfy them implicitly.

  ```go
  // internal/features/widgets/ports.go
  package widgets

  // Consumer-defined: the use case wrote this, the adapter satisfies it.
  type WidgetStore interface {
      ByID(ctx context.Context, id WidgetID) (Widget, error)
      Save(ctx context.Context, w Widget) error
  }
  ```

- **MUST keep adapters dumb.** `http.go` validates at the edge and writes the
  `{detail, code}` envelope via `httpx` only. `postgres.go` calls `gen/db`,
  maps rows to domain types, and translates driver errors inward to domain
  errors. No rules in adapters.
- **MUST NOT import between slices.** Slices share through `internal/shared`
  (kernel), `internal/platform/`, or a narrow port declared by the consumer —
  never a sideways import. Fix the shape, not the lint: never
  `//nolint:depguard` an edge away.
- **MUST pair every `queries.sql` change with its migration.** A slice's
  `queries.sql` names only tables its migration created; both change in the same
  commit; generated `internal/gen/**` is committed and never hand-edited
  (`make generate` must be a no-op).
- **MUST keep migrations reversible and out of startup.** golang-migrate is the
  standard: paired Up and Down migration files in `migrations/`, applied by a
  deploy step (`make migrate`), never when the server boots. goose is an
  acceptable explicit alternative with the same Up/Down discipline; whichever
  tool runs, reversibility stays honest (the integration suite walks
  apply -> down -> apply).
- **MUST follow the request lifecycle.** Routes declared per-slice in
  `module.go` via `Register(r chi.Router, Deps)` mounting chi's method+wildcard
  pattern shape (`"POST /api/v1/widgets"`, `r.Get("/widgets/{id}")`,
  `chi.URLParam(r, "id")` — the ServeMux `PathValue` shape carried by chi); the
  composition root in `cmd/` wires everything with wire; identity travels in
  context; `r.Context()` flows into every use case and port call.
- **MUST wrap errors with `%w` and match with `errors.Is`/`errors.As`.** Adapters
  never invent envelope codes; the stable `{detail, code}` vocabulary lives in
  `internal/shared/apperr`.
- **MUST use one logging policy: `slog` with the JSON handler.** `request_id`
  comes from middleware. Never log inside `domain.go`, never log-and-return the
  same error.

Instruction: when a repo has `internal/features/` and this template, read
`references/backend-go-stack.md` first and leave alone what the template
mandates — the six files per slice, the `Register` contract, committed
`internal/gen/`. A correct slice is not something to "improve".

## 3. Before you hand back code

Run these and fix everything they report:

```bash
gofmt -l .           # empty output
go vet ./...
golangci-lint run    # project config, or the lints/ drop-in
go test ./...        # with -race in CI and wherever concurrency appears
go tool sqlc generate && make gen-check   # stack projects; must be a no-op
```

- Fix a lint rather than silencing it. When a lint is genuinely wrong for one
  item, `//nolint:<name> // reason` goes on the narrowest line with a reason.
  NEVER use `//nolint:depguard` to sneak an import edge past the architecture
  law — fix the shape, or argue the rule in review.
- Configure lints once in `.golangci.yml`. If the project has none, suggest the
  drop-in from https://github.com/beautifulgo; it encodes the depguard contract
  in §2, and every project other than the facta template substitutes its module
  path once for the `github.com/<scope>/<app>` placeholder (see
  `lints/README.md`).
- `go vet` is the floor, not the ceiling: it catches printf-verb mistakes,
  unused results, and lock copying that review otherwise finds by eye.

## 4. Types and interfaces

### Naming

| Item | Case | Example |
|---|---|---|
| Types, exported funcs, methods | `MixedCaps` (Go never uses underscores in names) | `WidgetStore`, `NewHandler` |
| Unexported funcs, locals | `mixedCaps` | `parseCode` |
| Constants | `MixedCaps` for exported, `mixedCaps` private | `MaxRetries`, `errCodeLen` |
| Packages | short, lowercase, no underscores | `widgets`, `httpx`, `apperr` |

- Initialisms stay all-caps: `URL`, `ID`, `HTTP`, `API`. `WidgetID`, not
  `WidgetId`; `ServeHTTP`, not `ServeHttp`.
- No `Get` prefix on getters: `w.Name()`, not `w.GetName()`. Go the language and
  both style guides agree; getters are unnecessary anyway when the field can be
  exported.
- The package name carries meaning: `widget.ID`, never `widgets.WidgetID` (no
  stutter). Name packages after what they provide (`httpx`, `time`), never
  `util`, `helper`, `common`, `misc`, `base`.
- Sentinel errors start with `Err`: `ErrWidgetMissing`. Error types end in
  `Error`: `ParseError` (errname).

### Accept interfaces, return concrete types

- Parameters accept interfaces, returns are concrete — the caller stays
  flexible, the semantics stay inspectable.
- **No interface pollution.** An interface needs a second plausible
  implementation or a consumer that declared it as a port. An interface with one
  implementation outside `ports.go` is a smell. Do not pre-declare "the
  repository interface next to the adapter" — declare the port where the use
  case consumes it.

  ```go
  // WRONG: an interface invented to organize code, one implementation
  type WidgetRepository interface {
      Save(ctx context.Context, w Widget) error
  }
  ```

  ```go
  // RIGHT: the use case declares the name and shape it needs
  type WidgetStore interface {
      Save(ctx context.Context, w Widget) error
  }
  ```

- Keep structs small with a usable zero value. `bytes.Buffer`, `sync.Mutex`,
  `time.Time` all work at zero; design yours to as well, so `var s MyServer`
  compiles into something correct.

### Constructors, conversion, and shapes

- Constructors are `New<Type>` (`NewHandler`, `NewStore`); fallible ones are
  `New...` returning `(T, error)`. No errors in var blocks of a different shape.
- **No `bool` parameters in shared signatures.** `Save(w, true)` is unreadable
  at the call site and cannot grow a third mode. Use two methods
  (`save`, `saveAndValidate`) or a small typed constant.

  ```go
  // WRONG
  func Report(w Widget, includeSecrets bool) string
  ```

  ```go
  // RIGHT: a typed mode, not a bool
  type ReportKind int

  const (
      ReportPublic  ReportKind = iota
      ReportInternal
  )

  func Report(w Widget, kind ReportKind) string
  ```

- No `bool` fields on option structs either — an option struct with `Strict bool`
  is the same unreadable call site one level removed.
- Generics where they earn their keep, nowhere else: a constraint earns its
  existence when the code is otherwise duplicated per type (`Map[T, U]` over
  slices, a container, a `Number` helper). A generic that wraps one concrete
  type, or an interface constraint satisfied by exactly one type, is ceremony.

  ```go
  // RIGHT: real duplication removed
  func Keys[K comparable, V any](m map[K]V) []K {
      ks := make([]K, 0, len(m))
      for k := range m {
          ks = append(ks, k)
      }
      return ks
  }
  ```

  ```go
  // WRONG: generics to look modern
  func Load[T any](ctx context.Context, id string) (*T, error)
  ```

## 5. Errors and panics

- **Sentinel + wrap.** Declare sentinels with `errors.New`, add context with
  `fmt.Errorf` and `%w`. Every `fmt.Errorf` carries a verb phrase — "get widget",
  never bare interpolation.

  ```go
  var ErrWidgetMissing = errors.New("widget not found")

  if errors.Is(err, db.ErrNotFound) {
      return Widget{}, ErrWidgetMissing
  }
  if err != nil {
      return Widget{}, fmt.Errorf("get widget %s: %w", id, err)
  }
  ```

- **Match with `errors.Is` (sentinels) and `errors.As` (typed causes)** — never
  string comparison, never a type assertion without the comma-ok form, never
  `%s` where `%w` belongs (errorlint).

  ```go
  // WRONG
  if err == ErrWidgetMissing { .. }
  if pgErr, ok := err.(*pgconn.PgError); ok { .. }
  return fmt.Errorf("get widget: %s", err)
  ```

  ```go
  // RIGHT
  if errors.Is(err, ErrWidgetMissing) { .. }
  var pgErr *pgconn.PgError
  if errors.As(err, &pgErr) {
      if pgErr.Code == pgerrcode.UniqueViolation { return ErrEmailTaken }
  }
  return fmt.Errorf("get widget: %w", err)
  ```

- **Panics are for programmer bugs only.** `panic` on impossible internal state;
  `error` on everything reachable from outside, including bad input, missing
  files, and network failures. `recover` lives only in the recovery middleware
  (`httpx.Recover`), never sprinkled through business code.
- Wrap don't swallow: an error you return loses nothing; one you log-and-return
  chains twice; one you discard (`_ = f()`) — errcheck flags it.
- No panic-converting helpers (`Must` variants) in stack code outside package
  init on compile-time constants.

## 6. Context propagation

- `ctx context.Context` is the first parameter, named `ctx`, of every function
  that does I/O, waits, or runs work per request.
- **Never store a context in a struct** — pass it through. A struct holding a
  ctx freezes one request's scope into a long-lived object, which vet's
  `context` check and review both flag.
- Take `r.Context()` at the edge (the handler) and hand it inward untouched.
- **Respect cancellation.** Blocking work selects on `ctx.Done()`; loops check
  it; long polls use `context.WithTimeout` at the caller with the deadline that
  belongs there, not a global constant.

  ```go
  // WRONG: ignoring the request context the handler already gave you
  ctx := context.Background()
  rows, err := s.q.ListWidgets(ctx, userID)
  ```

  ```go
  // RIGHT
  func (s Store) ByID(ctx context.Context, id WidgetID) (Widget, error) {
      row, err := s.q.GetWidget(ctx, id)
      ...
  }
  ```

- No `time.Sleep` to coordinate goroutines or "wait for readiness" — a timer is
  not a signal. Use channels, `sync.WaitGroup`, or context cancellation.
- On the stack: use cases and ports take `ctx` first; adapters pass it to
  gen/db; streaming handlers (SSE/WS) read `ctx.Done()` for teardown — the
  client disconnect *is* the cancel.

## 7. Concurrency

- **Every goroutine has an owner and a shutdown path.** A `go` statement whose
  lifetime you cannot bound, whose errors you cannot observe, or that outlives
  its request context is a leak.

  ```go
  // WRONG: fire-and-forget; nothing stops it, nothing observes it
  go func() {
      time.Sleep(2 * time.Second)
      s.metrics.Record(q)
  }()
  ```

  ```go
  // RIGHT: owned loop with a stop channel and a done handshake
  func (s *Service) Run(ctx context.Context) {
      go func() {
          <-ctx.Done()
          close(s.stop)
      }()
      for {
          select {
          case <-s.stop:
              return
          case q := <-s.queue:
              s.record(q)
          }
      }
  }
  ```

- **Durable work is River work, not a goroutine.** Anything that must survive
  the process — emails, webhooks, reindexes, scheduled sweeps — goes through
  River: a job struct with a `Kind()`, enqueued with `AddTx` inside the **same
  Postgres transaction** as the write, retried with backoff, deduped by
  `UniqueOpts` when a repeat send is intolerable; periodic sweeps ride
  `river.PeriodicJobs` (old janitor loops). A fire-and-forget goroutine is by
  definition *not* durable: one crash and the work is gone without a trace.
  The worker process itself shuts down gracefully — River drains in-flight
  jobs on SIGTERM.

  ```go
  // postgres.go — the write and its after-effect commit together
  type NotifyArgs struct {
      WidgetID WidgetID
  }

  func (NotifyArgs) Kind() string { return "widgets.notify" }

  type store struct {
      river *river.Client[pgx.Tx]
  }

  func (s store) enqueueNotify(ctx context.Context, tx pgx.Tx, id WidgetID) error {
      _, err := s.river.AddTx(ctx, river.AddTxArgs{
          Tx:   tx,
          Args: NotifyArgs{WidgetID: id},
          Opts: &river.InsertOpts{
              Queue:      "widgets",
              UniqueOpts: river.UniqueOpts{ByArgs: true}, // a retry never double-sends
          },
      })
      if err != nil {
          return fmt.Errorf("enqueue widget notify %s: %w", id, err)
      }
      return nil
  }
  ```

- **Channels for ownership transfer, mutexes for state.** Don't share memory by
  communicating when a `sync.Mutex` around one map says it in three lines; don't
  bolt a mutex onto what is already an ownership handoff.
- `sync.WaitGroup` for fan-out joins, `sync.Once` for one-time setup, `sync/atomic`
  for single counters. Prefer them over hand-rolled maps of channels.
- **Never copy a value that contains a mutex** (vet catches this): receivers and
  arguments pass mutex-bearing types by pointer.
- Don't close another goroutine-owned channel; the sender closes, the receiver
  only ranges.
- Run `go test -race` whenever two things in the package touch shared state.
- Before redesigning a pipeline, read `references/go-concurrency-patterns.md` —
  most "pipeline" code wants two channels and a WaitGroup, not an architecture.

## 8. Standard library first

- **chi is the router.** The stack mandates `github.com/go-chi/chi/v5` — a
  net/http-native router, so handlers stay plain `http.HandlerFunc`s and
  nothing custom crosses the port boundary. The ServeMux pattern shape is
  still the contract: chi mounts the same method + wildcard strings
  (`"POST /api/v1/widgets"`, `"GET /api/v1/widgets/{id}"`), just via
  `r.Post`/`r.Get` instead of `mux.HandleFunc`. gin and echo are acceptable
  alternatives when a review approves the deviation; fiber only for
  extreme-throughput gateways — never the default choice.

  ```go
  // module.go — the port-compatibility shape: the pattern is the router.
  // The ServeMux spelling still stands on non-stack ports and legacy code;
  // on the stack the chi form below is the router.
  func Register(mux *http.ServeMux, d Deps) {
      mux.HandleFunc("POST /api/v1/widgets", d.Handler.Create)
      mux.HandleFunc("GET /api/v1/widgets/{id}", d.Handler.ByID)
  }
  ```

  ```go
  // module.go — the same wiring on chi, the stack's router. Middleware order
  // is registration order: r.Use first (every route in the group), then
  // r.With for per-route guards inside it.
  func Register(r chi.Router, d Deps) {
      r.Route("/api/v1", func(r chi.Router) {
          r.Use(httpx.RequestID, httpx.Logger, httpx.Recover)
          r.With(d.Auth).Post("/widgets", d.Handler.Create)
          r.With(httpx.RequireRole("admin")).Get("/widgets/{id}", d.Handler.ByID)
      })
  }
  ```

  ```go
  // http.go — the handler reads the wildcard by its chi name, the
  // URLParam spelling of the ServeMux r.PathValue("id") shape.
  func (h Handler) ByID(w http.ResponseWriter, r *http.Request) {
      id, err := widgets.ParseWidgetID(chi.URLParam(r, "id"))
      ...
  }
  ```

- Every dependency costs build time, audit surface, and supply-chain risk.
  Before adding one, check whether the standard library has it (`net/http`,
  `encoding/json`, `slog`, `context`, `sync`, `time`); before writing a helper,
  check whether it already exists in the module.
- Single go module; no per-slice modules, no workspaces for an application's
  internal packages. `go.mod` pins direct dependencies at modern majors; commit
  both `go.mod` and `go.sum`.
- Mandated by the stack: chi (router), pgx/v5 + pgxpool, sqlc, golang-migrate
  (goose is the explicit acceptable alternative), river (durable jobs), go-redis
  (cache), google/wire (compile-time DI at the composition root),
  go-playground/validator at transport edges, slog (zap the acceptable
  alternative), OpenTelemetry (otelhttp at the chain head), the prometheus
  client, PgBouncer in transaction pooling mode, and Docker/K8s for delivery.
  Also allowed: testify/go-cmp in tests, jwt/v5, env/v11. Anything beyond that
  list is a review conversation.

## 9. Packages and file organization

- **The template topology wins in stack projects** — six files per slice,
  always:

  ```
  internal/features/widgets/
  ├── domain.go    pure types + rules + errors (stdlib + shared only)
  ├── ports.go     the interfaces this feature needs (consumer-defined)
  ├── usecase.go   orchestration: rules first, I/O last
  ├── http.go      chi route adapters, edge validation, envelope
  ├── postgres.go  pgx/gen-db adapters, error translation inward
  ├── queries.sql  sqlc source for this slice (schema = migrations/)
  └── module.go    Register(r chi.Router, Deps) — the wiring contract
  ```

- "Where does X live?" is answerable by file kind, never by grep.
- New capability = new slice directory wired at the root. Never a new horizontal
  god-directory: `internal/repos/`, `internal/services/`, `internal/handlers/`
  reintroduce the problem the slices exist to kill.
- `internal/shared` is a kernel, not a junk drawer: types and rules so
  fundamental they never depend on a mechanism (`apperr`, `rolex`, small value
  types). Anything "util" is either a mechanism (→ `platform/`) or a domain
  concept (→ the slice that owns it).
- `internal/platform/` holds transversal infra (`config`, `httpx`, `pgx`, `authx`,
  `email`, `realtime`, `river` for the durable-jobs client and workers, `redis`
  for the cache client, `otel` for tracing setup, `metrics` for the prometheus
  registry). It serves features; it never imports them. `wire` is not a package
  at all — it is compile-time DI generation for the composition root in `cmd/`.
- In non-stack repos, keep packages small and cohesive, one package per
  directory, leaf packages importing sideways never; the same taste applies
  without the six-file law.

## 10. Logging

- `slog` with the JSON handler is the only logger. No `fmt.Println`, `log.Print`,
  or `println` outside scratch code (errcheck and review both flag them).
- Structured attributes over string interpolation:
  `slog.Error("widget save failed", "request_id", rid, "widget_id", id, "err", err)` —
  not `fmt.Sprintf` baked into the message.
- Log at the boundary where the context exists — the handler, the adapter, the
  worker loop. **Never log inside `domain.go`; never log-and-return the same
  error** (the caller logs it, and you get two).
- Attach `request_id` (from `httpx` middleware) to every per-request log.
- Don't log secrets; env parsing scrubs them once, logs never re-derive them.

## 11. Tests

- **Table-driven with named fields.** `name`, `got`, `want`; `t.Run` subtests;
  `t.Parallel()` where the cases are independent.

  ```go
  func TestParseCode(t *testing.T) {
      t.Parallel()
      tests := []struct {
          name   string
          input  string
          want   Code
          errMsg string
      }{
          {name: "six digits", input: "482913", want: Code("482913")},
          {name: "too short", input: "48", errMsg: "must be 6 digits"},
      }
      for _, tt := range tests {
          t.Run(tt.name, func(t *testing.T) {
              t.Parallel()
              got, err := ParseCode(tt.input)
              if tt.errMsg != "" {
                  if err == nil || !strings.Contains(err.Error(), tt.errMsg) {
                      t.Fatalf("ParseCode(%q) err = %v, want %q", tt.input, err, tt.errMsg)
                  }
                  return
              }
              if got != tt.want {
                  t.Fatalf("ParseCode(%q) = %v, want %v", tt.input, got, tt.want)
              }
          })
      }
  }
  ```

- **Fakes, not mocks.** Ports are 1–2 methods, so write in-memory fakes in the
  test file — a struct with a map and the methods. No mocking framework, no
  database, no network, no clock fakes unless the test needs determinism, and
  then inject a `func() time.Time`.
- Test observable behavior and properties (idempotency, monotonicity,
  round-trips), not internal constants restated.
- `testdata/` for fixtures and golden files; `t.Cleanup` over `defer` in helpers
  that register cleanup (defer fires at helper return, t.Cleanup at test end).
- **Write the failing test before the bug fix** — even small ones; it pins the
  regression forever.
- Stack projects: unit tests per slice with fakes over `ports.go`; integration
  (testcontainers Postgres) under `-tags=integration`; godog acceptance over the
  real chi server wired with fakes; River worker tests assert on `river.Job`
  state or run against a testcontainers River schema.

## 12. Performance, in order

- Measure first: `go test -bench`, `pprof` on a live profile. No optimization
  without a number.
- Preallocate slices with capacity when the length is knowable
  (`make([]K, 0, len(m))`); reuse buffers in hot paths; stream over load-everything
  (`http.ResponseWriter` flush, `json.Decoder`, `bufio.Scanner`).
- Avoid interface boxing in hot loops — a concrete-type loop beats
  `[]any` plumbing when the profiler says so.
- Never optimize away correctness or clarity; a deliberate simplification gets a
  comment naming its ceiling (`// naive: O(n²), fine under ~10k rows`).
- The default posture is the boring one: pgxpool is shared and reused, queries
  are indexed, River's workers batch and pace themselves under PgBouncer's
  transaction pooling — the stack already made the big calls. Nothing to
  hand-roll here: no outbox tables, no janitor loops, no fire-and-forget
  goroutines.

## 13. Final checklist

Before returning Go code, confirm:

- `gofmt -l` empty; `go vet ./...` clean; `golangci-lint run` clean; `go test ./...`
  green (with `-race` where concurrency appears).
- `domain.go` imports nothing that does I/O; `usecase.go`/`ports.go` name no
  transport or storage package; no cross-slice imports anywhere.
- Ports are consumer-defined, 1–2 methods, no port without a consumer.
- New SQL landed in the slice's `queries.sql` with the paired migration (Up and
  Down) in the same change; `internal/gen/**` untouched by hand.
- Every wrap is `%w`; every match is `errors.Is`/`errors.As`; sentinels are
  `Err*`.
- `ctx` is the first parameter and it flows from `r.Context()`; no ctx in a
  struct; no `context.Background()` where a request ctx exists.
- Every goroutine has an owner and a shutdown path; `-race` passes on the files
  that touch shared state.
- No bool parameters in shared signatures; no one-implementation interfaces
  outside `ports.go`; no `Get` prefixes; no `util` packages.
- Logging is `slog` JSON, structured attrs, never in domain, never
  log-and-return.
- Tests are table-driven with fakes over ports; the failing test came first for
  any bug fix.

## 14. References

Read these when you need the reasoning behind a rule or a complete checklist for
a task. Each is a condensed digest of one source.

- `references/effective-go.md` (https://go.dev/doc/effective_go): language
  idioms — interfaces, embedding, errors, concurrency flavor, naming.
- `references/go-code-review-comments.md`
  (https://go.dev/wiki/CodeReviewComments): the wiki checklist — error wrapping,
  context keys, initialisms, goroutine lifetimes, imports, naked params.
- `references/google-go-style-guide.md`
  (https://google.github.io/styleguide/go/index): readability decisions, package
  design, error handling policy, naming, when NOT to abstract.
- `references/go-concurrency-patterns.md`
  (https://go.dev/talks/2012/concurrency.slide): pipelines, cancellation,
  fan-in/out, select discipline, when NOT to reach for channels.
- `references/backend-go-stack.md` (the backend-go handbook): read FIRST when the
  repo has `internal/features/` — the six-file slice, dependency edges, request
  lifecycle, persistence rules, error envelope, slog policy, and the depguard
  rule names in sync with `lints/.golangci.yml`.