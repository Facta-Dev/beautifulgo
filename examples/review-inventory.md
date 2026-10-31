<!--
This review was produced by the go-review skill, unedited, for the deliberately
messy store slice in skills/go-review/evals/review-messy-store/files/. The
snapshot ships four files of the module (no internal/gen, no go.sum, no other
slices), so the agent could not compile or run gofmt, go vet, or
golangci-lint, and the report notes that it reviewed by reading.
-->

# Go review: the `store` slice

`store` is a vertical slice for customer orders: it validates orders, saves
them, lists a customer's orders by email, and queues the receipt mail through
an outbox-style `MailQueue` port. The module declares `go 1.27` and imports
pgx/v5, and the `internal/features/store/` layout with `domain.go`, `ports.go`,
`usecase.go`, and `postgres.go` means I reviewed it under the **stack mode** of
the architecture rules (hexagonal ports and adapters plus vertical slices) at
full strictness. **Verdict: not ready to build on.** The wiring needs work
before it goes near the composition root: the domain imports pgx, the use case
bypasses its own ports and reaches for the adapter, two errors are swallowed,
and the receipt-mail goroutine has no owner. **The most important fix:** make
the use case depend on the consumer-declared ports again, and route save and
count through them.

**Tools.** The snapshot is not compilable as shipped (it references
`internal/gen/db` without shipping it, and there is no `go.sum`), so
`gofmt -l`, `go vet ./...`, `golangci-lint run`, and `go test -race ./...` were
not run: the findings below are from reading, under stack rules. Line numbers
refer to the eval input files.

## Must fix

### 1. The domain imports pgx (`internal/features/store/domain.go:8, :26`)
**Rule:** dep: domain-pure (depguard in the stack's `.golangci.yml`; backend-go
handbook: the domain stays zero-I/O, adapters live in postgres.go)
**Problem:** `domain.go` imports `github.com/jackc/pgx/v5` so that `Order`
can carry a `pgx.TextArray` field (line 26, commented "handy for batch inserts
later"). The domain must import stdlib and `internal/shared` only; that one
convenience field couples the business rules to the database driver, makes
`domain.go` red under `dep: domain-pure` the moment the drop-in `.golangci.yml`
lands, and drags pgx's compile-time surface into every consumer of `Order`.
The field is also speculative — nothing reads it yet.
**Fix:**
```go
// domain.go — stdlib shape, driver shape stays in the adapter:
type Order struct {
	ID     ID
	Email  string
	Note   string
	Tags   []string
	Status Status
	Items  []Item
}
```
The adapter maps `pgx.TextArray` in one direction, in `postgres.go`.

### 2. The use case reaches for the adapter, not its ports
(`internal/features/store/usecase.go:10, :15, :28, :29, :34`)
**Rule:** backend-go handbook (ports are declared by the consumer; "depends on
the interface but reaches for the adapter"); Google Go Style Guide,
"Package Design": program to what the function needs
**Problem:** `Place` and `OrdersForEmail` take `*Store` — the concrete
pgx-backed struct from `postgres.go` — and call `s.InsertOrder`,
`s.CountByEmail`, and `s.ByEmail` directly. No port in `ports.go` declares
`InsertOrder` or `CountByEmail`, so the use case's actual dependencies are
invisible: unit tests can't fake them, and swapping the adapter touches the
use case. This is
the constructor-argument version of the architecture law that depguard cannot
see, because it is not an import.
**Fix:**
```go
// ports.go — declare what the use case actually needs:
type OrderWriter interface {
	InsertOrder(ctx context.Context, o Order) error
}

// usecase.go — signatures name behaviors, not mechanisms:
func Place(ctx context.Context, w OrderWriter, q MailQueue, o Order) (Order, error)

func OrdersForEmail(ctx context.Context, r OrderReader, email string, verbose bool) ([]Order, int, error)
```
(The bool goes away in finding 7; the port is satisfied implicitly, and
cmd/api keeps wiring the concrete `NewStore`.)

### 3. Two errors are swallowed (`usecase.go:34-35`, `postgres.go:57-58`)
**Rule:** Don't discard errors (Go wiki CodeReviewComments, "Handling errors";
golangci `errcheck`)
**Problem:** In `OrdersForEmail` the count request is fired with `_, err :=`,
the error only logged and the function keeps going with `len(orders)` in its
place (lines 34-36) — the caller receives a partial report presented as a
complete one. In `CountByEmail` the adapter's `if err != nil` branch returns
`0, nil` (lines 57-58) under a comment claiming "queries fail rarely; zero is
close enough". Together they guarantee the "verbose" report can be silently
wrong, and the two bugs mask each other.
**Fix:**
```go
// usecase.go, lines 33-37:
if verbose {
	count, err := s.CountByEmail(ctx, email)
	if err != nil {
		return nil, 0, fmt.Errorf("count orders for %q: %w", email, err)
	}
	return orders, count, nil
}
return orders, len(orders), nil

// postgres.go, lines 55-61:
func (s Store) CountByEmail(ctx context.Context, email string) (int, error) {
	n, err := s.q.CountOrdersByEmail(ctx, email)
	if err != nil {
		return 0, fmt.Errorf("count orders: %w", err)
	}
	return int(n), nil
}
```

### 4. The receipt-mail goroutine has no owner (`usecase.go:18-22`)
**Rule:** Every goroutine has an owner and a shutdown path (backend-go
handbook; Go wiki CodeReviewComments, "Goroutine lifetimes")
**Problem:** `Place` starts `go func()` with `context.Background()`, logs
failure with `log.Printf`, and returns while the goroutine races the process
shutting down — the mail request is lost silently on shutdown, and nothing
waits for or cancels it. The stack's answer is the outbox pattern: the mail
queue port enqueues a row and the outbox worker delivers it, so there is no
goroutine to own at the use-case layer at all.
**Fix:**
```go
// usecase.go, lines 18-23 — Enqueue is a durable row insert, not a send:
if err := q.Enqueue(ctx, o.Email); err != nil {
	return Order{}, fmt.Errorf("queue receipt mail: %w", err)
}
return o, nil
```

### 5. Sentinel wrapped with %s breaks errors.Is (`usecase.go:12`,
`postgres.go:31`)
**Rule:** Wrap errors with %w and match with errors.Is (Go wiki
CodeReviewComments; golangci `errorlint`; errname-adjacent convention)
**Problem:** Both failure paths wrap a sentinel with `%s`, which flattens the
wrapped value into the message string and makes the sentinel invisible to
every `errors.Is` upstream. The `%w`-wrap-and-`errors.Is`-match chain is the
stack's one error vocabulary; a caller keying on `store.ErrOrderNotFound`
after `fmt.Errorf("place order: %s", err)` gets nothing. The shape at line 30
of postgres.go is otherwise right — `errors.Is(err, pgx.ErrNoRows)` translated
into the domain sentinel at the adapter edge is exactly the template's
translation pattern; only the verb is wrong (`%s` instead of `%w`).
**Fix:**
```go
// usecase.go, line 12:
return Order{}, fmt.Errorf("place order: %w", err)

// postgres.go, line 31 — same translation, now still matchable:
return nil, fmt.Errorf("orders for %q: %w", email, ErrOrderNotFound)
```

