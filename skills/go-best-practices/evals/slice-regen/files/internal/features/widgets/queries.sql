-- widgets slice queries (sqlc source; schema pointed at migrations/)
-- name: GetWidget :one
SELECT id, name, size, tags, created_at FROM widgets WHERE id = $1;

-- name: InsertWidget :exec
INSERT INTO widgets (id, name, size, tags, created_at)
VALUES ($1, $2, $3, $4, $5);

-- name: ListWidgetsBySize :many
SELECT id, name, size, tags, created_at FROM widgets WHERE size = $1 ORDER BY created_at;