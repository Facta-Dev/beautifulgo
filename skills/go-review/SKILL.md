---
name: go-review
description: >-
  Review existing Go code for idiom, API design, error handling, concurrency,
  and hexagonal architecture, and produce a prioritized report where every
  finding cites the rule it breaks, its file:line location, and the smallest
  concrete fix. Use whenever the user asks to review, audit, critique, grade,
  check, or explain what is wrong with Go code - a .go file, a package, a
  module (go.mod), a diff, a pull request, or golangci-lint, go vet, or gofmt
  output - including pgx, sqlc, goose, slog, net/http ServeMux, context,
  goroutines, channels, and table-driven tests, even when the user does not
  say "best practices". Pairs with the go-best-practices skill, which covers
  writing new Go code.
---

# Go review

Review Go code against the same rules the `go-best-practices` skill uses for
writing it, and report what to change. The output is a review, not a rewrite:
the reader decides what to fix. Only rewrite code when the user asks for that.

## 1. Decide the scope

- **What to read.** Review exactly what the user pointed at: a file, a package,
  a slice, or a diff. For a diff, review the changed lines and anything they
  break, not the whole file.
- **Stack or not.** A `go.mod` plus `internal/features/<slice>/` directories
  holding the `domain.go` / `ports.go` / `usecase.go` / `http.go` /
  `postgres.go` / `module.go` set means the facta backend-go stack applies at
  full strictness: the slice topology, consumer-declared ports, the `{detail,
  code}` envelope, and the depguard rules are law. A partial snapshot counts
  too: apply the stack rules to the slice files and the general rules to the
  rest. State at the top of the report which mode you reviewed under. A repo
  without that layout - a CLI, a library, a tool - gets the general rules only:
  do not impose six-file slices, an `apperr` envelope, or a `platform/` layer
  on a package that is not part of a server.
- **The Go version and module shape**, from `go.mod`, so you don't recommend
  features or patterns the project can't use: `http.ServeMux` method+wildcard
  routing needs Go 1.22+, so a module pinned older should not be told to use
  it. An importable library module (no `internal/`) is held to the API-design
  rules strictly; application code gets the simplicity rules. Say which you
  assumed at the top of the report.
- **The lint config.** If a `.golangci.yml` exists, read it and review against
  what it enables, not the defaults. If it is missing, the mechanical rules run
  weaker than they should - fold that into the report and see section 5.

## 2. Run the tools first, if you can

If a Go toolchain is available, run these from the module root and fold the
results into the report. They catch the mechanical issues, which leaves you
free for design and architecture.

```bash
gofmt -l .
go vet ./...
golangci-lint run
go test -race ./...
```

Don't paste raw tool output. Group repeated warnings into one finding, skip
pedantic noise that doesn't matter for this code, and say what you couldn't
run (no toolchain here, a file snapshot without `go.sum` or a missing
generated package) so the reader knows which findings are from reading. The
`go-best-practices` skill holds the full "before you hand back code" tool
list; this section is the review-sized version of it.

## 3. What to look for, in priority order

Work through these in order. The first two categories are where real bugs and
real rework live.

**Architecture violations** - stack repos only; cite each as `dep: <rule>`,
the depguard rule name in the stack's `.golangci.yml`.

- `domain.go` importing `net/http`, `database/sql`, `pgx` (any
  `github.com/jackc/pgx/v5/...` package), `internal/gen`, `internal/platform`,
  or another feature slice - the domain stays zero-I/O (`dep: domain-pure`).
- `usecase.go` or `ports.go` importing `net/http` or `pgx` - mechanism names
  belong to adapters (`dep: usecase-transport-free`).
- Any file under `internal/features/` importing another slice - vertical
  slices are sealed; share through `internal/shared`, `platform/`, or a
  consumer-declared port (`dep: slice-isolation`).
- Code under `internal/platform/` importing `internal/features/**` - platform
  serves features, never consumes them (`dep: platform-no-features`).
- A port with no consumer, or an interface declared "for the future" - no
  consumer, no port (backend-go handbook).