## Should fix

### 6. `ByEmail` silently drops `Items` and `Tags`
(`internal/features/store/postgres.go:36, :65-72`)
**Rule:** Adapters are dumb: map rows to domain completely (backend-go
handbook); Don't silently drop data (Google Go Style Guide, "Go for
production" — error handling and data integrity)
**Problem:** `ByEmail` appends `toDomain(r)` for every row, but `toDomain`
maps only four fields; `Items` and `Tags` are never populated, so every
returned `Order` reports `Total() == 0` and no tags. Any caller trusting
`Total()` is silently wrong by the full line-item amount — a data-integrity
bug wearing an adapter's clothes.
**Fix:**
```go
// postgres.go — map everything the domain type carries, and extend the
// slice's queries.sql to load the line items in the same change:
func toDomain(r db.Order, items []db.OrderItem) Order {
	o := Order{
		ID:     ID(r.ID),
		Email:  r.Email,
		Note:   r.Note,
		Tags:   r.Tags,
		Status: Status(r.Status),
	}
	for _, it := range items {
		o.Items = append(o.Items, Item{SKU: it.SKU, Quantity: int(it.Quantity), UnitCents: it.UnitCents})
	}
	return o
}
```
(If line items live in another table, the join lands in the slice's
`queries.sql`, and its migration ships in the same change with a Down
section.)

### 7. The `verbose bool` parameter switches behavior at a distance
(`usecase.go:28`)
**Rule:** No boolean parameters that switch behavior (Google Go Style Guide,
"Decision: function and method signatures"; the go-best-practices rule against
bool parameters in shared signatures)
**Problem:** `OrdersForEmail(ctx, s, email, true)` doesn't say what `true`
buys the caller, and the second return value changes meaning behind it: it is
`len(orders)` in the non-verbose case and a full-table count in the verbose
case. Two behaviors, one signature.
**Fix:**
```go
// The pieces, plainly named — the caller composes them:
func OrdersForEmail(ctx context.Context, r OrderReader, email string) ([]Order, error)

func CountOrdersByEmail(ctx context.Context, r OrderReader, email string) (int, error)
```
(If a single call shape is genuinely convenient, take an options struct with
a named field; never a positional bool.)

