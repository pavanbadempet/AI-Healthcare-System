"""
Feature Tokenizer Transformer (FT-Transformer) for tabular data.

Implements the FT-Transformer architecture which tokenises each numerical
feature into an embedding, prepends a learnable ``[CLS]`` token, passes
the sequence through a stack of Pre-LN Transformer encoder blocks, and
classifies using the ``[CLS]`` output.

Architecture::

    ┌────────────────────────┐
    │  Input (B, F)          │   B = batch, F = num features
    └───────────┬────────────┘
                ▼
    ┌────────────────────────┐
    │  NumericalFeature      │   per-feature linear projection → (B, F, D)
    │  Tokenizer             │
    └───────────┬────────────┘
                ▼
    ┌────────────────────────┐
    │  Prepend [CLS] token   │   → (B, F+1, D)
    └───────────┬────────────┘
                ▼
    ┌────────────────────────┐
    │  Transformer Encoder   │   × depth  (Pre-LN, multi-head self-attn)
    │  Blocks                │
    └───────────┬────────────┘
                ▼
    ┌────────────────────────┐
    │  LayerNorm → Linear    │   CLS output → 2-class logits
    └────────────────────────┘

Reference:
    Gorishniy et al., "Revisiting Deep Learning Models for Tabular Data",
    NeurIPS 2021.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from torch.utils.data import DataLoader, TensorDataset


class NumericalFeatureTokenizer(nn.Module):
    """Project each numerical feature into an embedding space.

    Every input feature *f_i* is mapped to a *d_embedding*-dimensional
    token via a learned affine transformation:

        token_i = f_i * w_i + b_i

    Parameters
    ----------
    num_features : int
        Number of input features.
    d_embedding : int
        Dimensionality of the embedding space for each feature token.

    Examples
    --------
    >>> tokenizer = NumericalFeatureTokenizer(num_features=9, d_embedding=32)
    >>> x = torch.randn(16, 9)          # batch of 16, 9 features
    >>> tokens = tokenizer(x)
    >>> tokens.shape
    torch.Size([16, 9, 32])
    """

    def __init__(self, num_features: int, d_embedding: int):
        super().__init__()
        self.weights = nn.Parameter(torch.randn(num_features, d_embedding))
        self.biases = nn.Parameter(torch.randn(num_features, d_embedding))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Tokenise numerical features.

        Parameters
        ----------
        x : Tensor of shape ``(batch_size, num_features)``

        Returns
        -------
        Tensor of shape ``(batch_size, num_features, d_embedding)``
        """
        # (B, F) → (B, F, 1)
        x_unsqueezed = x.unsqueeze(-1)
        # (B, F, 1) * (1, F, D) + (1, F, D) → (B, F, D)
        tokens = x_unsqueezed * self.weights.unsqueeze(0) + self.biases.unsqueeze(0)
        return tokens


