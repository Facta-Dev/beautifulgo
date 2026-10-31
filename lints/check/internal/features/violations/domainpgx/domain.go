// Package domainpgx violates domain purity: the pgx driver type reaches into a
// domain struct, the classic leak the domain-pure rule exists to stop.
package domainpgx

import "github.com/jackc/pgx/v5" // want depguard

// Row is a domain shape carrying the driver's row type.
type Row struct {
	Marker pgx.Rows
}

var _ pgx.Rows = nil
