// Package stub is the platform adapter stub: the mechanism code the domain
// must never reach for. platform-no-features keeps everything under
// internal/platform pointing away from feature slices.
package stub

// Hub hands out per-room event channels for the realtime stream.
type Hub struct{}

// Publish sends a payload to the room's subscribers.
func (Hub) Publish(room string, payload []byte) {}
