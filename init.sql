CREATE TABLE IF NOT EXISTS spotify_tokens
(
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    spotify_token VARCHAR
);