- A use case that takes the adapter type (the pgx-backed struct from
  `postgres.go`) as a parameter instead of its own port from `ports.go` - the
  constructor-argument version of the law, which depguard cannot see because
  it is not an import. Flag it anyway (backend-go handbook).
- SQL in `.go` files bypassing the slice's `queries.sql`, or hand-edited
  `internal/gen/**` - the adapter calls the generated queries, nothing else.
- An adapter inventing `apperr` codes or writing the `{detail, code}`
  envelope outside `httpx` - the envelope has one definition, and codes are a
  stable contract (backend-go handbook).
- goose migrations applied at server startup - migrations are a deploy step,
  never `main()` (backend-go handbook).

**Correctness**

- Panics on reachable paths: indexing a slice parsed from input without a
  length check, a type assertion without the `ok` form (`v := x.(T)` instead
  of `v, ok := x.(T)`), a nil map write, or a nil dereference on a value that
  can be absent - wherever input from outside can reach them.
- Swallowed errors: an `error` assigned to `_`, an error only logged while the
  function keeps going, a result dropped with `_, err :=` and the error
  ignored, or an `if err != nil` branch that returns `nil` instead.
- Wrapping bugs: `fmt.Errorf("failed: %s", err)` and `%s`/`%v` on errors
  instead of `%w` (breaks `errors.Is`), an error compared with `==` or a tag
  string instead of `errors.Is`/`errors.As`, and a wrapped error that drops
  the sentinel entirely (linters: `errorlint`, `errcheck`, `govet`).
- Data races: shared state reached from two goroutines without a mutex or
  channel, a goroutine with no owner or shutdown path, or a struct with a
  `sync.Mutex` field copied by value.
- Lost cancellation: a long wait with no `select` on `ctx.Done()`, an
  I/O call that takes `context.Background()` where a request context was in
  hand, or a goroutine started with `context.Background()` when it should
  derive from the caller.
- Leaked resources: `rows.Close()`, `resp.Body.Close()`, or `ticker.Stop()`
  never called; a row cursor held while streaming an HTTP response.
- `time.Sleep` used to coordinate goroutines instead of channels or
  `sync.WaitGroup`.

**Error handling**

- Errors callers can't act on: no sentinel exported for a case callers must
  distinguish, or an error type without an `Error() string` method.
- Names: a sentinel named `ErrorFoo` instead of `ErrFoo`, or an error type
  that doesn't end in `Error` (linter: `errname`).
- `panic` used for expected failures (bad input, missing row), or `recover`
  used as control flow outside a recovery middleware boundary.
- Every `fmt.Errorf` carries a verb phrase: `fmt.Errorf("get widget: %w",
  err)`, never `fmt.Errorf("%w", err)`.

**API design** (strict for library modules)

- One-implementation interfaces declared outside the stack's `ports.go` - an
  interface needs a second plausible implementation or a consumer; otherwise
  use the concrete type (backend-go handbook; Google Go Style Guide).
- Boolean parameters in signatures, especially ones that switch behavior at
  a distance (`save(ctx, o, true)`); use two methods or an enum-like type.
- Stuttering names (`widgets.Widgets`), a `Get` prefix on getters, and
  packages named `util`, `helper`, or `manager`.
- Missing constructors: exported types with a non-trivial zero value should
  get `New<Type>`; errors as exported sentinel values, not string fields.
- Exported fields that should be private with accessors, and third-party
  types (`pgx` rows, types from a driver) leaking into a package's public
  signatures.
- An exported function that takes a whole struct to use two fields where
  two parameters would say what is required.

**Idiom and clarity**

- Interfaces introduced where a concrete type clearly does, so the code has
  an abstraction with no second implementation in sight.
- Check-then-act redundancy: `if x != nil { return x }` chains, a `map`
  lookup tested with a separate `_, ok :=` and then indexed again, a loop
  that is clearer as an `if` with a range over a slice of two.
- Map iteration order leaking into output or tests - range over a map and
  print, without sorting keys first.