### 8. `log.Print*` where slog is the one logging policy (`usecase.go:6`,
`:20`, `:35`)
**Rule:** Use slog (JSON handler) as the only logging dependency; log at the
boundary, never in the use case, and never log-and-continue (backend-go
handbook, observability doc; go-best-practices logging section)
**Problem:** `usecase.go` imports `log` and both `log.Printf` calls exist to
silence errors the function should have returned (findings 3 and 4 remove
them both). What remains is the policy point: stack code logs with structured
`slog` at the boundary where context exists (the handler or the worker loop,
with `request_id`), not with `log.Printf` inside a use case.
**Fix:**
```go
// Use cases return errors; boundaries log once, with the request context:
import "log/slog"

slog.WarnContext(ctx, "order lookup slow", "email", email, "err", err)
```

### 9. No tests on any of the four files (`whole slice`)
**Rule:** Test logic; table-driven tests with named fields (Effective Go,
"Tests"; go-best-practices testing section)
**Problem:** Nothing is tested, and the domain's `Validate` is exactly where
tests pay off first: the empty-cart and note-length rules are the invariants
callers lean on, and finding 3's swallow would have been caught by a test
that asks for the count and checks the error path.
**Fix:**
```go
func TestOrderValidate(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name  string
		order Order
		want  error
	}{
		{name: "empty cart rejected", order: Order{}, want: ErrEmptyCart},
		{name: "note too long rejected",
			order: Order{Items: []Item{{SKU: "A", Quantity: 1}},
				Note: strings.Repeat("x", 501)},
			want: ErrNoteTooLong},
		{name: "valid order passes",
			order: Order{Items: []Item{{SKU: "A", Quantity: 1}}}, want: nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if err := tt.order.Validate(); !errors.Is(err, tt.want) {
				t.Errorf("Validate() = %v, want %v", err, tt.want)
			}
		})
	}
}
```
(An in-memory fake of the two one-method ports is about ten lines each —
no mock framework.)

## Consider

### 10. `Store` keeps a `pool` field it never uses (`postgres.go:16-19`)
**Rule:** No fields without a consumer (YAGNI; Google Go Style Guide, package
design)
**Problem:** `Store.pool` is set in `NewStore` and never read — the adapter
only uses `q`. It reads like a future transaction handle, but speculative
state on a struct is the same "declared for the future" smell as a port with
no consumer.
**Fix:** drop the field until a method needs the pool, then take it as a
narrow transaction port rather than raw `*pgxpool.Pool`.

### 11. Speculative fields and self-incriminating comments
(`domain.go:26`, `postgres.go:58`)
**Rule:** Don't declare things "for the future" (backend-go handbook,
GoYAGNI)
**Problem:** The `Tags pgx.TextArray` comment says "handy for batch inserts
later" (domain.go:26) and the swallow in `CountByEmail` is documented with
"queries fail rarely; zero is close enough" (postgres.go:58). A comment that
explains away a rule violation is a smell the reader tripped over, not a
design note.
**Fix:** the tags fix is finding 1 (plain `[]string`); remove the
"close enough" comment together with the fix in finding 3.

## What's already good

- `ports.go` declares two consumer-defined, one-method ports (lines 5-9,
  11-14): the right shape for the stack — narrow, named by the consumer, and
  satisfied implicitly by the adapter.
- The adapter's error translation at `postgres.go:30-33` is the template's
  pattern: `errors.Is(err, pgx.ErrNoRows)` mapped inward to the domain
  sentinel `ErrOrderNotFound` (only the `%w` verb needs fixing, finding 5).
- The domain keeps its invariants in one place (`Validate`, domain.go:57-66)
  and its sentinels use the `Err*` naming convention with package-scoped
  messages (domain.go:41-46).
- `Status` has a usable zero value (`StatusDraft == 0`), and every exported
  item has a doc comment.

## Suggested lints

This module has no `.golangci.yml` in the snapshot. Adding the beautifulgo
drop-in (`lints/.golangci.yml`) would have caught, automatically:

- both swallowed errors (the `_, err :=` drop in `OrdersForEmail` and the
  `0, nil` return in `CountByEmail`) via `errcheck`,
- the `%s` wraps at `usecase.go:12` and `postgres.go:31` via `errorlint`,
- the pgx import in `domain.go` via the depguard `domain-pure` rule, and
- the `context.Background()` inside `Place`, which has a `ctx` in hand, via
  `contextcheck`.

Two of the architecture findings (the adapter reach in the use case and the
missing `Items` in `toDomain`) are review-level — depguard sees imports, not
signatures or row mappings — which is why the linter and this review run
together.
