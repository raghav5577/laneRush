-- LaneRush Postgres schema
-- Apply with: psql $PG_DSN -f schema.sql

CREATE TABLE IF NOT EXISTS tls_state (
    tls_id TEXT PRIMARY KEY,
    data   JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lane_samples (
    id          BIGSERIAL PRIMARY KEY,
    run_id      TEXT NOT NULL,
    t           INT  NOT NULL,
    lane_id     TEXT NOT NULL,
    count       INT  NOT NULL,
    halting     INT  NOT NULL,
    max_wait    FLOAT NOT NULL,
    emergency   BOOLEAN NOT NULL,
    source      TEXT NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lane_samples_run_t ON lane_samples (run_id, t);

CREATE TABLE IF NOT EXISTS decisions (
    id          BIGSERIAL PRIMARY KEY,
    run_id      TEXT NOT NULL,
    t           INT  NOT NULL,
    tls_id      TEXT NOT NULL,
    action      TEXT NOT NULL,
    target_phase INT,
    reason      TEXT NOT NULL,
    scores_json JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS decisions_run_t ON decisions (run_id, t);

CREATE TABLE IF NOT EXISTS ev_state (
    vehicle_id TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS run_meta (
    run_id      TEXT PRIMARY KEY,
    mode        TEXT NOT NULL,
    seed        INT  NOT NULL,
    git_hash    TEXT,
    sumo_version TEXT,
    config_yaml TEXT,
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);
