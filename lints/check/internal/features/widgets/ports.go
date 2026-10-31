// ports.go declares the ports where they are consumed: one interface per
// dependency, each with a plausible second implementation (postgres.go in
// production, fakes in tests).
package widgets

import (
	"context"
	"time"
)

// Store persists owner-scoped widgets.
type Store interface {
	Insert(ctx context.Context, w Widget) error
	Get(ctx context.Context, id, owner string) (Widget, bool, error)
}

// Now answers the clock question; a fake replaces it in usecase tests.
type Now interface {
	Time() time.Time
}
