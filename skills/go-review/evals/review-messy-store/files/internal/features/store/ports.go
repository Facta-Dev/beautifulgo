package store

import "context"

// OrderReader is the persistence port the use case needs. It is declared here,
// by the consumer, and satisfied implicitly by the pgx adapter.
type OrderReader interface {
	ByEmail(ctx context.Context, email string) ([]Order, error)
}

// MailQueue is the receipt-mail port; platform/email satisfies it.
type MailQueue interface {
	Enqueue(ctx context.Context, to string) error
}