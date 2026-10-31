---
type: llm
focus: trace
weight: 1
---

Number parsing uses strconv (Atoi or ParseInt with errors.Is for strconv.ErrRange) and
string trimming uses strings.TrimSpace or similar, rather than hand-written copies of
strtol or isspace
