// Package shared is the kernel stub: the shared vocabulary a domain may
// import. domain-pure allows exactly stdlib plus internal/shared, so the clean
// slice below imports this and nothing internal beyond it.
package shared

// MaxPerList is a page-size constant the kernel owns.
const MaxPerList = 50

// Clock is a shared type the kernel lends to any slice.
type Clock struct{}
