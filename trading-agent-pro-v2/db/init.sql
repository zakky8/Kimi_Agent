-- ================================================================
-- Kimi Agent — TimescaleDB Schema Initialisation
-- ================================================================
-- Run inside the PostgreSQL container with TimescaleDB extension.
-- docker-compose.dev.yml maps this file to /docker-entrypoint-initdb.d/

-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ================================================================
-- Table 1: market_data_ohlcv  (continuous append-only hypertable)
-- ================================================================
CREATE TABLE IF NOT EXISTS market_data_ohlcv (
    time         TIMESTAMPTZ      NOT NULL,
    symbol       TEXT              NOT NULL,
    timeframe    TEXT              NOT NULL,
    open         DOUBLE PRECISION,
    high         DOUBLE PRECISION,
    low          DOUBLE PRECISION,
    close        DOUBLE PRECISION,
    volume       DOUBLE PRECISION,
    source       TEXT,
    PRIMARY KEY (time, symbol, timeframe)
);

SELECT create_hypertable('market_data_ohlcv', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf_time
    ON market_data_ohlcv (symbol, timeframe, time DESC);

-- ================================================================
-- Table 2: trading_signals
-- ================================================================
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    symbol             TEXT NOT NULL,
    timeframe          TEXT NOT NULL,
    direction          TEXT NOT NULL,
    entry_price        DOUBLE PRECISION,
    stop_loss          DOUBLE PRECISION,
    take_profit_1      DOUBLE PRECISION,
    take_profit_2      DOUBLE PRECISION,
    take_profit_3      DOUBLE PRECISION,
    overall_confidence DOUBLE PRECISION,
    confluence_score   DOUBLE PRECISION,
    xgb_win_prob       DOUBLE PRECISION,
    lstm_forecast_24h  DOUBLE PRECISION,
    regime             TEXT,
    reasoning          TEXT,
    status             TEXT DEFAULT 'ACTIVE',
    feature_vector     JSONB,
    indicators         JSONB
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol
    ON trading_signals (symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signals_status
    ON trading_signals (status);

-- ================================================================
-- Table 3: signal_outcomes
-- ================================================================
CREATE TABLE IF NOT EXISTS signal_outcomes (
    outcome_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id     UUID REFERENCES trading_signals(signal_id),
    closed_at     TIMESTAMPTZ DEFAULT NOW(),
    exit_price    DOUBLE PRECISION,
    outcome       TEXT,         -- WIN / LOSS / BREAKEVEN
    pnl_pct       DOUBLE PRECISION,
    pnl_r         DOUBLE PRECISION,
    holding_hours DOUBLE PRECISION,
    exit_reason   TEXT          -- TP1 / TP2 / TP3 / SL / MANUAL / EXPIRED
);

CREATE INDEX IF NOT EXISTS idx_outcomes_signal
    ON signal_outcomes (signal_id);

-- ================================================================
-- Table 4: model_performance_metrics  (hypertable)
-- ================================================================
CREATE TABLE IF NOT EXISTS model_performance_metrics (
    recorded_at    TIMESTAMPTZ      NOT NULL,
    symbol         TEXT              NOT NULL,
    model_type     TEXT              NOT NULL,
    win_rate_20    DOUBLE PRECISION,
    win_rate_50    DOUBLE PRECISION,
    win_rate_100   DOUBLE PRECISION,
    sharpe_30d     DOUBLE PRECISION,
    profit_factor  DOUBLE PRECISION,
    avg_r_multiple DOUBLE PRECISION,
    total_trades   INTEGER,
    model_version  TEXT,
    PRIMARY KEY (recorded_at, symbol, model_type)
);

SELECT create_hypertable('model_performance_metrics', 'recorded_at', if_not_exists => TRUE);

-- ================================================================
-- Retention policy: drop raw OHLCV data older than 2 years
-- ================================================================
SELECT add_retention_policy('market_data_ohlcv', INTERVAL '2 years', if_not_exists => TRUE);
