// Package widgets implements the widgets vertical slice: domain, ports, use
// cases, and adapters for widgets.
package widgets

import (
	"errors"
	"time"
)

// WidgetID identifies a widget across services and storage.
type WidgetID string

// Size is a widget's physical size class.
type Size string

// Widget sizes.
const (
	SizeSmall  Size = "small"
	SizeMedium Size = "medium"
	SizeLarge  Size = "large"
)

// ErrWidgetMissing is returned when no widget has the requested ID.
var ErrWidgetMissing = errors.New("widget not found")

// ErrNameRequired is returned when a widget has no name.
var ErrNameRequired = errors.New("widget name is required")

// ErrSizeRequired is returned when a widget has no size class.
var ErrSizeRequired = errors.New("widget size is required")

// Widget is the slice's aggregate. The zero value is a valid empty widget.
type Widget struct {
	ID        WidgetID
	Name      string
	Size      Size
	Tags      []string
	CreatedAt time.Time
}

// Valid reports whether the widget satisfies the domain's invariants.
func (w Widget) Valid() error {
	if w.Name == "" {
		return ErrNameRequired
	}
	if w.Size == "" {
		return ErrSizeRequired
	}
	return nil
}