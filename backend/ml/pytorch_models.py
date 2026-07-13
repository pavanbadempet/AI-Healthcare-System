import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.base import BaseEstimator, ClassifierMixin
from torch.utils.data import DataLoader, TensorDataset


class PyTorchTabularMLP(ClassifierMixin, BaseEstimator):
    def __init__(self, input_dim=None, hidden_dims=[64, 32], lr=0.005, epochs=150, batch_size=128, weight_decay=1e-4, dropout=0.1):
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

    def _build_model(self, input_dim):
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

        optimizer = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
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

    def _ensure_model_loaded(self, X_shape_1):
        if self.model is None:
            self.model = self._build_model(X_shape_1)
            if self.model_state_ is not None:
                self.model.load_state_dict(self.model_state_)
            self.model.eval()

    def predict_proba(self, X):
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
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

    def __getstate__(self):
        state = self.__dict__.copy()
        if "model" in state:
            state["model"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.model = None
