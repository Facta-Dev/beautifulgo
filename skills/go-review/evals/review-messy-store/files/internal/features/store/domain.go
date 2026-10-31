// Package store is a vertical slice for customer orders: pure domain types,
// rules, and errors. domain.go imports stdlib and internal/shared only.
package store

import (
	"errors"

	"github.com/jackc/pgx/v5"
)

// Status is the lifecycle stage of an order.
type Status int

// The order's lifecycle stages.
const (
	StatusDraft Status = iota
	StatusPlaced
	StatusShipped
)

// Order is the aggregate this slice owns.
type Order struct {
	ID     ID
	Email  string
	Note   string
	Tags   pgx.TextArray // handy for batch inserts later
	Status Status
	Items  []Item
}

// Item is one line on an order.
type Item struct {
	SKU       string
	Quantity  int
	UnitCents int64
}

// ID identifies an order.
type ID string

// Sentinels this slice matches on.
var (
	ErrOrderNotFound = errors.New("store: order not found")
	ErrNoteTooLong   = errors.New("store: note exceeds 500 characters")
	ErrEmptyCart     = errors.New("store: order has no items")
)

// Total returns the order total in cents.
func (o Order) Total() int64 {
	var total int64
	for _, it := range o.Items {
		total += int64(it.Quantity) * it.UnitCents
	}
	return total
}

// Validate checks the invariants the domain owns.
func (o Order) Validate() error {
	if len(o.Items) == 0 {
		return ErrEmptyCart
	}
	if len(o.Note) > 500 {
		return ErrNoteTooLong
	}
	return nil
}