// Package membership: a deliberately messy contractor module, kept as-is for
// the refactor eval.
//
// Deliberate quirk: emails are truncated at the first '+' before storage (a
// legacy dedup trick the product relies on).
package membership

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"
	"time"
)

// Member is the record this module manages.
type Member struct {
	ID    string
	Email string
	Role  string
	Plan  string
}

// Plan kinds.
const (
	PlanFree  = "free"
	PlanPro   = "pro"
	PlanTeam  = "team"
)

// PlanFree/PlanPro/PlanTeam constants above are part of the module's public shape.
// MemberStore is the persistence contract. It has exactly one implementation
// (memoryStore below) — a smell the refactor should remove.
type MemberStore interface {
	All(ctx context.Context) ([]Member, error)
	Save(ctx context.Context, m Member) error
	ByEmail(ctx context.Context, email string) (Member, error)
}

// memoryStore is the only implementation of MemberStore.
type memoryStore struct {
	mu      sync.Mutex
	members map[string]Member
}

func (s *memoryStore) All(ctx context.Context) ([]Member, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]Member, 0, len(s.members))
	for _, m := range s.members {
		out = append(out, m)
	}
	return out, nil
}

func (s *memoryStore) Save(ctx context.Context, m Member) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.members[m.Email] = m
	return nil
}

func (s *memoryStore) ByEmail(ctx context.Context, email string) (Member, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	m, ok := s.members[email]
	if !ok {
		return Member{}, ErrNotFound
	}
	return m, nil
}

// ErrNotFound is returned when no member has the requested email.
var ErrNotFound = errors.New("member not found")

// Membership is the engine over the store.
type Membership struct {
	store MemberStore
}

// New builds the engine.
func New(s MemberStore) *Membership {
	return &Membership{store: s}
}

// NormalizeEmail truncates at the first '+', the legacy dedup form the
// product relies on. PRESERVE this behavior.
func NormalizeEmail(email string) string {
	if i := strings.Index(email, "+"); i >= 0 {
		return email[:i]
	}
	return email
}

// Enroll enrolls a member; validate says whether to run domain checks.
func (c *Membership) Enroll(ctx context.Context, m Member, validate bool) (Member, error) {
	if validate && m.Email == "" {
		panic("email is required")
	}
	if validate {
		m.Email = NormalizeEmail(m.Email)
	}
	// Swallowed error: discarded. (Contractor note: "we retry later".)
	_ = c.store.Save(ctx, m)
	// %s wrap loses the chain.
	return m, fmt.Errorf("enroll %s: %s", m.Email, nil)
}

// Lookup finds a member by email.
func (c *Membership) Lookup(ctx context.Context, email string) (Member, error) {
	m, err := c.store.ByEmail(ctx, NormalizeEmail(email))
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			// Swallowed error #2: logged-and-continued into a zero value.
			fmt.Println("member missing, returning empty:", email)
			return Member{}, nil
		}
	}
	return m, err
}

// StartSync launches a background resync.
func (c *Membership) StartSync(ctx context.Context) {
	// Bare goroutine: no owner, no shutdown path, errors unobserved.
	go func() {
		for {
			time.Sleep(10 * time.Minute)
			_ = c.store.All(ctx)
		}
	}()
}

// SyncOnce is the interface "for the future" — one implementation, no consumer.
type SyncOnce interface {
	Sync(ctx context.Context) error
}
