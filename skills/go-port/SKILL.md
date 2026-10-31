---
name: go-port
description: >-
  Port code from C, C++, Python, Java, JavaScript, TypeScript, Rust, or legacy Go into
  idiomatic Go that keeps the original behavior: error values instead of error codes and
  exceptions, nil instead of NULL, slices instead of pointer arithmetic, context.Context
  instead of sleeps and torn-down threads, and table-driven tests that prove the port
  matches. Use this whenever the user asks to port, translate, convert, migrate, or
  rewrite code in Go ("rewrite this in Go", "what would this look like in Go", "move this
  module to Go"), or to modernize old Go — even if they don't say "port" — for .go
  files, go.mod, gofmt, go vet, and golangci-lint. Pairs with the go-best-practices
  skill, which covers the target code's style.
---

# Go port

The goal is the Go a Go developer would have written to solve the same problem, with the
same observable behavior. A line-by-line transliteration (C written in Go syntax with
`unsafe` and manual index juggling, or Python with `panic`/`recover` standing in for
exceptions and `interface{}` standing in for duck typing) compiles but keeps every
problem the original had and adds Go's rules on top. Port the behavior, not the
structure.

## 1. Understand the original before writing anything

1. **Read the code and its tests**, and anything that calls it, if you have it.
2. **List the observable behavior**: every public function, its inputs, its outputs, and
   every way it can fail. Include the quiet parts, which are where ports go wrong:
   ordering of results, how ties break, what happens on empty input, whitespace and case
   handling, integer limits, and what counts as an error versus a valid edge case.
3. **Note what is incidental**, meaning things the original only does because of its
   language: manual memory management, out-parameters, `NULL` returns, global state,
   fixed-size buffers, a class that exists only to group functions, `isinstance` chains,
   or an exception hierarchy used as an API. These don't carry over.
4. If the original has a bug or an ambiguity, keep its behavior, flag it in the porting
   notes, and let the user decide. A port is not the place to silently fix things.

## 2. Port the tests first

Translate the original tests into Go table-driven tests before porting the
implementation. Keep one Go test per original test, with a name that maps back to it, so
a reader can check coverage. The tests are the definition of "same behavior". If the
original has no tests, write characterization tests from the behavior list in step 1.
Include the quiet parts: empty input, whitespace, case, and integer limits.

## 3. Design the Go API, then implement it

Decide the public types and signatures from the behavior list, not from the original's
shape. Return concrete types; declare an interface only where the port genuinely needs a
swappable callee, keep it to one or two methods, and declare it where it is consumed.
Then implement against the ported tests.

### From C and C++

| In the original | In Go |
|---|---|
| `malloc`/`free`, `new`/`delete`, `create`/`destroy` pairs | Owned types (`string`, `[]byte`, slices, `append`) dropped by the GC; `Close` kept only for real resources (files, rows, response bodies), not for plain data |
| `NULL` meaning "absent" | `nil` with an explicit check, or the comma-ok pattern (`v, ok := m[key]`) |
| Error codes (`-1`, `ERR_*` defines), `errno`, out-params (`int *err_line`, `long *out`) | `error` return values: a sentinel per code (`var ErrSyntax = errors.New("syntax error")`) wrapped with context, or a typed error struct carrying line numbers; data returned as values, not through out-params |
| Flag bitmasks (`CONFIG_TRIM_VALUES \| CONFIG_ALLOW_DUPLICATES`) | An options struct with named fields and a usable zero value; never a raw integer |
| `char *` plus length, `strcmp` | `string` with `==` and `!=` |
| `strcasecmp` / `strncasecmp` | `strings.EqualFold` |
| Pointer plus count, iteration by index | Slices and `range` |
| Fixed-size buffers and their truncation | Growable slices; drop the limit unless the limit is behavior |
| `#define` constants and macros | `const` (or `iota` for enums); macros that compute → functions |
| Global or static mutable state | A struct the caller owns |
| `strtol` and friends | `strconv.Atoi`/`strconv.ParseInt`; `errno == ERANGE` → `errors.Is(err, strconv.ErrRange)`; parse failures map to your sentinels |

Keep it free of cgo and `unsafe` unless the port must interoperate with C, and under the
facta stack never.

### From Python

| In the original | In Go |
|---|---|
| An exception hierarchy | Sentinel errors (`var ErrParse = ...`) or typed error structs whose fields carry the exception's data (line numbers, task names, cycle paths); matched with `errors.Is`/`errors.As` |
| `None` as a value | `nil`, or the comma-ok pattern |
| Strings used as a closed set (`kind in ("build", "test")`) | Typed constants (`iota`) or a named type with a parse function; never a string compared against literals |
| Dicts or classes used as records | Structs with named fields |
| `dict` insertion order | A slice, or a struct wrapping its map with an explicit ordered key slice; a plain Go map silently reorders |
| Duck typing, `isinstance` | Interfaces (consumer-declared, one or two methods) or typed constants |
| Unbounded `int` | A sized integer chosen on purpose (`int64`), with overflow handled explicitly where input can be large |
| `sorted(..., key=...)` | `sort.Slice` or `sort.SliceStable`; Python's `sorted` is stable, so pick `SliceStable` when stability is observable, or `slices.SortStableFunc` for keyed comparisons |
| `str.splitlines()`, `strip()` | `strings.Split(s, "\n")` (or `strings.Lines` on Go 1.24+), checking edge cases such as `\r\n` against the original; `strings.TrimSpace` |
| `try`/`except` around a parse | A checked `err` with `%w` wrapping, never `recover` |

### From JavaScript, TypeScript, Java, and Rust

- JavaScript `null`/`undefined` → `nil`; thrown errors → `error` values; plain objects →
  structs with a `New` constructor; JS `number` → `int64` or `float64`, chosen on purpose.
- Java class hierarchies → small interfaces + embedding; checked exceptions → `error`
  values; static utility classes → package-level functions; streams → slices and `range`
  loops.
- Rust `Result` → `error` values with sentinels or error structs; `Option` → `nil` or the
  comma-ok pattern; traits → interfaces; enums → typed constants (`iota`); borrow
  semantics → plain ownership (the GC does the borrow checker's job); `unsafe` → nothing
  in the port.

### From legacy Go

Modernizing old Go *is* a port: the behavior stays, the idioms move. While porting:

- `io/ioutil` (`ioutil.ReadFile`, `WriteFile`, `TempDir`) → `os.ReadFile`, `os.WriteFile`,
  `os.MkdirTemp`.
- `log`/`log.Printf` → `slog` (JSON handler on the facta stack); `interface{}` → `any`.
- `fmt.Errorf("failed: %s", err)` → `fmt.Errorf("failed: %w", err)`; error strings in
  switch → `errors.Is`/`errors.As`.
- `golang.org/x/net/context` → `context.Context` (stdlib since Go 1.7); the import path
  and the type name are the whole change.
- Goroutines coordinated by `time.Sleep` → an owner goroutine, `sync.WaitGroup`, and a
  `ctx.Done()` select for cancellation.
- Old `net/http` routing (manual method checks inside a prefix tree) → `http.ServeMux`
  method + wildcard patterns (`"POST /api/v1/items/{id}"`, `r.PathValue("id")`). Under
  the mandated backend-go stack those routes land on `chi` with the same method+wildcard
  pattern shape (`"POST /api/v1/items/{id}"`, read with `chi.URLParam(r, "id")`, or
  `r.PathValue` where the mux is stdlib `http.ServeMux`).
- Hand-rolled `min`/`max`/`clamp` helpers → the builtins (Go 1.21).
- Generics only where they remove real duplication; do not retrofit them.

## 4. Land it under the stack when the destination is a facta backend-go repo

The signs: `go.mod` plus `internal/features/` plus `.golangci.yml` with depguard rules.
Then the ported code obeys the architecture contract, restrictively:

- A port that touches HTTP or storage becomes a vertical slice: the six files
  (`domain.go`, `ports.go`, `usecase.go`, `http.go`, `postgres.go`, `module.go`), with
  `Register(r chi.Router, Deps)` as the only wiring seam.
- Pure domain: `domain.go` imports stdlib + `internal/shared` only — no `net/http`, no
  `database/sql`, no `pgx`, no `internal/gen`, no `internal/platform`.
- Ports are declared where consumed: the use case's `ports.go` declares the 1-2-method
  interfaces it needs; the adapter satisfies them implicitly. Never a port without a
  consumer.
- SQL lives in the slice's `queries.sql`; the migration that creates those tables ships
  in the same change as a golang-migrate migration with `Up` and `Down` sections (goose
  acceptable), applied by the deploy step.
- Adapters stay dumb: `http.go` decodes, validates at the edge, and writes the
  `{"detail","code"}` envelope only through `httpx`; `postgres.go` calls `gen/db`, maps
  rows inward, and translates errors with `%w`.
- **Infrastructure decisions land at the composition root.** `cmd/api/main.go` (or
  `cmd/worker`) builds the pool, adapters, and config, and injects them: the pool sits
  behind PgBouncer transaction pooling, the DI graph is generated by `google/wire`, and
  request DTOs are validated at the transport edge with `go-playground/validator`. A
  ported module never opens its own database, never builds its own `pgxpool`, never
  bypasses the wire-generated graph with manual constructor chains, and never reads its
  own env config at `init` time — config flows in as struct fields or ports from the
  root.
  Old Go code that read env at import time is exactly the habit this step breaks.
- `slog` only, never logged inside `domain.go`; log once at the boundary where context
  exists.
- A pure-algorithm port stays a leaf package with no stack obligations.
- When landing under the stack, read `references/backend-go-stack.md` in the
  `go-best-practices` skill first.

## 5. Keep the port proportionate

A port that matches the original on every possible input is usually the wrong goal.
Match it on the inputs it actually receives, and use Go's standard library for the rest.

- **Don't reimplement the source language's runtime.** Use `strconv`, `strings`, `time`,
  and `unicode`, not hand-written copies of `strtol`, Python's `splitlines`/`strip`, or
  C's `isspace`. Where Go's behavior differs only on exotic input, such as Unicode digits
  in `strconv`, `\x0b`-separated "lines", or unbounded integers, list the difference in
  the porting notes instead of coding around it. Write a compatibility shim only when the
  user says those inputs occur.
- **Don't grow the API.** Port the public surface the original has, plus what Go callers
  expect: `String()`, `Error()`, a count/len accessor, constructors (`New<Type>`), and
  sentinels. Skip option structs, builders, and custom iterator types unless the
  original's callers need them.
- **Keep the algorithm unless it's wrong.** Swap in a different algorithm only to fix a
  real problem, such as quadratic behavior on realistic input, and say so in the notes.
- **Check the size.** Count code lines, excluding tests, comments, and doc comments. A
  port from C or C++ usually lands near the original's size. A port from Python,
  JavaScript, TypeScript, or Java usually lands at two to three times the original,
  because types, error types, and struct definitions are explicit in Go. Much more than
  that usually means one of the three habits above.

Differential testing against the original is worth doing, but a few dozen realistic and
edge-case inputs answer the question. A fuzzing harness over millions of inputs usually
just finds exotic divergences that belong in the notes.

## 6. Verify

Run these if a Go toolchain is available, and fix everything before reporting:

```bash
go build ./...
go vet ./...
golangci-lint run
go test ./... -race
```

`golangci-lint run` uses the project's `.golangci.yml`; if the project has none, use the
beautifulgo `lints/.golangci.yml` drop-in. Every ported test must pass, and `go test
-race` is mandatory once the port brought goroutines. If the original's tests can be run
too, run them and compare results on the same inputs.

## 7. Write the porting notes

Alongside the code, write a short `PORTING.md` that a reviewer can check in a few
minutes:

- **API mapping:** a table from each original function or type to its Go equivalent.
- **Test mapping:** each original test and the Go test that covers it.
- **Deliberate differences:** anything that now behaves differently and why, such as
  `malloc` failure paths that no longer exist, a fixed buffer limit that's gone, map
  ordering made explicit, or exotic input where the Go standard library behaves
  differently from the original's.
- **Preserved quirks:** odd behavior kept on purpose, so nobody "fixes" it by accident.
- **Verification:** which commands you ran and their result, or a plain statement that
  you couldn't run them.

For the style of the Go itself, follow the `go-best-practices` skill if it is installed.
