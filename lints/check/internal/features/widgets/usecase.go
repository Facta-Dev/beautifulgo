// usecase.go consumes the ports from ports.go and returns error values only:
// no mechanism types, no logging, no envelope.
package widgets

import (
	"context"
	"fmt"
)

// UseCase runs the widget flow against the ports.
type UseCase struct {
	store Store
	now   Now
}

// New wires the use case with its ports; nothing here names a mechanism.
func New(store Store, now Now) *UseCase {
	return &UseCase{store: store, now: now}
}

// Get fetches one owned widget, wrapping store failures with %w.
func (uc *UseCase) Get(ctx context.Context, id, owner string) (Widget, error) {
	w, found, err := uc.store.Get(ctx, id, owner)
	if err != nil {
		return Widget{}, fmt.Errorf("get widget %s: %w", id, err)
	}
	if !found {
		return Widget{}, ErrNotFound
	}
	return w, nil
}

// Create inserts a widget stamped by the clock port.
func (uc *UseCase) Create(ctx context.Context, owner, name string) (Widget, error) {
	if name == "" {
		return Widget{}, ErrValidation
	}
	stamp := uc.now.Time()
	w := Widget{
		ID:          fmt.Sprintf("w_%d", stamp.UnixNano()),
		Name:        name,
		OwnerUserID: owner,
		CreatedAt:   stamp,
	}
	if err := uc.store.Insert(ctx, w); err != nil {
		return Widget{}, fmt.Errorf("insert widget: %w", err)
	}
	return w, nil
}
