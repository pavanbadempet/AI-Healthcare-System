"""
PyTorch Tabular MLP for binary classification.

A simple multi-layer perceptron with batch normalisation and dropout,
wrapped in a scikit-learn compatible estimator.  Suitable for flat
(non-sequential) tabular clinical data.

Architecture::

    ┌──────────────────────┐
    │  Input (B, F)        │   B = batch, F = num features
    └──────────┬───────────┘
               ▼
    ┌──────────────────────┐
    │  Linear → BN → ReLU  │ ×  len(hidden_dims)
    │  → Dropout           │
    └──────────┬───────────┘
               ▼
    ┌──────────────────────┐
    │  Linear(1) → Sigmoid │   binary output
    └──────────────────────┘
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.base import BaseEstimator, ClassifierMixin
from torch.utils.data import DataLoader, TensorDataset


class PyTorchTabularMLP(ClassifierMixin, BaseEstimator):
    """Scikit-learn compatible PyTorch MLP for tabular binary classification.

    Builds a feed-forward network from a list of hidden-layer sizes, with
    batch normalisation, ReLU activations, and dropout between each layer.
    Training uses Adam with ``BCEWithLogitsLoss``.

    Parameters
    ----------
    input_dim : int or None
        Number of input features.  Inferred from *X* at fit-time if
        ``None``.
    hidden_dims : list of int, default=[64, 32]
        Sizes of hidden layers.  Each entry creates one
        ``Linear → BatchNorm1d → ReLU → Dropout`` block.
    lr : float, default=0.005
        Learning rate for the Adam optimiser.
    epochs : int, default=150
        Number of training epochs.
    batch_size : int, default=128
        Mini-batch size for training.
    weight_decay : float, default=1e-4
        L2 regularisation coefficient for Adam.
    dropout : float, default=0.1
        Dropout probability applied after each hidden layer.

    Attributes
    ----------
    classes_ : ndarray of shape ``(n_classes,)``
        Unique class labels discovered during :meth:`fit`.
    model_state_ : dict or None
        Serialised PyTorch ``state_dict`` (pickle-safe).
    input_dim : int
        Number of features seen during :meth:`fit`.

    Examples
    --------
    >>> from clinical_tabular.models.tabular_mlp import PyTorchTabularMLP
    >>> clf = PyTorchTabularMLP(hidden_dims=[64, 32], epochs=50)
    >>> clf.fit(X_train, y_train)
    PyTorchTabularMLP(...)
    >>> probabilities = clf.predict_proba(X_test)
    >>> predictions = clf.predict(X_test)

    Notes
    -----
    The ``model`` attribute (the live ``nn.Sequential`` instance) is
    excluded from pickle serialisation.  On unpickling, the network is
    lazily reconstructed from ``model_state_`` on the first call to
    :meth:`predict` or :meth:`predict_proba`.
    """

    def __init__(
        self,
        input_dim=None,
        hidden_dims=[64, 32],  # noqa: B006
        lr: float = 0.005,
        epochs: int = 150,
        batch_size: int = 128,
        weight_decay: float = 1e-4,
        dropout: float = 0.1,
    ):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.weight_decay = weight_decay
        self.dropout = dropout
        self.classes_ = np.array([0, 1])
        self.model_state_ = None
        self.model = None

    def _build_model(self, input_dim: int) -> nn.Sequential:
        """Construct the MLP as an ``nn.Sequential``.

        Parameters
        ----------
        input_dim : int
            Number of input features.

        Returns
        -------
        nn.Sequential
            The fully-connected network.
        """
        layers = []
        prev_dim = input_dim
        for h_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(self.dropout))
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, 1))
        return nn.Sequential(*layers)

    def fit(self, X, y):
        """Fit the MLP on tabular data.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Training feature matrix.  DataFrames are converted to NumPy.
        y : array-like of shape ``(n_samples,)``
            Binary labels (0/1).

        Returns
        -------
        self
            Fitted estimator.
        """
        if hasattr(X, "values"):
            X = X.values
        if hasattr(y, "values"):
            y = y.values

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)

        self.classes_ = np.unique(y)
        self.input_dim = X.shape[1]
        self.model = self._build_model(self.input_dim)

        dataset = TensorDataset(torch.tensor(X), torch.tensor(y).unsqueeze(1))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        optimizer = optim.Adam(
            self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        criterion = nn.BCEWithLogitsLoss()

        self.model.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                out = self.model(batch_x)
                loss = criterion(out, batch_y)
                loss.backward()
                optimizer.step()

        self.model.eval()
        self.model_state_ = self.model.state_dict()
        return self

    def _ensure_model_loaded(self, X_shape_1: int) -> None:
        """Lazily reconstruct the network from ``model_state_``.

        Called automatically before inference.  If the live ``model``
        attribute is ``None`` (e.g. after unpickling), the network is
        rebuilt and its weights are restored from ``model_state_``.

        Parameters
        ----------
        X_shape_1 : int
            Number of input features (``X.shape[1]``).
        """
        if self.model is None:
            self.model = self._build_model(X_shape_1)
            if self.model_state_ is not None:
                self.model.load_state_dict(self.model_state_)
            self.model.eval()

    def predict_proba(self, X):
        """Predict class probabilities for *X*.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Feature matrix.

        Returns
        -------
        ndarray of shape ``(n_samples, 2)``
            Columns are ``[P(class=0), P(class=1)]``.
        """
        if hasattr(X, "values"):
            X = X.values
        X = np.array(X, dtype=np.float32)
        self._ensure_model_loaded(X.shape[1])

        self.model.eval()
        with torch.no_grad():
            logits = self.model(torch.tensor(X))
            probs = torch.sigmoid(logits).numpy()

        p1 = probs
        p0 = 1.0 - p1
        return np.hstack((p0, p1))

    def predict(self, X):
        """Predict binary class labels for *X*.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Feature matrix.

        Returns
        -------
        ndarray of shape ``(n_samples,)``
            Binary predictions (0 or 1).
        """
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

    # ------------------------------------------------------------------
    # Serialisation helpers (pickle-safe)
    # ------------------------------------------------------------------
    def __getstate__(self):
        """Exclude live PyTorch model from pickle serialisation."""
        state = self.__dict__.copy()
        if "model" in state:
            state["model"] = None
        return state

    def __setstate__(self, state):
        """Restore instance; model is lazily rebuilt on first inference."""
        self.__dict__.update(state)
        self.model = None
