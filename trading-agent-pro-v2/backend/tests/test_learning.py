"""
Kimi Agent — Unit Tests for Learning Engine Components
"""
import pytest

from app.services.learning.learning_engine import (
    OnlineLearner,
    MistakeTracker,
    PerformanceTracker,
    TradeOutcome,
    TradeResult,
)


@pytest.fixture
def learner():
    return OnlineLearner(buffer_size=10, retrain_every=3)


@pytest.fixture
def tracker():
    return MistakeTracker()


@pytest.fixture
def perf():
    pt = PerformanceTracker()
    pt.set_balance(10000.0)
    return pt


class TestOnlineLearner:
    def test_add_outcome(self, learner):
        outcome = TradeOutcome(
            features=[0.5] * 20,
            result=TradeResult.WIN,
            pnl=50.0,
        )
        learner.add_outcome(outcome)
        assert len(learner._buffer) == 1

    def test_buffer_limit(self, learner):
        for i in range(15):
            learner.add_outcome(TradeOutcome(
                features=[float(i)] * 20,
                result=TradeResult.WIN if i % 2 == 0 else TradeResult.LOSS,
                pnl=10.0 if i % 2 == 0 else -5.0,
            ))
        assert len(learner._buffer) <= 10


class TestMistakeTracker:
    def test_no_mistakes_initially(self, tracker):
        summary = tracker.get_summary()
        assert summary["total_mistakes"] == 0

    def test_record_mistake(self, tracker):
        tracker.record(
            symbol="BTC/USDT",
            direction="LONG",
            mistake_type="counter_trend",
            severity=0.8,
            description="Took long against daily downtrend",
        )
        summary = tracker.get_summary()
        assert summary["total_mistakes"] == 1

    def test_multiple_same_type(self, tracker):
        for _ in range(3):
            tracker.record(
                symbol="BTC/USDT",
                direction="LONG",
                mistake_type="counter_trend",
                severity=0.5,
                description="Counter-trend entry",
            )
        summary = tracker.get_summary()
        assert summary["total_mistakes"] == 3


class TestPerformanceTracker:
    def test_initial_state(self, perf):
        assert not perf.is_paused
        assert perf.pause_reason == ""

    def test_record_win(self, perf):
        perf.record_trade(pnl=100.0, is_win=True)
        snap = perf.get_snapshot()
        assert snap.total_trades == 1
        assert snap.winning_trades == 1

    def test_record_loss(self, perf):
        perf.record_trade(pnl=-50.0, is_win=False)
        snap = perf.get_snapshot()
        assert snap.total_trades == 1
        assert snap.losing_trades == 1

    def test_win_rate_calculation(self, perf):
        perf.record_trade(pnl=100.0, is_win=True)
        perf.record_trade(pnl=-50.0, is_win=False)
        snap = perf.get_snapshot()
        assert snap.win_rate == 0.5

    def test_kill_switch_on_low_win_rate(self, perf):
        # Record 10 losses to trigger kill switch
        for _ in range(10):
            perf.record_trade(pnl=-100.0, is_win=False)
        # After many losses, the tracker should pause
        assert perf.is_paused or perf.get_snapshot().win_rate < 0.4

    def test_pnl_tracking(self, perf):
        perf.record_trade(pnl=200.0, is_win=True)
        perf.record_trade(pnl=-80.0, is_win=False)
        snap = perf.get_snapshot()
        assert snap.total_pnl == 120.0
