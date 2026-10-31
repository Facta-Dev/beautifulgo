// Package domainsql violates domain purity with the sql driver package.
package domainsql

import "database/sql" // want depguard

// NullString aliases the driver's nullable string into the domain.
type NullString = sql.NullString
