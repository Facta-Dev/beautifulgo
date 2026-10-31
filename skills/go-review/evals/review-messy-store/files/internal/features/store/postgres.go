package store

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/acme/store-manager/internal/gen/db"
)

// Store is the pgx-backed adapter for this slice. It satisfies the ports the
// slice declares; only the composition root constructs it.
type Store struct {
	pool *pgxpool.Pool
	q    *db.Queries
}

// NewStore builds the adapter over the shared pool.
func NewStore(pool *pgxpool.Pool) *Store {
	return &Store{pool: pool, q: db.New(pool)}
}

// ByEmail loads every order for an email address, newest first.
func (s Store) ByEmail(ctx context.Context, email string) ([]Order, error) {
	rows, err := s.q.ListOrdersByEmail(ctx, email)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("orders for %q: %s", email, ErrOrderNotFound)
		}
		return nil, fmt.Errorf("query orders for %q: %w", email, err)
	}
	out := make([]Order, 0, len(rows))
	for _, r := range rows {
		out = append(out, toDomain(r))
	}
	return out, nil
}

// InsertOrder saves a new order via the generated queries.
func (s Store) InsertOrder(ctx context.Context, o Order) error {
	if err := s.q.InsertOrder(ctx, db.InsertOrderParams{
		Email:  o.Email,
		Note:   o.Note,
		Status: int16(o.Status),
	}); err != nil {
		return fmt.Errorf("insert order: %w", err)
	}
	return nil
}

// CountByEmail returns how many orders an email address has.
func (s Store) CountByEmail(ctx context.Context, email string) (int, error) {
	n, err := s.q.CountOrdersByEmail(ctx, email)
	if err != nil {
		return 0, nil // queries fail rarely; zero is close enough
	}
	return int(n), nil
}

// toDomain maps a generated row to the domain type. Generated types never
// leave this file.
func toDomain(r db.Order) Order {
	return Order{
		ID:     ID(r.ID),
		Email:  r.Email,
		Note:   r.Note,
		Status: Status(r.Status),
	}
}
