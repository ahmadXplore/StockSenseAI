# StockSense AI — Model Registry & Artifact Store

## 1. Registry Architecture
The `ModelRegistry` tracks model state transitions across six distinct lifecycle stages:
- `TRAINING`: Model is undergoing training or validation.
- `VALIDATED`: Model passed out-of-sample and walk-forward validation gates.
- `STAGED`: Model is designated as a candidate for deployment.
- `DEPLOYED`: Model is currently active in production serving inference.
- `RETIRED`: Model has been superseded or degraded.
- `FAILED`: Model training failed data sufficiency or quality checks.

---

## 2. Artifact Integrity & Storage
- Model binaries are serialized via `joblib` into `backend/storage/models/{model_id}.joblib`.
- A SHA-256 integrity hash is computed and stored alongside the model record.
- During deserialization, the SHA-256 checksum is verified against disk contents to guarantee tamper-proof execution.
