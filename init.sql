CREATE TABLE IF NOT EXISTS tokens
(
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT,
    platform_name VARCHAR,
    token VARCHAR,
    UNIQUE (telegram_id, platform_name)
);
CREATE INDEX IF NOT EXISTS tg_idx_platform ON tokens (telegram_id, platform_name);

CREATE TABLE IF NOT EXISTS cached_files
(
    id SERIAL PRIMARY KEY,
    uri VARCHAR UNIQUE,
    file_id VARCHAR
);
CREATE INDEX IF NOT EXISTS our_uri ON cached_files (uri);
