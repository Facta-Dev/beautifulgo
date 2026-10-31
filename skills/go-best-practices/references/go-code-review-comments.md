# Go Code Review Comments (digest)

Source: the Go wiki page *Code Review Comments*
(https://go.dev/wiki/CodeReviewComments), the checklist reviewers quote by name.
Distilled from the published wiki; nothing quoted verbatim. Read this when
reviewing or before opening a PR — it is the list of comments Go reviewers post
over and over, each with the exact linting consequence. ~25 rules, paraphrased
faithfully, with a link back.

## Error handling

1. **Wrap errors with `%w`, match with `errors.Is`/`errors.As`.** `fmt.Errorf`
   with `%s` or `%v` for an `error` argument loses the chain; a bare `==` on an
   error or a one-way type cast breaks wrapped causes. errorlint encodes both
   halves of this rule.
2. **Don't panic on ordinary failures.** `panic` for unrecoverable programmer
   error; `error` for expected failures. Libraries should be especially paranoid
   about panicking.
3. **Error strings go lowercase, no punctuation at the end**, both when you
   create them (`errors.New`) and when you wrap (`fmt.Errorf`).
4. **Check every error you care about; don't discard with `_`.** For `Close` on
   writes and flushes, handle or log it; errcheck flags the discarded ones.
5. **Don't check `err != nil` just to re-wrap identically** — add context or
   return as-is; never both log AND return the same error.

## Concurrency

6. **Goroutine lifetimes must be clear.** Every `go` statement needs an answer
   to "when does it end, and who observes its error?" If it depends on another
   goroutine's progress, that must be explicit (channel, WaitGroup, context).
7. **Never start a goroutine without a plan to stop it.** Fire-and-forget
   goroutines in servers accumulate until the process dies. The wiki's exact
   smell: "if the goroutine's lifetime is not obvious, document it or block until
   it can no longer run".
8. **Copy locks by pointer only.** A type holding a `sync.Mutex` gets pointer
   receivers and travels by `*T`; vet's `copylocks` catches copies.
9. **Sync package usage**: prefer channels for ownership transfer, `sync.Mutex`
   for state, `sync.WaitGroup` for waiting on groups; don't hand-roll worker
   pools over raw channels when WaitGroup + jobs channel says it directly.

## Naming and imports

10. **Initialisms keep constant case: `URL`, `ID`, `HTTP`, `XML`, `API`** —
    `urlString`, not `uRLString`; `ServeHTTP`, `widgetID`.
11. **No stutter between package and identifier**: `bytes.Buffer`, not
    `bytes.ByteBuffer`; `chunk.Reader`, not `chunk.ChunkReader`. Rename on
    import rather than mangling names.
12. **Import as `_` only to register side effects** (`image/png` codecs, database
    drivers), with a comment naming why; dot-imports are effectively banned.
13. **Import grouping**: stdlib, then third-party, then your own module — blank
    line between groups. gofmt's older `-local` flag and every linter's
    import-ordering rule agree.

## Functions and parameters

14. **Don't send a bool to switch modes** — same as SKILL.md §4: two methods or
    an enum-like type; a naked `func(frob(x, true))` caller is unreadable.
15. **Naked parameters in calls to functions with many same-typed args** get
    inline comments at the call site for the truly ambiguous ones; better, split
    or name via struct.
16. **Use `any` in new code** rather than `interface{}`; they are identical, the
    short one is current style. Don't mix in the same API.

## Types and data

17. **Package `testing`'s `TestMain`** is for suite-level setup/teardown, not
    per-test; prefer `Test*` with `t.Cleanup` where possible.
18. **Zero-value structs are usable** — design so `var x T` works; sync types,
    bytes.Buffer, time.Time set the example. Pointer receivers that check
    `== nil` on the receiver are a smell.
19. **Copy structs deliberately**: `slices.Clone`, explicit assignment over
    aliasing slices/maps; maps returned from getters hand the caller a live
    reference — return a copy or a read-only view.
20. **`string(int)` conversion is virtually never what you want** (rune vs digit
    confusion); use `string(rune(i))` for the character or `strconv.Itoa`.
21. **JSON and struct tags**: exported fields only marshal; use tags for names;
    time fields as `time.Time`; embedded structs marshal by promotion — design
    wire structs explicitly rather than sharing domain structs at the edge.

## API shape

22. **Interfaces belong to the consumer**, not the implementer — the wiki's
    classic line: "Go interfaces belong on the client side" don't pre-define
    interfaces on the same side as their single implementation. Mirrors
    SKILL.md §4 and the hexagonal ports rule.
23. **Don't use `init()` for things callers can do**; constructors and explicit
    setup beat hidden global mutation. Prefer registering with the caller.
24. **Don't define methods on primitive-ish types you don't own** (a `type
    MyInt int` with methods is usually fine but rarely a bridge — weigh it
    against just using functions).
25. **Doc comments start with the identifier's name**: `// ParseCode converts ...`
    for `func ParseCode`; a complete sentence. godoc reads them as prose.

## Where the wiki and other digests disagree

- The wiki's "interfaces belong to the consumer" is the general rule; the
  backend-go handbook makes it absolute inside `internal/features/` (every port
  lives in `ports.go`) — stack projects follow the handbook, non-stack Go
  follows the wiki's softer version.
- The wiki is fine with `interface{}` in older code; the Google style guide and
  Go 1.18+ style prefer `any`. This skill says `any`.
- The wiki historically said "check error values in if-statements directly";
  modern linters allow both shapes — pick the project's and be consistent.

Full text: https://go.dev/wiki/CodeReviewComments