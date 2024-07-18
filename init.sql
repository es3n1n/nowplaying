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

CREATE TABLE IF NOT EXISTS local_tracks
(
    id VARCHAR,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    platform_name VARCHAR,
    url VARCHAR,
    artist VARCHAR,
    name VARCHAR,
    PRIMARY KEY (id, platform_name),
    UNIQUE (platform_name, url)
);
CREATE INDEX IF NOT EXISTS local_track_idx ON local_tracks (platform_name, url);

CREATE OR REPLACE FUNCTION cache_local_track_id(
    p_id VARCHAR,
    p_platform_name VARCHAR,
    p_url VARCHAR,
    p_artist VARCHAR,
    p_name VARCHAR
)
RETURNS TABLE (
    result_id VARCHAR,
    inserted BOOLEAN
) AS $$
DECLARE
    v_id VARCHAR;
BEGIN
    -- Generate UUID if p_id is NULL
    v_id := COALESCE(p_id, gen_random_uuid()::VARCHAR);

    -- Attempt to insert a new track
    INSERT INTO local_tracks (id, platform_name, url, artist, name)
    VALUES (v_id, p_platform_name, p_url, p_artist, p_name)
    ON CONFLICT (platform_name, url) DO UPDATE
    SET id = EXCLUDED.id,
        artist = EXCLUDED.artist,
        name = EXCLUDED.name
    RETURNING id, (xmax = 0) AS inserted INTO result_id, inserted;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
