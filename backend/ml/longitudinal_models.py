"""
Longitudinal Patient Time-Series Models.

Implements ClinicalTemporalLSTM — a bidirectional LSTM with temporal
attention for classifying patient risk from a sequence of clinical visits.

Input shape: (batch_size, sequence_length, num_features)
  - Each "step" in the sequence represents a single patient visit.
  - Features per step match the standard prediction input schema for the
    target condition (e.g. the 9 diabetes features).

Architecture:
  ┌──────────────┐
  │ Input (B,T,F) │
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  Bi-LSTM     │   ← captures forward & backward temporal dynamics
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  Temporal    │   ← learns which visits are most predictive
  │  Attention   │
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  FC + Sigmoid│   ← binary risk classification
  └──────────────┘
"""

import logging
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.base import BaseEstimator, ClassifierMixin
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure PyTorch Module
# ---------------------------------------------------------------------------
class TemporalAttention(nn.Module):
    """Additive (Bahdanau-style) attention over LSTM hidden states."""

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, lstm_output: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            lstm_output: (B, T, H) — hidden states for every timestep.

        Returns:
            context: (B, H) — attention-weighted summary.
            weights: (B, T) — normalised attention weights per timestep.
        """
        scores = self.attn(lstm_output).squeeze(-1)       # (B, T)
        weights = torch.softmax(scores, dim=1)             # (B, T)
        context = (lstm_output * weights.unsqueeze(-1)).sum(dim=1)  # (B, H)
        return context, weights


class ClinicalTemporalNet(nn.Module):
    """Bi-LSTM + temporal attention for longitudinal clinical data."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        full_hidden = hidden_dim * 2  # bidirectional
        self.attention = TemporalAttention(full_hidden)
        self.classifier = nn.Sequential(
            nn.LayerNorm(full_hidden),
            nn.Dropout(dropout),
            nn.Linear(full_hidden, full_hidden // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(full_hidden // 2, 1),
        )

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (B, T, F) — batch of patient visit sequences.

        Returns:
            logits: (B, 1)
            attn_weights: (B, T)
        """
        lstm_out, _ = self.lstm(x)               # (B, T, 2*H)
        context, attn_weights = self.attention(lstm_out)  # (B, 2*H), (B, T)
        logits = self.classifier(context)         # (B, 1)
        return logits, attn_weights


# ---------------------------------------------------------------------------
# Sklearn-compatible wrapper
# ---------------------------------------------------------------------------
class ClinicalTemporalLSTM(ClassifierMixin, BaseEstimator):
    """
    Sklearn-compliant wrapper around ClinicalTemporalNet for longitudinal
    patient visit sequences.

    Parameters
    ----------
    input_dim : int or None
        Number of features per visit.  Inferred from X at fit-time.
    hidden_dim : int
        LSTM hidden size (per direction).
    num_layers : int
        Number of stacked LSTM layers.
    lr : float
        Learning rate for AdamW optimiser.
    epochs : int
        Training epochs.
    batch_size : int
        Mini-batch size.
    dropout : float
        Dropout probability.
    weight_decay : float
        L2 regularisation coefficient.
    class_weight : float or None
        Positive-class weight for BCEWithLogitsLoss.  ``None`` → balanced.
    patience : int
        Early-stopping patience (epochs without validation improvement).
    """

    def __init__(
        self,
        input_dim: Optional[int] = None,
        hidden_dim: int = 64,
        num_layers: int = 2,
        lr: float = 1e-3,
        epochs: int = 100,
        batch_size: int = 64,
        dropout: float = 0.3,
        weight_decay: float = 1e-4,
        class_weight: Optional[float] = None,
        patience: int = 10,
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.dropout = dropout
        self.weight_decay = weight_decay
        self.class_weight = class_weight
        self.patience = patience
        # Internal state (not constructor params)
        self.classes_ = np.array([0, 1])
        self.model_state_: Optional[dict] = None
        self.model: Optional[ClinicalTemporalNet] = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def fit(self, X, y):
        """
        Fit the temporal LSTM on patient visit sequences.

        Parameters
        ----------
        X : array-like of shape (n_samples, seq_len, n_features)
            3-D tensor of patient visit sequences.
        y : array-like of shape (n_samples,)
            Binary labels.
        """
        X = self._to_3d_array(X)
        y = np.asarray(y, dtype=np.float32)

        self.classes_ = np.unique(y)
        self.input_dim = X.shape[2]

        # Auto-balance class weight
        if self.class_weight is None:
            n_pos = y.sum()
            n_neg = len(y) - n_pos
            pos_weight = n_neg / max(n_pos, 1.0)
        else:
            pos_weight = self.class_weight

        self.model = ClinicalTemporalNet(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            dropout=self.dropout,
        )

        dataset = TensorDataset(
            torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.float32).unsqueeze(1),
        )

        # 90/10 train/val split for early stopping
        n_val = max(1, int(len(dataset) * 0.1))
        n_train = len(dataset) - n_val
        train_ds, val_ds = torch.utils.data.random_split(dataset, [n_train, n_val])

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size)

        optimizer = optim.AdamW(
            self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        criterion = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor([pos_weight])
        )

        best_val_loss = float("inf")
        best_state = None
        epochs_no_improve = 0

        self.model.train()
        for epoch in range(self.epochs):
            # --- Training ---
            train_loss = 0.0
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                logits, _ = self.model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item() * batch_x.size(0)
            train_loss /= n_train

            # --- Validation ---
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    logits, _ = self.model(batch_x)
                    val_loss += criterion(logits, batch_y).item() * batch_x.size(0)
            val_loss /= max(n_val, 1)
            self.model.train()

            # --- Early stopping ---
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= self.patience:
                    logger.info(
                        "Early stopping at epoch %d (best val_loss=%.4f)",
                        epoch + 1,
                        best_val_loss,
                    )
                    break

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)

        self.model.eval()
        self.model_state_ = self.model.state_dict()
        return self

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict_proba(self, X):
        """Return (n_samples, 2) probability array."""
        X = self._to_3d_array(X)
        self._ensure_model_loaded(X.shape[2])

        self.model.eval()
        with torch.no_grad():
            logits, _ = self.model(torch.tensor(X, dtype=torch.float32))
            probs = torch.sigmoid(logits).numpy()

        p1 = probs  # (n, 1)
        p0 = 1.0 - p1
        return np.hstack((p0, p1))

    def predict(self, X):
        """Return binary predictions."""
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

    def predict_with_attention(self, X):
        """
        Return predictions along with per-visit attention weights.

        Returns
        -------
        probs : ndarray of shape (n_samples,)
            Positive-class probabilities.
        attn_weights : ndarray of shape (n_samples, seq_len)
            Attention weight per visit, summing to 1.
        """
        X = self._to_3d_array(X)
        self._ensure_model_loaded(X.shape[2])

        self.model.eval()
        with torch.no_grad():
            logits, attn = self.model(torch.tensor(X, dtype=torch.float32))
            probs = torch.sigmoid(logits).squeeze(-1).numpy()
            attn_np = attn.numpy()
        return probs, attn_np

    # ------------------------------------------------------------------
    # Serialisation helpers (pickle-safe)
    # ------------------------------------------------------------------
    def __getstate__(self):
        state = self.__dict__.copy()
        if "model" in state:
            state["model"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.model = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _ensure_model_loaded(self, input_dim: int):
        if self.model is None:
            self.model = ClinicalTemporalNet(
                input_dim=input_dim,
                hidden_dim=self.hidden_dim,
                num_layers=self.num_layers,
                dropout=self.dropout,
            )
            if self.model_state_ is not None:
                self.model.load_state_dict(self.model_state_)
            self.model.eval()

    @staticmethod
    def _to_3d_array(X) -> np.ndarray:
        """Ensure X is a 3-D float32 numpy array (B, T, F)."""
        if hasattr(X, "values"):
            X = X.values
        X = np.asarray(X, dtype=np.float32)
        if X.ndim == 2:
            # Single-step fallback: treat each row as a length-1 sequence
            X = X[:, np.newaxis, :]
        if X.ndim != 3:
            raise ValueError(
                f"ClinicalTemporalLSTM expects 3-D input (batch, seq, feat), "
                f"got shape {X.shape}"
            )
        return X
