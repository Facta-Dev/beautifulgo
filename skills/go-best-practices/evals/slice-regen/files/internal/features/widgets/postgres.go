// Postgres adapter over the slice's sqlc-generated queries.
package widgets

import (
	"context"
	"errors"
	"fmt"

	"github.com/example/widgetsapp/internal/gen/db"
)

// Store is the pgx-backed adapter satisfying WidgetStore. Built once at the
// composition root.
type Store struct {
	q *db.Queries
}

// NewStore builds the adapter over the committed gen/db output.
func NewStore(q *db.Queries) *Store { return &Store{q: q} }

// ByID loads one widget and maps the row to the domain type, translating the
// driver error inward. db.ErrNotFound is the sqlc sentinel; map errors inward,
// never outward.
func (s *Store) ByID(ctx context.Context, id WidgetID) (Widget, error) {
	row, err := s.q.GetWidget(ctx, id)
	if errors.Is(err, db.ErrNotFound) {
		return Widget{}, ErrWidgetMissing
	}
	if err != nil {
		return Widget{}, fmt.Errorf("get widget: %w", err)
	}
	return toDomain(row), nil
}

// Save persists a widget through the slice's queries.
func (s *Store) Save(ctx context.Context, w Widget) error {
	if err := s.q.InsertWidget(ctx, db.InsertWidgetParams{
		ID:        w.ID,
		Name:      w.Name,
		Size:      w.Size,
		Tags:      w.Tags,
		CreatedAt: w.CreatedAt,
	}); err != nil {
		return fmt.Errorf("save widget: %w", err)
	}
	return nil
}

// ListBySize returns widgets of one size class.
func (s *Store) ListBySize(ctx context.Context, size Size) ([]Widget, error) {
	rows, err := s.q.ListWidgetsBySize(ctx, db.ListWidgetsBySizeParams{Size: size})
	if err != nil {
		return nil, fmt.Errorf("list widgets by size: %w", err)
	}
	out := make([]Widget, 0, len(rows))
	for _, r := range rows {
		out = append(out, toDomain(r))
	}
	return out, nil
}

// toDomain maps a gen/db row to the domain type, one direction per file.
func toDomain(r db.Widget) Widget {
	return Widget{
		ID:     r.ID,
		Name:   r.Name,
		Size:   r.Size,
		Tags:   r.Tags,
		CreatedAt: r.CreatedAt,
	}
}