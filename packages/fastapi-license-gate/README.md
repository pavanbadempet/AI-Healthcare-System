# FastAPI License Gate

`fastapi-license-gate` is a highly customizable, offline-first cryptographic B2B licensing validation layer and tier-enforcement utility for B2B self-hosted/on-premise deployments built on top of FastAPI.

It uses JSON Web Tokens (JWT) signed with a secret key (HS256) to verify license validity, client details, expiration timestamps, and active tiers—completely offline, without making calls to a central licensing server.

## Features

- **Offline-First Cryptographic Licensing**: Validates signed JWT keys locally at startup and during request dispatching.
- **Tier-Based Access Control**: Easily enforce required license tiers (`trial` < `community` < `enterprise`) on specific router paths.
- **Flexible Path Exclusions**: Exempt specific endpoints (e.g. login, signup, health check, docs) from global licensing restrictions.
- **FastAPI Middleware Integration**: Reusable middleware class that plugs directly into standard FastAPI applications.

## Installation

Install the package via pip:

```bash
pip install fastapi-license-gate
```

## Quick Start

### 1. Initialize the License Manager

Create a license manager instance with your custom B2B tiers, secret key, and trial bypass parameters:

```python
from fastapi_license_gate import LicenseManager

# Configure B2B tiers and pre-approved offline trial keys
trial_keys = {
    "TRIAL-KEY-2026": {
        "holder": "Acme Corp (Trial)",
        "tier": "trial",
        "expires_at": "2026-12-31"
    }
}

license_manager = LicenseManager(
    secret_key="your-super-secret-signing-key",
    algorithm="HS256",
    trial_keys=trial_keys,
    tier_hierarchy={"trial": 0, "community": 1, "enterprise": 2},
    env_var_name="LICENSE_KEY",
    testing_env_var="TESTING"
)
```

### 2. Register Middleware in FastAPI

Register the validation middleware early in your FastAPI application lifecycle:

```python
from fastapi import FastAPI
from fastapi_license_gate import LicenseValidationMiddleware

app = FastAPI()

app.add_middleware(
    LicenseValidationMiddleware,
    license_manager=license_manager,
    exclude_paths=["/", "/healthz", "/docs", "/openapi.json", "/v1/signup", "/v1/token"],
    exclude_prefixes=["/assets", "/static"]
)
```

### 3. Enforce Tier Gating on Specific Endpoints

Protect premium routes using the `enforce_license_tier` FastAPI dependency helper:

```python
from fastapi import Depends, APIRouter

router = APIRouter()

# Telemetry snapshot requires enterprise tier
@router.get("/telemetry", dependencies=[Depends(license_manager.enforce_license_tier("enterprise"))])
def get_telemetry():
    return {"status": "ok", "telemetry_data": []}

# Basic report generator requires community tier
@router.get("/report", dependencies=[Depends(license_manager.enforce_license_tier("community"))])
def get_report():
    return {"report_url": "https://..."}
```

### 4. Key Provisioning (Generating Customer Keys)

You can generate cryptographically signed client keys using the utility function. Run this inside an interactive Python shell or your licensing portal:

```python
# Generate a community license key for "Hospital Alpha" valid for 365 days
key = license_manager.generate_license_key(
    holder="Hospital Alpha",
    tier="community",
    days_valid=365
)
print(key)
# Outputs a cryptographically signed JWT key that the customer configures in their .env
```

## Running Tests

To run the unit tests of the package:

```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
