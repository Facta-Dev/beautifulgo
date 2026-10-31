# Effective Go (digest)

Source: *Effective Go* (https://go.dev/doc/effective_go), the Go project's own
document of language idioms. Distilled from the published document; nothing
quoted verbatim. Read this when weighing how Go itself does it: interfaces,
embedding, methods, errors, maps and slices, concurrency flavor, naming — or
when a code review argues from "that's not Go-like". ~40 rules, paraphrased
faithfully, with a link back for the full text.

## Formatting and naming

1. **gofmt is the formatting spec.** Nobody argues about brace placement in Go;
   run `gofmt` (or `gofmt -s`) and merge tabs-vs-spaces debates out of reviews.
   Indentation is tabs, line length is whatever gofmt says.
2. **Package names are short, lowercase, mixed only by convention of the words
   they join.** `bufio`, `httputil`, `time`. No underscores, no camelCase
   package names. The name describes what it provides, not what it contains.
3. **Getters take no `Get` prefix.** `obj.Owner()`, not `obj.GetOwner()`.
   Setters may use `SetOwner`. Effective Go's own example; the wiki agrees.
4. **MixedCaps, always.** `MixedCase` exported, `mixedCase` unexported. Underscores
   in identifiers and SCREAMING_CASE constants both read as non-Go.
5. **Interface names are one-method verbs plus the -er suffix**: `Reader`,
   `Writer`, `Formatter`, `Clock`. Several methods: name the thing the set
   provides, not an -er.
6. **Error strings are lowercase, no trailing punctuation, no capitalized first
   word**, so they compose inside other messages: `errors.New("widget not
   found")`.

## Control flow and declarations

7. **`if` comes with its initialization statement.** `if err := f(); err != nil
   { return err }` scopes the error tightly and reads the guard with the call.
8. **Redeclaration with `:=` in the same scope adds a variable only when a new
   one appears on the left.** Handy for splitting `n, err := f()` into
   `n, err = g()`.
9. **`for` is the only loop.** `for i := range n` (Go 1.22+) for counting,
   `for k, v := range m` over maps, `range` over channels with `v, ok :=`.
10. **range always copies the value** (except pointer/iter-yield cases): if you
    mutate through the loop, index the slice or use `&v`.
11. **`switch` needs no break; `fallthrough` is explicit.** Type switches
    (`switch v := x.(type)`) are the idiomatic way to branch on dynamic type
    when you genuinely have an `any`.
12. **Labels and `goto` exist** for break/continue out of nested loops;
    `goto` is otherwise avoided.

## Functions and multiple returns

13. **Multiple return values replace out-parameters.** `(v, ok)` is the idiom:
    map lookup, type assertion, channel receive all share it. Name results only
    when they document meaning (`(size int, err error)`) or to enable naked
    returns in tiny functions — naked returns elsewhere are a smell.
14. **Defer schedules cleanup at function exit**, LIFO order. Use it for unlock,
    close, recover-style flushes. A deferred call's arguments evaluate at the
    defer site. Defer in a loop holds the file open until the function ends —
    close per iteration instead.
15. **Functions are values.** First-class function literals let handlers close
    over their setup; closures on loop variables (Go 1.22+ semantics: each
    iteration gets a fresh variable) are the standard per-item handler trick.

## Data: structs, slices, maps

16. **Embedding is composition, not inheritance.** A struct embedding a type
    delegates method calls to it. Embed for "has-a with forwarding", never to
    fake an "is-a"; the promoted methods still operate on the inner value.
17. **Make() allocates and initializes slices, maps, channels**; `new(T)` gives
    a zeroed `*T`. In practice: `make` for those three, composite literals
    otherwise.
18. **Slices carry an underlying array.** `append` reallocates when capacity is
    exhausted; two slices sharing an array alias mutations. A copy (`slices.Clone`)
    breaks aliasing when you need independent data.
19. **Maps are not ordered.** Iteration order varies run to run. Sorting keys
    before iterating is the standard deterministic-output move; the wiki and the
    Google style guide both make it a rule for printed or hashed output.
20. **The comma-ok idiom distinguishes a missing key from a zero value.**
    `v, ok := m[k]`; deleting is `delete(m, k)`.
21. **Initialize maps and slices with composite literals** where shape is part
    of the declaration; grow maps by assignment, never re-declare.
22. **Empty struct `struct{}` costs zero bytes** — the canonical set is
    `map[string]struct{}` or `map[K]bool` when memory matters; `struct{}{}`
    channel signals carry no payload.

## Methods, interfaces, and errors

23. **Pointer receivers mutate; value receivers copy.** Mixed receivers over one
    type are confusing — pick per type. Methods on a value type are in the
    method set of both `T` and `*T`; a pointer-receiver method exists only on
    `*T`. This decides what satisfies an interface.
24. **Interfaces are satisfied implicitly** — no `implements` clause, no
    registration. A type satisfies an interface by implementing its methods;
    small interfaces, declared where used, compose.
25. **"The bigger the interface, the weaker the abstraction."** One and two
    method interfaces (`io.Reader`, `fmt.Stringer`, `sort.Interface`) are the
    stdlib's shape; mirror it.
26. **Errors are values.** `error` is an interface with one method; the language
    gives you no exceptions, so guards read `if err != nil { return err }`. Add
    context with `fmt.Errorf("...: %w", err)` so `errors.Is/As` still work.
27. **`panic` is for invariant violations, not error handling.** Real panics in
    production code are bugs; expected failures are `error`.

## Concurrency flavor

28. **Do not communicate by sharing memory; share memory by communicating.**
    The channel-before-mutex heuristic comes from this document: pass values
    between goroutines; keep the data with one owner.
29. **A channel takes a direction in its type**: `chan<- int` send-only,
    `<-chan int` receive-only. Type your functions' channels with direction —
    it documents the protocol and the compiler enforces it.
30. **Buffered channels exist for bounding** work handed off, not for
    "performance"; unbuffered is the default and gives rendezvous semantics.
31. **`select` waits on several channel operations**; a `default` case makes it
    non-blocking. Timeouts come from `select` on a `time.After`/`ctx.Done()`
    case, not from polling.
32. **`sync` has its place**: `WaitGroup` for joins, `Mutex`/`RWMutex` for
    cached shared state. The document presents channels as the first choice and
    mutexes as the honest fallback when ownership transfer doesn't map.

## Where this document is dated

- It predates modules, generics, `slog`, and the modern error-wrapping verbs
  (`%w`); where it speaks of error handling it is describing the interface, not
  today's wrapping discipline — SKILL.md §5 and the wiki digest govern the
  current practice.
- Its `map[K]bool` advice predates Go 1.21's `maps` package; use
  `maps.Keys`/`slices` helpers before hand-rolling them.
- On package layout it shows the classic flat `src`-style tree; stack projects
  follow the backend-go topology instead (backend-go-stack.md), which SKILL.md
  §9 declares the winner for `internal/features/` repos.

Full text: https://go.dev/doc/effective_go