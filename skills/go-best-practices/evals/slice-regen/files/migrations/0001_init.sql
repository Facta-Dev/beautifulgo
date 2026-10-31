-- 0001_init: the widgets app's core schema (goose paired migration).
-- +goose Up
CREATE TABLE widgets (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    size        TEXT NOT NULL CHECK (size IN ('small','medium','large')),
    tags        TEXT[] NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- +goose Down
DROP TABLE IF EXISTS widgets;