"""
Kimi Agent — AI/ML Signal Prediction Engine (Part 4)

Provides model wrappers for predicting trade direction and sizing.
All models accept the flat indicator dict from IndicatorEngine.compute()
and output a direction probability (long/short/neutral) with confidence.

Models:
  • LSTMPredictor      — Sequential pattern recognition (PyTorch)
  • XGBoostPredictor   — Gradient-boosted feature importance
  • RandomForestPred   — Ensemble decision trees
  • PPOAgent           — Reinforcement learning (Stable-Baselines3)
  • EnsemblePredictor  — Weighted vote across all models

All models are designed to be:
  - Serialised/loaded via MLflow
  - Trained incrementally (online learning) or batch retrained
  - Used in inference with < 50ms latency per prediction
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Data Structures
# ────────────────────────────────────────────────────────

class PredictionDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class Prediction:
    """Output of a single model."""
    direction: PredictionDirection
    confidence: float            # 0.0 to 1.0
    long_prob: float = 0.5
    short_prob: float = 0.5
    model_name: str = ""
    latency_ms: float = 0.0
    features_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsemblePrediction:
    """Combined prediction from all models."""
    direction: PredictionDirection
    confidence: float
    individual: Dict[str, Prediction] = field(default_factory=dict)
    agreement_ratio: float = 0.0
    total_latency_ms: float = 0.0


# ────────────────────────────────────────────────────────
# Base Model Interface
# ────────────────────────────────────────────────────────

class BasePredictor(ABC):
    """Interface all prediction models must implement."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._is_trained = False

    @abstractmethod
    def predict(self, features: Dict[str, float]) -> Prediction:
        """Predict direction from indicator features."""
        ...

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Train or retrain the model. Returns metrics dict."""
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        """Serialise model to disk."""
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk."""
        ...

    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert flat feature dict to sorted numpy array."""
        sorted_keys = sorted(features.keys())
        return np.array([features.get(k, 0.0) for k in sorted_keys], dtype=np.float32)

    @property
    def is_trained(self) -> bool:
        return self._is_trained


# ────────────────────────────────────────────────────────
# LSTM Predictor (PyTorch)
# ────────────────────────────────────────────────────────

class LSTMPredictor(BasePredictor):
    """
    Sequential pattern recognition using a 2-layer LSTM.
    Best for detecting temporal patterns in feature sequences.
    
    Requires a sequence of feature vectors (not just one snapshot).
    When used with a single snapshot, it still works but with reduced accuracy.
    """

    def __init__(
        self,
        input_size: int = 80,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__("LSTM")
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self._model = None

    def _build_model(self) -> None:
        """Lazy-build PyTorch model on first use."""
        try:
            import torch
            import torch.nn as nn

            class LSTMNet(nn.Module):
                def __init__(self, input_sz, hidden_sz, n_layers, drop):
                    super().__init__()
                    self.lstm = nn.LSTM(
                        input_sz, hidden_sz, n_layers,
                        batch_first=True, dropout=drop if n_layers > 1 else 0,
                    )
                    self.fc = nn.Sequential(
                        nn.Linear(hidden_sz, 64),
                        nn.ReLU(),
                        nn.Dropout(drop),
                        nn.Linear(64, 3),  # 3 classes: long, short, neutral
                    )

                def forward(self, x):
                    lstm_out, _ = self.lstm(x)
                    last = lstm_out[:, -1, :]
                    return self.fc(last)

            self._model = LSTMNet(
                self.input_size, self.hidden_size, self.num_layers, self.dropout
            )
            logger.info(f"[{self.name}] Model built: {sum(p.numel() for p in self._model.parameters())} params")
        except ImportError:
            logger.warning(f"[{self.name}] PyTorch not available — using fallback")
            self._model = None

    def predict(self, features: Dict[str, float]) -> Prediction:
        start = time.time()

        if self._model is None:
            self._build_model()

        arr = self._features_to_array(features)

        if self._model is not None and self._is_trained:
            try:
                import torch
                x = torch.tensor(arr, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
                self._model.eval()
                with torch.no_grad():
                    logits = self._model(x)
                    probs = torch.softmax(logits, dim=1).squeeze().numpy()

                direction = [PredictionDirection.LONG, PredictionDirection.SHORT, PredictionDirection.NEUTRAL]
                idx = int(np.argmax(probs))

                return Prediction(
                    direction=direction[idx],
                    confidence=float(probs[idx]),
                    long_prob=float(probs[0]),
                    short_prob=float(probs[1]),
                    model_name=self.name,
                    latency_ms=(time.time() - start) * 1000,
                    features_used=len(features),
                )
            except Exception as exc:
                logger.warning(f"[{self.name}] Predict error: {exc}")

        # Fallback: feature-based heuristic
        return self._heuristic_predict(features, start)

    def _heuristic_predict(self, features: Dict[str, float], start: float) -> Prediction:
        """Simple fallback when model isn't trained."""
        ema_align = features.get("ema_alignment", 0.0)
        rsi = features.get("rsi_14", 50.0)
        macd_hist = features.get("macd_histogram", 0.0)

        score = ema_align * 0.4 + (rsi - 50) / 100 * 0.3
        if macd_hist > 0:
            score += 0.3
        elif macd_hist < 0:
            score -= 0.3

        if score > 0.2:
            direction = PredictionDirection.LONG
        elif score < -0.2:
            direction = PredictionDirection.SHORT
        else:
            direction = PredictionDirection.NEUTRAL

        return Prediction(
            direction=direction,
            confidence=min(abs(score), 1.0),
            long_prob=max(0, 0.5 + score / 2),
            short_prob=max(0, 0.5 - score / 2),
            model_name=f"{self.name}_heuristic",
            latency_ms=(time.time() - start) * 1000,
            features_used=len(features),
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        if self._model is None:
            self._build_model()
        if self._model is None:
            return {"error": "PyTorch not available"}

        try:
            import torch
            import torch.nn as nn
            from torch.utils.data import DataLoader, TensorDataset

            X_t = torch.tensor(X, dtype=torch.float32)
            if X_t.dim() == 2:
                X_t = X_t.unsqueeze(1)  # Add sequence dim
            y_t = torch.tensor(y, dtype=torch.long)

            dataset = TensorDataset(X_t, y_t)
            loader = DataLoader(dataset, batch_size=32, shuffle=True)

            optimiser = torch.optim.Adam(self._model.parameters(), lr=1e-3)
            criterion = nn.CrossEntropyLoss()

            self._model.train()
            total_loss = 0.0
            for epoch in range(10):
                epoch_loss = 0.0
                for xb, yb in loader:
                    optimiser.zero_grad()
                    out = self._model(xb)
                    loss = criterion(out, yb)
                    loss.backward()
                    optimiser.step()
                    epoch_loss += loss.item()
                total_loss = epoch_loss

            self._is_trained = True
            logger.info(f"[{self.name}] Training complete — loss={total_loss:.4f}")
            return {"final_loss": total_loss, "epochs": 10}

        except Exception as exc:
            logger.error(f"[{self.name}] Training failed: {exc}")
            return {"error": str(exc)}

    def save(self, path: str) -> None:
        if self._model is not None:
            try:
                import torch
                torch.save(self._model.state_dict(), path)
                logger.info(f"[{self.name}] Saved to {path}")
            except Exception as exc:
                logger.error(f"[{self.name}] Save failed: {exc}")

    def load(self, path: str) -> None:
        if self._model is None:
            self._build_model()
        if self._model is not None:
            try:
                import torch
                self._model.load_state_dict(torch.load(path, weights_only=True))
                self._is_trained = True
                logger.info(f"[{self.name}] Loaded from {path}")
            except Exception as exc:
                logger.error(f"[{self.name}] Load failed: {exc}")


# ────────────────────────────────────────────────────────
# XGBoost Predictor
# ────────────────────────────────────────────────────────

class XGBoostPredictor(BasePredictor):
    """
    Gradient-boosted decision trees. Excellent at learning feature importance
    from structured indicator data. Supports online updates.
    """

    def __init__(self, n_estimators: int = 200, max_depth: int = 6) -> None:
        super().__init__("XGBoost")
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._model = None
        self._feature_names: List[str] = []

    def predict(self, features: Dict[str, float]) -> Prediction:
        start = time.time()
        arr = self._features_to_array(features)

        if self._model is not None and self._is_trained:
            try:
                import xgboost as xgb
                dmat = xgb.DMatrix(arr.reshape(1, -1), feature_names=self._feature_names)
                probs = self._model.predict(dmat)[0]

                direction = [PredictionDirection.LONG, PredictionDirection.SHORT, PredictionDirection.NEUTRAL]
                idx = int(np.argmax(probs))

                return Prediction(
                    direction=direction[idx],
                    confidence=float(probs[idx]),
                    long_prob=float(probs[0]),
                    short_prob=float(probs[1]),
                    model_name=self.name,
                    latency_ms=(time.time() - start) * 1000,
                    features_used=len(features),
                )
            except Exception as exc:
                logger.warning(f"[{self.name}] Predict error: {exc}")

        # Fallback
        return Prediction(
            direction=PredictionDirection.NEUTRAL,
            confidence=0.0,
            model_name=f"{self.name}_untrained",
            latency_ms=(time.time() - start) * 1000,
            features_used=len(features),
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        try:
            import xgboost as xgb

            self._feature_names = [f"f{i}" for i in range(X.shape[1])]
            dtrain = xgb.DMatrix(X, label=y, feature_names=self._feature_names)

            params = {
                "objective": "multi:softprob",
                "num_class": 3,
                "max_depth": self._max_depth,
                "eta": 0.1,
                "eval_metric": "mlogloss",
                "tree_method": "hist",
            }

            self._model = xgb.train(params, dtrain, num_boost_round=self._n_estimators)
            self._is_trained = True
            logger.info(f"[{self.name}] Training complete")
            return {"estimators": self._n_estimators, "max_depth": self._max_depth}

        except ImportError:
            logger.warning(f"[{self.name}] xgboost not installed")
            return {"error": "xgboost not installed"}
        except Exception as exc:
            logger.error(f"[{self.name}] Training failed: {exc}")
            return {"error": str(exc)}

    def update(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Online update — add new trees to existing model."""
        try:
            import xgboost as xgb
            if self._model is None:
                return self.train(X, y)

            dtrain = xgb.DMatrix(X, label=y, feature_names=self._feature_names)
            self._model = xgb.train(
                self._model.save_config(),
                dtrain,
                num_boost_round=10,
                xgb_model=self._model,
            )
            return {"updated_trees": 10}
        except Exception as exc:
            return {"error": str(exc)}

    def save(self, path: str) -> None:
        if self._model:
            self._model.save_model(path)

    def load(self, path: str) -> None:
        try:
            import xgboost as xgb
            self._model = xgb.Booster()
            self._model.load_model(path)
            self._is_trained = True
        except Exception as exc:
            logger.error(f"[{self.name}] Load failed: {exc}")


# ────────────────────────────────────────────────────────
# Random Forest Predictor
# ────────────────────────────────────────────────────────

class RandomForestPredictor(BasePredictor):
    """
    Ensemble of decision trees. Robust against overfitting, handles
    mixed feature types well. Good for baseline comparisons.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 10) -> None:
        super().__init__("RandomForest")
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._model = None

    def predict(self, features: Dict[str, float]) -> Prediction:
        start = time.time()
        arr = self._features_to_array(features)

        if self._model is not None and self._is_trained:
            try:
                probs = self._model.predict_proba(arr.reshape(1, -1))[0]
                direction = [PredictionDirection.LONG, PredictionDirection.SHORT, PredictionDirection.NEUTRAL]
                idx = int(np.argmax(probs))

                return Prediction(
                    direction=direction[idx],
                    confidence=float(probs[idx]),
                    long_prob=float(probs[0]) if len(probs) > 0 else 0.0,
                    short_prob=float(probs[1]) if len(probs) > 1 else 0.0,
                    model_name=self.name,
                    latency_ms=(time.time() - start) * 1000,
                    features_used=len(features),
                )
            except Exception as exc:
                logger.warning(f"[{self.name}] Predict error: {exc}")

        return Prediction(
            direction=PredictionDirection.NEUTRAL,
            confidence=0.0,
            model_name=f"{self.name}_untrained",
            latency_ms=(time.time() - start) * 1000,
            features_used=len(features),
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        try:
            from sklearn.ensemble import RandomForestClassifier

            self._model = RandomForestClassifier(
                n_estimators=self._n_estimators,
                max_depth=self._max_depth,
                random_state=42,
                n_jobs=-1,
            )
            self._model.fit(X, y)
            self._is_trained = True

            accuracy = self._model.score(X, y)
            logger.info(f"[{self.name}] Training complete — train acc={accuracy:.4f}")
            return {"train_accuracy": accuracy}

        except ImportError:
            return {"error": "scikit-learn not installed"}
        except Exception as exc:
            return {"error": str(exc)}

    def save(self, path: str) -> None:
        if self._model:
            import joblib
            joblib.dump(self._model, path)

    def load(self, path: str) -> None:
        try:
            import joblib
            self._model = joblib.load(path)
            self._is_trained = True
        except Exception as exc:
            logger.error(f"[{self.name}] Load failed: {exc}")


# ────────────────────────────────────────────────────────
# PPO Reinforcement Learning Agent (Stable-Baselines3)
# ────────────────────────────────────────────────────────

class PPOAgent(BasePredictor):
    """
    Proximal Policy Optimisation agent using Stable-Baselines3.
    Learns optimal trading actions through environment interaction.

    Note: This is a stub — full RL training requires the trading
    environment (Part 8). Here we define the interface and fallback.
    """

    def __init__(self) -> None:
        super().__init__("PPO")
        self._model = None

    def predict(self, features: Dict[str, float]) -> Prediction:
        start = time.time()
        arr = self._features_to_array(features)

        if self._model is not None and self._is_trained:
            try:
                obs = arr.reshape(1, -1)
                action, _ = self._model.predict(obs, deterministic=True)
                direction = [PredictionDirection.LONG, PredictionDirection.SHORT, PredictionDirection.NEUTRAL]
                return Prediction(
                    direction=direction[int(action[0]) % 3],
                    confidence=0.6,  # PPO doesn't directly output confidence
                    model_name=self.name,
                    latency_ms=(time.time() - start) * 1000,
                    features_used=len(features),
                )
            except Exception as exc:
                logger.warning(f"[{self.name}] Predict error: {exc}")

        return Prediction(
            direction=PredictionDirection.NEUTRAL,
            confidence=0.0,
            model_name=f"{self.name}_untrained",
            latency_ms=(time.time() - start) * 1000,
            features_used=len(features),
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """PPO training requires environment interaction — see Part 8."""
        logger.info(f"[{self.name}] PPO training requires RL environment (Part 8)")
        return {"status": "requires_environment"}

    def save(self, path: str) -> None:
        if self._model:
            self._model.save(path)

    def load(self, path: str) -> None:
        try:
            from stable_baselines3 import PPO as SB3PPO
            self._model = SB3PPO.load(path)
            self._is_trained = True
        except Exception as exc:
            logger.error(f"[{self.name}] Load failed: {exc}")


# ════════════════════════════════════════════════════════
# Ensemble Predictor — Weighted Vote
# ════════════════════════════════════════════════════════

class EnsemblePredictor:
    """
    Combines predictions from all models via weighted voting.
    Only includes models that are trained and confident.

    Default weights:
      LSTM: 0.30, XGBoost: 0.30, RandomForest: 0.20, PPO: 0.20
    """

    DEFAULT_WEIGHTS = {
        "LSTM": 0.30,
        "XGBoost": 0.30,
        "RandomForest": 0.20,
        "PPO": 0.20,
    }

    def __init__(
        self,
        models: Optional[List[BasePredictor]] = None,
        weights: Optional[Dict[str, float]] = None,
        min_confidence: float = 0.5,
    ) -> None:
        self._models = models or [
            LSTMPredictor(),
            XGBoostPredictor(),
            RandomForestPredictor(),
            PPOAgent(),
        ]
        self._weights = weights or self.DEFAULT_WEIGHTS
        self._min_confidence = min_confidence

    def predict(self, features: Dict[str, float]) -> EnsemblePrediction:
        """Run all models and combine via weighted vote."""
        start = time.time()
        individual: Dict[str, Prediction] = {}

        for model in self._models:
            try:
                pred = model.predict(features)
                individual[model.name] = pred
            except Exception as exc:
                logger.warning(f"[Ensemble] {model.name} failed: {exc}")

        if not individual:
            return EnsemblePrediction(
                direction=PredictionDirection.NEUTRAL,
                confidence=0.0,
                agreement_ratio=0.0,
                total_latency_ms=(time.time() - start) * 1000,
            )

        # Weighted vote
        long_score = 0.0
        short_score = 0.0
        neutral_score = 0.0
        total_weight = 0.0

        for name, pred in individual.items():
            w = self._weights.get(name, 0.1)
            if pred.confidence < self._min_confidence and name not in ("PPO",):
                w *= 0.5  # Reduce weight for low-confidence predictions

            if pred.direction == PredictionDirection.LONG:
                long_score += w * pred.confidence
            elif pred.direction == PredictionDirection.SHORT:
                short_score += w * pred.confidence
            else:
                neutral_score += w * pred.confidence
            total_weight += w

        if total_weight > 0:
            long_score /= total_weight
            short_score /= total_weight
            neutral_score /= total_weight

        # Direction
        scores = {
            PredictionDirection.LONG: long_score,
            PredictionDirection.SHORT: short_score,
            PredictionDirection.NEUTRAL: neutral_score,
        }
        direction = max(scores, key=scores.get)  # type: ignore
        confidence = scores[direction]

        # Agreement ratio
        majority = direction
        agreeing = sum(
            1 for p in individual.values() if p.direction == majority
        )
        agreement = agreeing / len(individual)

        return EnsemblePrediction(
            direction=direction,
            confidence=round(confidence, 4),
            individual=individual,
            agreement_ratio=round(agreement, 3),
            total_latency_ms=round((time.time() - start) * 1000, 2),
        )

    def train_all(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Dict[str, float]]:
        """Train all models on the same dataset."""
        results = {}
        for model in self._models:
            logger.info(f"[Ensemble] Training {model.name}...")
            results[model.name] = model.train(X, y)
        return results
