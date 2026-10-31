// Package widgets: ports. Consumer-defined interfaces the use case needs.
package widgets

import "context"

// WidgetStore is the persistence seam the use cases consume. The
// postgres.go adapter satisfies it implicitly.
type WidgetStore interface {
	ByID(ctx context.Context, id WidgetID) (Widget, error)
	Save(ctx context.Context, w Widget) error
	ListBySize(ctx context.Context, size Size) ([]Widget, error)
}