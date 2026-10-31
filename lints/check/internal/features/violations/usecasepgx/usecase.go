// Package usecasepgx violates usecase-transport-free: pgx types belong to
// postgres.go, not the use case layer.
package usecasepgx

import "github.com/jackc/pgx/v5" // want depguard

// Fetcher holds the driver row type the use case must not know.
type Fetcher struct {
	Rows pgx.Rows
}
