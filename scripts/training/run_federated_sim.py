#!/usr/bin/env python
"""
AI Healthcare System — Federated Learning DP-FedAvg Simulator

Simulates collaborative model training (Diabetes risk) across 3 local hospital nodes
using a central coordinator, aggregating weights with Laplace Differential Privacy (DP).
"""

import numpy as np
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def sigmoid(z):
    return 1 / (np.exp(-np.clip(z, -25, 25)) + 1)

class LocalHospitalNode:
    """Simulates a decentralized clinical client node with its own private patient data."""
    def __init__(self, node_id, X, y):
        self.node_id = node_id
        self.X = X
        self.y = y.reshape(-1, 1)
        self.num_records = len(X)

    def compute_gradients(self, W, b, clip_value=1.0):
        """Compute local gradients on private data and clip them for DP."""
        N = self.num_records
        if N == 0:
            return np.zeros_like(W), 0.0

        # Sigmoid predictions
        predictions = sigmoid(np.dot(self.X, W) + b)

        # Loss gradient
        error = predictions - self.y
        dW = np.dot(self.X.T, error) / N
        db = np.sum(error) / N

        # L2 Clip gradients to enforce sensitivity
        l2_norm = np.linalg.norm(dW)
        if l2_norm > clip_value:
            dW = dW * (clip_value / l2_norm)

        if abs(db) > clip_value:
            db = db * (clip_value / abs(db))

        return dW, db

class FederatedCoordinator:
    """Central coordinator aggregating noisy client updates."""
    def __init__(self, num_features, epsilon=1.5, sensitivity=1.0):
        self.W = np.zeros((num_features, 1))
        self.b = 0.0
        self.epsilon = epsilon
        self.sensitivity = sensitivity

    def add_laplace_noise(self, val, num_records):
        """Inject Laplace noise for Differential Privacy."""
        if num_records <= 0:
            return val
        scale = self.sensitivity / (num_records * self.epsilon)
        # Laplace noise using numpy
        noise = np.random.laplace(0, scale, size=val.shape)
        return val + noise

    def aggregate_updates(self, client_updates):
        """Aggregate clipped, noisy gradients using FedAvg."""
        total_records = sum(c["num_records"] for c in client_updates)
        if total_records == 0:
            return

        avg_dW = np.zeros_like(self.W)
        avg_db = 0.0

        for client in client_updates:
            # Inject DP noise to the clipped local gradients at the client side
            noisy_dW = self.add_laplace_noise(client["dW"], client["num_records"])
            noisy_db = self.add_laplace_noise(client["db"], client["num_records"])

            # Weighted aggregation
            weight = client["num_records"] / total_records
            avg_dW += noisy_dW * weight
            avg_db += noisy_db * weight

        # Update global parameters (Gradient Descent step)
        learning_rate = 0.5
        self.W -= learning_rate * avg_dW
        self.b -= learning_rate * avg_db

    def predict(self, X):
        probs = sigmoid(np.dot(X, self.W) + self.b)
        return (probs >= 0.5).astype(int)

def run_simulation(epochs=10, epsilon=1.5, sensitivity=1.0):
    print("=" * 60)
    print("  FEDERATED PRIVACY MESH SIMULATOR (DP-FedAvg)  ")
    print("=" * 60)

    # 1. Generate synthetic clinical dataset (Diabetes classification)
    # 5 features: Age, BMI, Hypertension, HeartDisease, Glucose
    X, y = make_classification(
        n_samples=600,
        n_features=5,
        n_informative=4,
        n_redundant=1,
        random_state=42
    )

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Split training set among 3 hospital clients
    hospital_data = np.array_split(np.arange(len(X_train)), 3)
    clients = []
    for i, idxs in enumerate(hospital_data):
        client = LocalHospitalNode(
            node_id=f"hospital-node-0{i+1}",
            X=X_train[idxs],
            y=y_train[idxs]
        )
        print(f"Node initialized: {client.node_id} with {client.num_records} private records.")
        clients.append(client)

    # 2. Central Centralized training (Baseline - No DP, No Federation)
    # Just simple gradient descent on full training set
    W_central = np.zeros((5, 1))
    b_central = 0.0
    for epoch in range(epochs):
        predictions = sigmoid(np.dot(X_train, W_central) + b_central)
        error = predictions - y_train.reshape(-1, 1)
        dW = np.dot(X_train.T, error) / len(X_train)
        db = np.sum(error) / len(X_train)
        W_central -= 0.5 * dW
        b_central -= 0.5 * db

    y_pred_central = (sigmoid(np.dot(X_val, W_central) + b_central) >= 0.5).astype(int)
    acc_central = accuracy_score(y_val, y_pred_central)
    print(f"\nBaseline Centralized Model Accuracy (No DP): {acc_central * 100:.2f}%")

    # 3. Federated Training with Differential Privacy
    coordinator = FederatedCoordinator(num_features=5, epsilon=epsilon, sensitivity=sensitivity)
    print(f"Federated training started with privacy budget epsilon={epsilon}...")

    epoch_history = []
    for epoch in range(epochs):
        client_updates = []
        for client in clients:
            dW, db = client.compute_gradients(coordinator.W, coordinator.b, clip_value=sensitivity)
            client_updates.append({
                "dW": dW,
                "db": db,
                "num_records": client.num_records
            })

        coordinator.aggregate_updates(client_updates)

        # Intermediate eval
        y_pred_fed = coordinator.predict(X_val)
        acc_fed = accuracy_score(y_val, y_pred_fed)
        epoch_history.append(float(acc_fed))
        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Validation Accuracy: {acc_fed * 100:.2f}%")

    print("\n" + "=" * 60)
    print("  SIMULATION RESULTS SUMMARY  ")
    print("=" * 60)
    print(f"Centralized Model Accuracy (Baseline): {acc_central * 100:.2f}%")
    print(f"Federated DP Model Accuracy:           {acc_fed * 100:.2f}%")
    print(f"Differential Privacy Parameters:       epsilon={epsilon}, sensitivity={sensitivity}")
    print("Privacy protection: Local gradients clipped and Laplace noise added.")
    print("=" * 60)

    return {
        "acc_central": float(acc_central),
        "acc_federated": float(acc_fed),
        "history": epoch_history
    }

if __name__ == "__main__":
    run_simulation()