- `//nolint` without a reason, especially `//nolint:depguard` used to sneak
  an import edge past the architecture law - the fix is the shape, never the
  comment; if the edge is genuinely needed, the rule or the topology changes
  in review, not the call site.
- `fmt.Print*`, `log.Print*`, or `println` in application code instead of
  structured `slog` with the JSON handler.
- String building with `+=` in a loop where a `[]string` + `strings.Join`
  or `strings.Builder` is cheaper and clearer.

**Docs and tests**

- Exported items without doc comments, and docs that restate the name.
- Logic with no tests, or no table-driven tests on logic that branches -
  Go tests are table-driven with named fields (`name`, `got`, `want`) and
  `t.Run` subtests.
- Tests that only restate constants, and a test binary run without `-race`
  where goroutines appear.
- Mock frameworks where an in-memory fake of a 1-2 method port would be
  ten lines - the stack's ports are small on purpose (backend-go handbook).

The `go-best-practices` skill and its `references/` folder hold the full
rules and their sources. If it is installed, read the relevant digest when a
finding needs a rule you're unsure of. Otherwise, rely on the summary above.

## 4. Write the report

Use this structure:

~~~markdown
# Go review: <what was reviewed>

<One paragraph: what the code does, which mode you reviewed under (stack or
general), tools run or couldn't run, overall verdict, and the single most
important thing to fix.>

## Must fix
### 1. <Short title> (`internal/features/store/domain.go:26`)
**Rule:** dep: domain-pure (depguard in the stack's .golangci.yml)
**Problem:** <what is wrong and the concrete consequence, one or two sentences>
**Fix:**
```go
<the smallest code change that fixes it>
```

## Should fix
### 2. ...

## Consider
### 3. ...

## What's already good
- <2 to 4 specific things the code does well>
~~~

How to sort findings:

- **Must fix** means an architecture violation (a depguard-ruled edge or the
  adapter-reach smell), a bug, a data race or deadlock, a reachable panic, a
  swallowed error, or an API mistake that becomes a breaking change once
  other code depends on it.
- **Should fix** means it works but violates a rule with a real cost: worse
  error messages, harder testing, a leaked resource, or a confusing API.
- **Consider** means style, naming, and polish.

Rules for each finding:

- **Cite a location** as `file:line` for every finding (write `whole file`
  for a finding that has no single location, such as missing tests), and
  cite the rule with its source: a depguard rule name written as
  `dep: domain-pure`, a golangci linter name such as `errorlint` or
  `errcheck`, a Go wiki CodeReviewComments heading, a Google Go Style Guide
  section, an Effective Go passage, or "backend-go handbook". A reader
  should be able to look the rule up.
- **Show the fix as code**, kept to the lines that change. Don't rewrite
  whole functions.
- **Group repeats.** One finding for "four `fmt.Errorf` calls that wrap with
  `%s`", listing the lines, rather than four findings.
- **Respect intent.** If something looks deliberate, such as a documented
  quirk or a comment explaining it, mention it under Consider with the
  trade-off. Don't mark it Must fix.
- **Keep it proportionate.** For a short file, five to ten findings is
  plenty. Don't pad the list, and don't hide a real bug among style nits.
- **"What's already good" is required.** It tells the author what to keep
  and makes the rest credible. Name the valid Go shapes specifically - a
  consumer-declared port, an `errors.Is` translation, a usable zero value,
  a table-driven test - so the review doesn't read as "everything here is
  wrong".

## 5. Offer the lints

If the project lacks a `.golangci.yml`, end the report by suggesting the
beautifulgo drop-in (`lints/.golangci.yml` in the beautifulgo repo).
It enables the four depguard
architecture rules (`domain-pure`, `usecase-transport-free`,
`slice-isolation`, `platform-no-features`) plus `contextcheck`, `errname`,
`errorlint`, and `noctx` over the standard set, so the linter catches most of
the mechanical findings above automatically. Name two or three findings from
this review that it would have caught.
