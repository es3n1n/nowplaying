CREATE TABLE IF NOT EXISTS spotify_tokens
(
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    spotify_token VARCHAR
);
CREATE INDEX IF NOT EXISTS tg_idx ON spotify_tokens (telegram_id);

CREATE TABLE IF NOT EXISTS cached_files
(
    id SERIAL PRIMARY KEY,
    spotify_uri VARCHAR UNIQUE,
    file_id VARCHAR
);
CREATE INDEX IF NOT EXISTS spotify_uri ON cached_files (spotify_uri);
