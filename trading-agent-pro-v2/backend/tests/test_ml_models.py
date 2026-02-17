"""
Kimi Agent — Unit Tests for ML Models
"""
import numpy as np
import pytest

from app.services.ml.models import (
    EnsemblePredictor,
    XGBoostPredictor,
    RandomForestPredictor,
)


@pytest.fixture
def ensemble():
    return EnsemblePredictor()


@pytest.fixture
def features():
    """20-feature vector."""
    return [0.5, -0.3, 0.8, 0.2, -0.1, 0.6, -0.4, 0.9, 0.0, 0.3,
            0.7, -0.2, 0.1, 0.4, -0.5, 0.8, 0.3, -0.6, 0.2, 0.5]


class TestEnsemblePredictor:
    def test_predict_returns_dict(self, ensemble, features):
        result = ensemble.predict(features)
        assert isinstance(result, dict)

    def test_prediction_keys(self, ensemble, features):
        result = ensemble.predict(features)
        assert "direction" in result
        assert "confidence" in result
        assert "model_votes" in result

    def test_direction_valid(self, ensemble, features):
        result = ensemble.predict(features)
        assert result["direction"] in ["LONG", "SHORT", "NEUTRAL"]

    def test_confidence_range(self, ensemble, features):
        result = ensemble.predict(features)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_empty_features(self, ensemble):
        result = ensemble.predict([])
        assert result["direction"] == "NEUTRAL"


class TestXGBoostPredictor:
    def test_predict_untrained(self):
        model = XGBoostPredictor()
        result = model.predict([0.5] * 20)
        # Untrained model should return heuristic fallback
        assert isinstance(result, dict)

    def test_train_and_predict(self):
        model = XGBoostPredictor()
        X = np.random.randn(50, 20).tolist()
        y = [1 if x[0] > 0 else 0 for x in X]
        model.train(X, y)
        result = model.predict([0.5] * 20)
        assert "direction" in result


class TestRandomForestPredictor:
    def test_predict_untrained(self):
        model = RandomForestPredictor()
        result = model.predict([0.5] * 20)
        assert isinstance(result, dict)

    def test_train_and_predict(self):
        model = RandomForestPredictor()
        X = np.random.randn(50, 20).tolist()
        y = [1 if x[0] > 0 else 0 for x in X]
        model.train(X, y)
        result = model.predict([0.5] * 20)
        assert "direction" in result
