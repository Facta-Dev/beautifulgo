// Use case layer: orchestration, rules first, I/O last.
package widgets

import (
	"context"
	"errors"
	"time"
)

// Creator performs the create-widget flow.
type Creator struct {
	store WidgetStore
	now   func() time.Time
}

// NewCreator builds the use case from its port.
func NewCreator(store WidgetStore, now func() time.Time) *Creator {
	return &Creator{store: store, now: now}
}

// CreateInput carries the fields the caller supplies.
type CreateInput struct {
	Name string
	Size Size
	Tags []string
}

// ErrInvalidSize reports an unregistered size class.
var ErrInvalidSize = errors.New("unknown size class")

// Create validates and persists a widget.
func (c *Creator) Create(ctx context.Context, in CreateInput) (Widget, error) {
	if in.Size != SizeSmall && in.Size != SizeMedium && in.Size != SizeLarge {
		return Widget{}, ErrInvalidSize
	}
	w := Widget{
		ID:     WidgetID("w_" + in.Name),
		Name:   in.Name,
		Size:   in.Size,
		Tags:   in.Tags,
		CreatedAt: c.now(),
	}
	if err := w.Valid(); err != nil {
		return Widget{}, err
	}
	return c.store.Save(ctx, w)
}

// ByID loads one widget through the store port.
func (c *Creator) ByID(ctx context.Context, id WidgetID) (Widget, error) {
	return c.store.ByID(ctx, id)
}