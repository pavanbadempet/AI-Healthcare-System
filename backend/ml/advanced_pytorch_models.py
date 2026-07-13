import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from torch.utils.data import DataLoader, TensorDataset


class NumericalFeatureTokenizer(nn.Module):
    """
    Tokenizes numerical features by projecting each feature value into an embedding space.
    """
    def __init__(self, num_features, d_embedding):
        super().__init__()
        # Each feature gets its own weights and bias for linear projection
        self.weights = nn.Parameter(torch.randn(num_features, d_embedding))
        self.biases = nn.Parameter(torch.randn(num_features, d_embedding))

    def forward(self, x):
        # x shape: (batch_size, num_features)
        # We want to multiply each feature x[:, i] by self.weights[i] and add self.biases[i]
        # Reshape to (batch_size, num_features, 1)
        x_unsqueezed = x.unsqueeze(-1)
        # Project: (batch_size, num_features, 1) * (num_features, d_embedding)
        # Using broadcasting: weights shape (num_features, d_embedding)
        tokens = x_unsqueezed * self.weights.unsqueeze(0) + self.biases.unsqueeze(0)
        return tokens  # Shape: (batch_size, num_features, d_embedding)

class TransformerEncoderBlock(nn.Module):
    """
    Standard Transformer encoder block with Multi-Head Attention and Pre-LN.
    """
    def __init__(self, d_embedding, n_heads, ffn_dim, dropout=0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_embedding)
        self.mha = nn.MultiheadAttention(
            embed_dim=d_embedding,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True
        )
        self.dropout1 = nn.Dropout(dropout)

        self.ln2 = nn.LayerNorm(d_embedding)
        self.ffn = nn.Sequential(
            nn.Linear(d_embedding, ffn_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_dim, d_embedding)
        )
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x):
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
    """
    PyTorch Neural Network for Feature Tokenizer Transformer (FT-Transformer).
    """
    def __init__(self, num_features, d_embedding=32, n_heads=2, depth=2, ffn_dim=64, dropout=0.1):
        super().__init__()
        self.tokenizer = NumericalFeatureTokenizer(num_features, d_embedding)

        # [CLS] token representation
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_embedding))

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerEncoderBlock(d_embedding, n_heads, ffn_dim, dropout)
            for _ in range(depth)
        ])

        self.ln_final = nn.LayerNorm(d_embedding)

        # Binary classification head: maps CLS output to 2 classes (logits)
        self.head = nn.Linear(d_embedding, 2)

    def forward(self, x):
        # x shape: (batch_size, num_features)
        batch_size = x.shape[0]

        # Tokenize features
        tokens = self.tokenizer(x)  # Shape: (batch_size, num_features, d_embedding)

        # Expand [CLS] token to match batch size
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)  # Shape: (batch_size, 1, d_embedding)

        # Prepend [CLS] token to feature tokens
        tokens = torch.cat([cls_tokens, tokens], dim=1)  # Shape: (batch_size, num_features + 1, d_embedding)

        # Apply Transformer blocks
        for layer in self.layers:
            tokens = layer(tokens)

        # Final layer normalization
        tokens = self.ln_final(tokens)

        # Extract the output of the CLS token
        cls_output = tokens[:, 0]  # Shape: (batch_size, d_embedding)

        # Output logits
        logits = self.head(cls_output)  # Shape: (batch_size, 2)
        return logits

class FTTransformerClassifier(ClassifierMixin, BaseEstimator):
    """
    scikit-learn compliant wrapper for PyTorch FT-Transformer.
    """
    def __init__(self, d_embedding=32, n_heads=2, depth=2, ffn_dropout=0.1, lr=0.001, epochs=10, batch_size=512, weight_decay=1e-4):
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
            dropout=self.ffn_dropout
        )

        # Setup optimizer and loss
        optimizer = optim.AdamW(self.model_.parameters(), lr=self.lr, weight_decay=self.weight_decay)
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

    def _ensure_model_loaded(self, num_features):
        if self.model_ is None:
            ffn_dim = self.d_embedding * 2
            self.model_ = FTTransformerNet(
                num_features=num_features,
                d_embedding=self.d_embedding,
                n_heads=self.n_heads,
                depth=self.depth,
                ffn_dim=ffn_dim,
                dropout=self.ffn_dropout
            )
            if self.model_state_ is not None:
                self.model_.load_state_dict(self.model_state_)
            self.model_.eval()

    def predict_proba(self, X):
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
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

    def __getstate__(self):
        state = self.__dict__.copy()
        if "model_" in state:
            state["model_"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.model_ = None
