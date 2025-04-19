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
    uri VARCHAR UNIQUE NOT NULL,
    file_id VARCHAR NOT NULL,
    cached_by_user_id BIGINT
);
CREATE INDEX IF NOT EXISTS our_uri ON cached_files (uri);
CREATE INDEX IF NOT EXISTS cached_by_user ON cached_files (cached_by_user_id);

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

CREATE TABLE IF NOT EXISTS user_track_stats
(
    user_id BIGINT PRIMARY KEY,
    track_count INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_configs
(
    user_id BIGINT PRIMARY KEY UNIQUE NOT NULL,
    stats_opt_out BOOLEAN DEFAULT FALSE
);

CREATE OR REPLACE FUNCTION update_user_config_value(
    p_user_id BIGINT,
    field_name TEXT,
    field_value BOOLEAN
) RETURNS VOID AS $$
BEGIN
    -- Check if the user exists in the user_configs table
    IF NOT EXISTS (SELECT 1 FROM user_configs WHERE user_id = p_user_id) THEN
        -- Insert a new row if the user does not exist
        INSERT INTO user_configs (user_id)
        VALUES (p_user_id);
    END IF;

    -- Update the specified field for the user
    EXECUTE format('UPDATE user_configs SET %I = $1 WHERE user_id = $2', field_name)
    USING field_value, p_user_id;
END;
$$ LANGUAGE plpgsql;

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
