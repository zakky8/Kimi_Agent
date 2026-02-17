-- ================================================================
-- Kimi Agent — Database Migration: Agent Evolution + Mistakes
-- Run after the base init.sql
-- ================================================================

-- Agent Evolution Log
-- Tracks how the AI's parameters evolve over time
CREATE TABLE IF NOT EXISTS agent_evolution (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type      TEXT NOT NULL,           -- 'retrain', 'config_change', 'pause', 'resume'
    model_name      TEXT,                    -- 'LSTM', 'XGBoost', 'RandomForest', 'PPO'
    change_summary  TEXT NOT NULL,
    metrics_before  JSONB,                   -- snapshot of metrics before change
    metrics_after   JSONB,                   -- snapshot of metrics after change
    triggered_by    TEXT DEFAULT 'system'     -- 'system', 'user', 'online_learner'
);

CREATE INDEX idx_evolution_ts ON agent_evolution (timestamp DESC);
CREATE INDEX idx_evolution_model ON agent_evolution (model_name);

-- Mistake Log
-- Records every detected trading mistake for analysis
CREATE TABLE IF NOT EXISTS trading_mistakes (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,            -- 'LONG' or 'SHORT'
    mistake_type    TEXT NOT NULL,            -- 'counter_trend', 'oversize', etc
    severity        REAL NOT NULL DEFAULT 0.0,
    description     TEXT NOT NULL,
    corrective_action TEXT,
    trade_entry_price  REAL,
    trade_exit_price   REAL,
    trade_pnl       REAL,
    indicators_snapshot JSONB                -- indicators at time of mistake
);

CREATE INDEX idx_mistakes_ts ON trading_mistakes (timestamp DESC);
CREATE INDEX idx_mistakes_symbol ON trading_mistakes (symbol);
CREATE INDEX idx_mistakes_type ON trading_mistakes (mistake_type);

-- Performance Snapshots
-- Periodic snapshots of trading performance
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    win_rate        REAL NOT NULL,
    total_trades    INT NOT NULL,
    winning_trades  INT NOT NULL,
    losing_trades   INT NOT NULL,
    total_pnl       REAL NOT NULL,
    max_drawdown_pct REAL NOT NULL,
    sharpe_ratio    REAL NOT NULL,
    avg_rr          REAL NOT NULL,
    profit_factor   REAL
);

CREATE INDEX idx_perf_ts ON performance_snapshots (timestamp DESC);

-- Trading Signals
-- Historical log of all generated signals
CREATE TABLE IF NOT EXISTS trading_signals (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,
    signal_type     TEXT NOT NULL,            -- 'MARKET', 'LIMIT', 'STOP'
    entry_price     REAL NOT NULL,
    stop_loss       REAL NOT NULL,
    take_profit     REAL NOT NULL,
    position_size   REAL,
    risk_pct        REAL,
    risk_reward     REAL,
    confidence      REAL,
    consensus_score REAL,
    agreement_count INT,
    status          TEXT DEFAULT 'PENDING',
    exit_price      REAL,
    exit_reason     TEXT,
    pnl             REAL,
    reasons         JSONB
);

CREATE INDEX idx_signals_ts ON trading_signals (timestamp DESC);
CREATE INDEX idx_signals_symbol ON trading_signals (symbol);
CREATE INDEX idx_signals_status ON trading_signals (status);
