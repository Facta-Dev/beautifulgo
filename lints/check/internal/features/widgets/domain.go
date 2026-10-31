// Package widgets is the clean reference slice: a correct six-file-shaped
// feature that must lint with zero findings under the drop-in config, proving
// the rules never fire on the shape the skills teach.
package widgets

import (
	"errors"
	"time"

	"github.com/beautifulgo/check/internal/shared"
)

// Widget is one owned row.
type Widget struct {
	ID          string
	Name        string
	OwnerUserID string
	CreatedAt   time.Time
}

// MaxPerList reads the one shared kernel constant the domain may know.
const MaxPerList = shared.MaxPerList

// ErrNotFound and ErrValidation are the sentinels callers match with
// errors.Is; adapters never invent codes.
var (
	ErrNotFound   = errors.New("widget not found")
	ErrValidation = errors.New("invalid widget")
)
