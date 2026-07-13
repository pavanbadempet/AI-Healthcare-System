"""B2B License Keygen Server for LemonSqueezy / Gumroad webhook integration.

Enables automated sale and cryptographic delivery of licensing keys with $0 setup cost.
"""

import hashlib
import hmac
import json
import logging
import os
import sys

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

# Add repository root to python path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend import licensing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keygen_server")

app = FastAPI(title="AI Healthcare System - B2B License Delivery Server")

# Load environment configuration
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "healthcare-admin-keygen-secret-2026")
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")

# Product/Variant ID to Tier mappings
# Users can configure these in their LemonSqueezy/Gumroad dashboard and match here
VARIANT_TO_TIER_MAP = {
    os.getenv("LEMONSQUEEZY_COMMUNITY_VARIANT_ID", "variant_comm_123"): "community",
    os.getenv("LEMONSQUEEZY_ENTERPRISE_VARIANT_ID", "variant_ent_456"): "enterprise",
}


class ManualKeyRequest(BaseModel):
    holder: str
    tier: str  # "trial", "community", "enterprise"
    days_valid: int


def verify_admin_key(x_api_key: str = Header(None)):
    """Protects admin endpoints."""
    if not x_api_key or x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "keygen-server"}


@app.post("/manual-generate")
def manual_generate(payload: ManualKeyRequest, _=Depends(verify_admin_key)):
    """Generate license keys manually via API."""
    if payload.tier not in ["trial", "community", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid tier level")

    key = licensing.generate_license_key(holder=payload.holder, tier=payload.tier, days_valid=payload.days_valid)
    return {"holder": payload.holder, "tier": payload.tier, "days_valid": payload.days_valid, "license_key": key}


@app.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, x_signature: str = Header(None)):
    """Receives purchase callbacks from LemonSqueezy and generates cryptographic keys."""
    if not LEMONSQUEEZY_WEBHOOK_SECRET:
        logger.error("LEMONSQUEEZY_WEBHOOK_SECRET is not configured in env")
        raise HTTPException(status_code=500, detail="Webhook validation secret is unconfigured")

    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing X-Signature header")

    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    local_hash = hmac.new(LEMONSQUEEZY_WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(local_hash, x_signature):
        logger.warning("Invalid webhook signature received")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    meta = payload.get("meta", {})
    event_name = meta.get("event_name")

    # Process only completed orders or subscriptions
    if event_name not in ["order_created", "subscription_created"]:
        return {"status": "skipped", "reason": f"Event {event_name} ignored"}

    data = payload.get("data", {})
    attributes = data.get("attributes", {})

    variant_id = str(attributes.get("variant_id"))
    customer_email = attributes.get("user_email") or attributes.get("customer_email") or "Client"
    customer_name = attributes.get("user_name") or attributes.get("customer_name") or customer_email

    # Map variant ID to license tier (defaulting to community if unknown)
    tier = VARIANT_TO_TIER_MAP.get(variant_id, "community")

    # Order/Subscription duration: default to 365 days (1 year)
    days_valid = 365

    # Generate key
    license_key = licensing.generate_license_key(holder=customer_name, tier=tier, days_valid=days_valid)

    logger.info(
        "AUTOMATED LICENSE ISSUED: Event=%s, Holder=%s, Email=%s, Tier=%s, Key=%s",
        event_name,
        customer_name,
        customer_email,
        tier,
        license_key,
    )

    # In production, integrate here with SendGrid, Resend, or your email server
    # to mail the license key automatically. For now, we log it so it is retrievable.

    return {
        "status": "success",
        "issued_to": customer_name,
        "email": customer_email,
        "tier": tier,
        "license_key": license_key,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
