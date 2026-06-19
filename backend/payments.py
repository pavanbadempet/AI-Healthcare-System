"""
Payments Module (Razorpay)
==========================
Handles order creation and signature verification.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import razorpay
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import auth, database, models

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)

def _testing_enabled() -> bool:
    return os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}


def load_razorpay_credentials() -> tuple[str | None, str | None]:
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if key_id and key_secret:
        return key_id, key_secret
    if _testing_enabled():
        return "rzp_test_placeholder", "secret_placeholder"
    return None, None


KEY_ID, KEY_SECRET = load_razorpay_credentials()
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET)) if KEY_ID and KEY_SECRET else None

CREATE_ORDER_FAILURE_DETAIL = "Failed to create payment order"
VERIFY_PAYMENT_FAILURE_DETAIL = "Failed to verify payment"
PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL = "Payment gateway is not configured"

PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "pro": {"amount": 99900, "currency": "INR", "tier": "pro"},
    "pro_monthly": {"amount": 99900, "currency": "INR", "tier": "pro"},
    "enterprise": {"amount": 249900, "currency": "INR", "tier": "clinic"},
    "clinic": {"amount": 249900, "currency": "INR", "tier": "clinic"},
}


def get_plan_config(plan_id: str) -> dict[str, Any]:
    plan = PLAN_CATALOG.get(plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid payment plan")
    return plan


def get_payment_client():
    if client is None:
        raise HTTPException(status_code=503, detail=PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL)
    return client


def validate_order_for_user(order: dict[str, Any], current_user: models.User) -> dict[str, Any]:
    notes = order.get("notes") or {}
    plan_id = str(notes.get("plan") or "")
    plan = get_plan_config(plan_id)

    if str(notes.get("user_id")) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Payment order does not belong to current user")

    try:
        order_amount = int(order.get("amount"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Payment order amount mismatch")

    if order_amount != int(plan["amount"]) or str(order.get("currency", "")).upper() != plan["currency"]:
        raise HTTPException(status_code=400, detail="Payment order amount mismatch")

    return plan

# --- Schemas ---
class OrderRequest(BaseModel):
    plan_id: str = "pro"
    amount: Optional[int] = None
    currency: Optional[str] = None

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: Optional[str] = None

# --- Endpoints ---

@router.post("/create-order")
def create_order(
    req: OrderRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a Razorpay Order."""
    try:
        payment_client = get_payment_client()
        plan = get_plan_config(req.plan_id)
        data = {
            "amount": plan["amount"],
            "currency": plan["currency"],
            "receipt": f"receipt_{current_user.id}_{datetime.now().timestamp()}",
            "notes": {
                "user_id": str(current_user.id),
                "plan": req.plan_id
            }
        }
        order = payment_client.order.create(data=data)
        return {
            "id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "status": order.get("status", "created"),
            "plan_id": req.plan_id,
            "key_id": KEY_ID
        }
    except HTTPException:
        raise
    except Exception:
        logger.error("Payment order creation failed")
        raise HTTPException(status_code=500, detail=CREATE_ORDER_FAILURE_DETAIL)

@router.post("/verify")
def verify_payment(
    req: VerifyRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Verify signature and activate subscription.
    """
    try:
        payment_client = get_payment_client()
        # Verify Signature
        payment_client.utility.verify_payment_signature({
            'razorpay_order_id': req.razorpay_order_id,
            'razorpay_payment_id': req.razorpay_payment_id,
            'razorpay_signature': req.razorpay_signature
        })
        order = payment_client.order.fetch(req.razorpay_order_id)
        plan = validate_order_for_user(order, current_user)

        # If successful, update user
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.plan_tier = plan["tier"]

        # Set expiry to 30 days from now (Mock logic, real recurring needs webhook)
        user.subscription_expiry = datetime.now(timezone.utc) + timedelta(days=30)

        db.commit()

        return {
            "success": True,
            "status": "success",
            "message": "Payment Verified",
            "tier": user.plan_tier,
            "plan_tier": user.plan_tier,
        }

    except HTTPException:
        raise
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Signature Verification Failed")
    except Exception:
        logger.error("Payment verification failed")
        raise HTTPException(status_code=500, detail=VERIFY_PAYMENT_FAILURE_DETAIL)