class TransformerEncoderBlock(nn.Module):
    """Pre-LayerNorm Transformer encoder block.

    Consists of multi-head self-attention followed by a position-wise
    feed-forward network, each wrapped in a residual connection with
    pre-normalisation (Pre-LN).

    Parameters
    ----------
    d_embedding : int
        Model / embedding dimensionality.
    n_heads : int
        Number of attention heads.
    ffn_dim : int
        Hidden dimensionality of the feed-forward network.
    dropout : float, default=0.1
        Dropout probability applied after attention and FFN.

    Examples
    --------
    >>> block = TransformerEncoderBlock(d_embedding=32, n_heads=2,
    ...                                 ffn_dim=64, dropout=0.1)
    >>> x = torch.randn(16, 10, 32)   # (B, seq_len, D)
    >>> out = block(x)
    >>> out.shape
    torch.Size([16, 10, 32])
    """

    def __init__(self, d_embedding: int, n_heads: int, ffn_dim: int, dropout: float = 0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_embedding)
        self.mha = nn.MultiheadAttention(
            embed_dim=d_embedding,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.dropout1 = nn.Dropout(dropout)

        self.ln2 = nn.LayerNorm(d_embedding)
        self.ffn = nn.Sequential(
            nn.Linear(d_embedding, ffn_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_dim, d_embedding),
        )
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply Pre-LN attention + FFN with residuals.

        Parameters
        ----------
        x : Tensor of shape ``(batch_size, seq_len, d_embedding)``

        Returns
        -------
        Tensor of same shape as *x*.
        """
        # Pre-LN Multi-Head Attention
        x_norm = self.ln1(x)
        attn_out, _ = self.mha(x_norm, x_norm, x_norm)
        x = x + self.dropout1(attn_out)

        # Pre-LN Feed Forward
        x_norm2 = self.ln2(x)
        ffn_out = self.ffn(x_norm2)
        x = x + self.dropout2(ffn_out)
        return x


class FTTransformerNet(nn.Module):
    """Full FT-Transformer network with a learnable ``[CLS]`` token.

    Tokenises each numerical feature, prepends a ``[CLS]`` token, applies
    a stack of :class:`TransformerEncoderBlock` layers, and produces
    2-class logits from the final ``[CLS]`` representation.

    Parameters
    ----------
    num_features : int
        Number of input features.
    d_embedding : int, default=32
        Token embedding dimensionality.
    n_heads : int, default=2
        Number of attention heads per Transformer block.
    depth : int, default=2
        Number of stacked Transformer encoder blocks.
    ffn_dim : int, default=64
        Hidden size of the position-wise feed-forward networks.
    dropout : float, default=0.1
        Dropout probability throughout the network.

    Examples
    --------
    >>> net = FTTransformerNet(num_features=9, d_embedding=32, depth=2)
    >>> x = torch.randn(16, 9)
    >>> logits = net(x)
    >>> logits.shape
    torch.Size([16, 2])
    """

    def __init__(
        self,
        num_features: int,
        d_embedding: int = 32,
        n_heads: int = 2,
        depth: int = 2,
        ffn_dim: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.tokenizer = NumericalFeatureTokenizer(num_features, d_embedding)

        # [CLS] token representation
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_embedding))

        # Transformer layers
        self.layers = nn.ModuleList(
            [TransformerEncoderBlock(d_embedding, n_heads, ffn_dim, dropout) for _ in range(depth)]
        )

        self.ln_final = nn.LayerNorm(d_embedding)

        # Binary classification head: maps CLS output to 2 classes (logits)
        self.head = nn.Linear(d_embedding, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass producing 2-class logits.

        Parameters
        ----------
        x : Tensor of shape ``(batch_size, num_features)``

        Returns
        -------
        Tensor of shape ``(batch_size, 2)`` — raw logits.
        """
        batch_size = x.shape[0]

        # Tokenize features → (B, F, D)
        tokens = self.tokenizer(x)

        # Expand [CLS] token to match batch size → (B, 1, D)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)

        # Prepend [CLS] token → (B, F+1, D)
        tokens = torch.cat([cls_tokens, tokens], dim=1)

        # Apply Transformer blocks
        for layer in self.layers:
            tokens = layer(tokens)

        # Final layer normalization
        tokens = self.ln_final(tokens)

        # Extract the output of the CLS token → (B, D)
        cls_output = tokens[:, 0]

        # Output logits → (B, 2)
        logits = self.head(cls_output)
        return logits


class FTTransformerClassifier(ClassifierMixin, BaseEstimator):
    """Scikit-learn compatible wrapper for the FT-Transformer.

    Wraps :class:`FTTransformerNet` so it can be used in scikit-learn
    pipelines, grid-searches, and cross-validation loops.  The model is
    trained with AdamW and CrossEntropyLoss.

    Parameters
    ----------
    d_embedding : int, default=32
        Token embedding dimensionality.
    n_heads : int, default=2
        Number of attention heads per Transformer block.
    depth : int, default=2
        Number of stacked Transformer encoder blocks.
    ffn_dropout : float, default=0.1
        Dropout probability used throughout the network.
    lr : float, default=0.001
        Learning rate for the AdamW optimiser.
    epochs : int, default=10
        Number of training epochs.
    batch_size : int, default=512
        Mini-batch size for training.
    weight_decay : float, default=1e-4
        L2 regularisation coefficient for AdamW.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Unique class labels discovered during :meth:`fit`.
    n_features_in_ : int
        Number of features seen during :meth:`fit`.
    model_state_ : dict or None
        Serialised PyTorch ``state_dict`` (pickle-safe).

    Examples
    --------
    >>> from clinical_tabular.models.ft_transformer import FTTransformerClassifier
    >>> clf = FTTransformerClassifier(d_embedding=32, depth=2, epochs=5)
    >>> clf.fit(X_train, y_train)
    FTTransformerClassifier(...)
    >>> probabilities = clf.predict_proba(X_test)
    >>> predictions = clf.predict(X_test)

    Notes
    -----
    The ``model_`` attribute (the live :class:`FTTransformerNet` instance)
    is excluded from pickle serialisation.  On unpickling, the network is
    lazily reconstructed from ``model_state_`` on the first call to
    :meth:`predict` or :meth:`predict_proba`.
    """

    def __init__(
        self,
        d_embedding: int = 32,
        n_heads: int = 2,
        depth: int = 2,
        ffn_dropout: float = 0.1,
        lr: float = 0.001,
        epochs: int = 10,
        batch_size: int = 512,
        weight_decay: float = 1e-4,
    ):
        self.d_embedding = d_embedding
        self.n_heads = n_heads
        self.depth = depth
        self.ffn_dropout = ffn_dropout
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.weight_decay = weight_decay
        self.model_ = None
        self.model_state_ = None
        self.classes_ = None
        self.n_features_in_ = None

    def fit(self, X, y):
        """Fit the FT-Transformer on tabular data.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Training feature matrix.  DataFrames are converted to NumPy.
        y : array-like of shape ``(n_samples,)``
            Integer class labels.

        Returns
        -------
        self
            Fitted estimator.
        """
        # Cast input to numpy
        if hasattr(X, "values"):
            X = X.values
        if hasattr(y, "values"):
            y = y.values

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64)

        self.n_features_in_ = X.shape[1]
        self.classes_ = np.unique(y)

        # Determine FFN hidden dimension (typically 2x or 4x d_embedding)
        ffn_dim = self.d_embedding * 2

        # Initialize network
        self.model_ = FTTransformerNet(
            num_features=self.n_features_in_,
            d_embedding=self.d_embedding,
            n_heads=self.n_heads,
            depth=self.depth,
            ffn_dim=ffn_dim,
            dropout=self.ffn_dropout,
        )

        # Setup optimizer and loss
        optimizer = optim.AdamW(
            self.model_.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        criterion = nn.CrossEntropyLoss()

        # Create dataset and loader
        dataset = TensorDataset(torch.tensor(X), torch.tensor(y))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self.model_.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                logits = self.model_(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

        self.model_.eval()
        self.model_state_ = self.model_.state_dict()
        return self

    def _ensure_model_loaded(self, num_features: int) -> None:
        """Lazily reconstruct the network from ``model_state_``.

        Called automatically before inference.  If the live ``model_``
        attribute is ``None`` (e.g. after unpickling), the network is
        rebuilt and its weights are restored from ``model_state_``.

        Parameters
        ----------
        num_features : int
            Number of input features (must match training dimensionality).
        """
        if self.model_ is None:
            ffn_dim = self.d_embedding * 2
            self.model_ = FTTransformerNet(
                num_features=num_features,
                d_embedding=self.d_embedding,
                n_heads=self.n_heads,
                depth=self.depth,
                ffn_dim=ffn_dim,
                dropout=self.ffn_dropout,
            )
            if self.model_state_ is not None:
                self.model_.load_state_dict(self.model_state_)
            self.model_.eval()

    def predict_proba(self, X):
        """Predict class probabilities for *X*.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Feature matrix.

        Returns
        -------
        ndarray of shape ``(n_samples, 2)``
            Predicted probabilities for each class.

        Raises
        ------
        sklearn.exceptions.NotFittedError
            If :meth:`fit` has not been called.
        """
        check_is_fitted(self, ["model_state_"])

        if hasattr(X, "values"):
            X = X.values

        X = np.array(X, dtype=np.float32)
        self._ensure_model_loaded(X.shape[1])

        self.model_.eval()
        with torch.no_grad():
            x_tensor = torch.tensor(X)
            logits = self.model_(x_tensor)
            probs = torch.softmax(logits, dim=1).numpy()

        return probs

    def predict(self, X):
        """Predict class labels for *X*.

        Parameters
        ----------
        X : array-like of shape ``(n_samples, n_features)``
            Feature matrix.

        Returns
        -------
        ndarray of shape ``(n_samples,)``
            Predicted class labels (integers).
        """
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

    # ------------------------------------------------------------------
    # Serialisation helpers (pickle-safe)
    # ------------------------------------------------------------------
    def __getstate__(self):
        """Exclude live PyTorch model from pickle serialisation."""
        state = self.__dict__.copy()
        if "model_" in state:
            state["model_"] = None
        return state

    def __setstate__(self, state):
        """Restore instance; model is lazily rebuilt on first inference."""
        self.__dict__.update(state)
        self.model_ = None
