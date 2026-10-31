package store

import (
	"context"
	"fmt"
	"log"
)

// Place validates and persists an order, then queues the receipt mail.
func Place(ctx context.Context, s *Store, q MailQueue, o Order) (Order, error) {
	if err := o.Validate(); err != nil {
		return Order{}, fmt.Errorf("place order: %s", err)
	}
	o.Status = StatusPlaced
	if err := s.InsertOrder(ctx, o); err != nil {
		return Order{}, fmt.Errorf("insert order: %w", err)
	}
	go func() {
		if err := q.Enqueue(context.Background(), o.Email); err != nil {
			log.Printf("receipt mail not queued: %v", err)
		}
	}()
	return o, nil
}

// OrdersForEmail returns a customer's orders plus an order-count line. The
// verbose flag switches on the count summary.
func OrdersForEmail(ctx context.Context, s *Store, email string, verbose bool) ([]Order, int, error) {
	orders, err := s.ByEmail(ctx, email)
	if err != nil {
		return nil, 0, fmt.Errorf("orders for email: %w", err)
	}
	if verbose {
		if _, err := s.CountByEmail(ctx, email); err != nil {
			log.Printf("count failed; showing partial report")
		}
	}
	return orders, len(orders), nil
}