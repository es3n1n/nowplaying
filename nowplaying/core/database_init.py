# TODO(es3n1n): this is rather a temporary measure. not sure where to put this yet, sorry
DATABASE_INIT_SQL: str = """
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    platform_name VARCHAR,
    url VARCHAR,
    artist VARCHAR,
    name VARCHAR,
    UNIQUE (platform_name, url)
);
CREATE INDEX IF NOT EXISTS local_track_idx ON local_tracks (platform_name, url);

CREATE TABLE IF NOT EXISTS cached_song_link_urls
(
    song_url VARCHAR(512) PRIMARY KEY,
    song_link TEXT NOT NULL
);

CREATE OR REPLACE FUNCTION cache_local_track_id(
    p_platform_name VARCHAR,
    p_url VARCHAR,
    p_artist VARCHAR,
    p_name VARCHAR
)
RETURNS TABLE (
    result_id UUID,
    inserted BOOLEAN
) AS $$
BEGIN
    -- Attempt to insert a new track
    INSERT INTO local_tracks (platform_name, url, artist, name)
    VALUES (p_platform_name, p_url, p_artist, p_name)
    ON CONFLICT (platform_name, url) DO NOTHING
    RETURNING id, TRUE INTO result_id, inserted;

    -- Fetch the existing ID if failed
    IF result_id IS NULL THEN
        SELECT id, FALSE INTO result_id, inserted
        FROM local_tracks
        WHERE platform_name = p_platform_name
        AND url = p_url
        LIMIT 1;
    END IF;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
"""
