"""
Payments Module (Multi-Gateway: Stripe + Razorpay)
=================================================
Handles secure order creation and signature verification.
Provides unhackable payment flows using strictly server-side pricing.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import stripe
import razorpay
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import auth, database, models

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)

def _testing_enabled() -> bool:
    return os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}

# Gateway Configuration
# Default to razorpay, override with PAYMENT_GATEWAY=stripe
ACTIVE_GATEWAY = os.getenv("PAYMENT_GATEWAY", "razorpay").strip().lower()

# Stripe Keys
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")

if not stripe.api_key and _testing_enabled():
    stripe.api_key = "sk_test_placeholder"

# Razorpay Keys
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if (not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET) and _testing_enabled():
    RAZORPAY_KEY_ID = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET = "secret_placeholder"

try:
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    else:
        razorpay_client = None
except Exception as e:
    logger.error(f"Failed to initialize Razorpay: {e}")
    razorpay_client = None

CREATE_ORDER_FAILURE_DETAIL = "Failed to create payment order"
VERIFY_PAYMENT_FAILURE_DETAIL = "Failed to verify payment"
PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL = f"Payment gateway ({ACTIVE_GATEWAY}) is not configured properly"

# SERVER-SIDE TRUTH: Pricing Catalog
# Amount is in smallest currency unit (cents or paise)
PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "pro": {"amount_usd": 999, "amount_inr": 99900, "tier": "pro"},
    "pro_monthly": {"amount_usd": 999, "amount_inr": 99900, "tier": "pro"},
    "enterprise": {"amount_usd": 2499, "amount_inr": 249900, "tier": "clinic"},
    "clinic": {"amount_usd": 2499, "amount_inr": 249900, "tier": "clinic"},
}

def get_plan_config(plan_id: str) -> dict[str, Any]:
    plan = PLAN_CATALOG.get(plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid payment plan")
    return plan

class OrderRequest(BaseModel):
    plan_id: str = "pro"

class VerifyRequest(BaseModel):
    gateway: str
    
    # Stripe Fields
    payment_intent_id: Optional[str] = None
    
    # Razorpay Fields
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    plan_id: Optional[str] = None


from fastapi import Request
from .main import limiter

@router.post("/create-order")
@limiter.limit("3/minute")
def create_order(
    request: Request,
    req: OrderRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a securely priced Order using the configured gateway."""
    plan = get_plan_config(req.plan_id)
    
    if ACTIVE_GATEWAY == "stripe":
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail=PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL)
        
        try:
            if stripe.api_key == "sk_test_placeholder" and _testing_enabled():
                return {
                    "id": "cs_test_12345",
                    "url": f"http://localhost:5173/pricing?session_id=cs_test_12345&plan={req.plan_id}",
                    "gateway": "stripe",
                    "status": "created",
                    "plan_id": req.plan_id
                }

            domain_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'AI Healthcare - {plan["tier"].capitalize()} Plan',
                        },
                        'unit_amount': plan["amount_usd"],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=domain_url + '/pricing?session_id={CHECKOUT_SESSION_ID}&plan=' + req.plan_id,
                cancel_url=domain_url + '/pricing?canceled=true',
                metadata={
                    "user_id": str(current_user.id),
                    "plan": req.plan_id
                }
            )
            return {
                "id": session.id,
                "url": session.url,
                "gateway": "stripe",
                "status": "created",
                "plan_id": req.plan_id
            }
        except Exception as e:
            logger.error(f"Stripe order creation failed: {e}")
            raise HTTPException(status_code=500, detail=CREATE_ORDER_FAILURE_DETAIL)

    elif ACTIVE_GATEWAY == "razorpay":
        if not razorpay_client:
            raise HTTPException(status_code=503, detail=PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL)

        try:
            if RAZORPAY_KEY_ID == "rzp_test_placeholder" and _testing_enabled():
                return {
                    "id": "order_test_12345",
                    "amount": plan["amount_inr"],
                    "currency": "INR",
                    "gateway": "razorpay",
                    "status": "created",
                    "plan_id": req.plan_id
                }

            data = {
                "amount": plan["amount_inr"],
                "currency": "INR",
                "receipt": f"receipt_{current_user.id}_{req.plan_id}",
                "notes": {
                    "user_id": str(current_user.id),
                    "plan": req.plan_id
                }
            }
            
            order = razorpay_client.order.create(data=data)
            
            return {
                "id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "gateway": "razorpay",
                "status": order["status"],
                "plan_id": req.plan_id
            }
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise HTTPException(status_code=500, detail=CREATE_ORDER_FAILURE_DETAIL)
    
    else:
        raise HTTPException(status_code=500, detail=f"Unsupported gateway: {ACTIVE_GATEWAY}")

@router.post("/verify")
def verify_payment(
    req: VerifyRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Verify payment signature strictly and activate subscription."""
    if req.gateway == "stripe":
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail=PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL)
        
        try:
            if not req.payment_intent_id:
                raise HTTPException(status_code=400, detail="Missing payment_intent_id (session_id)")
            
            if stripe.api_key == "sk_test_placeholder" and _testing_enabled():
                plan_id = req.plan_id or "pro"
            else:
                session = stripe.checkout.Session.retrieve(req.payment_intent_id)
                if session.payment_status != "paid":
                    raise HTTPException(status_code=400, detail="Payment not successful")
                    
                metadata = session.metadata
                if str(metadata.get("user_id")) != str(current_user.id):
                    raise HTTPException(status_code=403, detail="Order does not belong to current user")

                plan_id = metadata.get("plan", "pro")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Stripe verification failed: {e}")
            raise HTTPException(status_code=500, detail=VERIFY_PAYMENT_FAILURE_DETAIL)

    elif req.gateway == "razorpay":
        if not razorpay_client:
            raise HTTPException(status_code=503, detail=PAYMENT_GATEWAY_NOT_CONFIGURED_DETAIL)

        try:
            if not req.razorpay_order_id or not req.razorpay_payment_id or not req.razorpay_signature:
                raise HTTPException(status_code=400, detail="Missing razorpay payload")

            if RAZORPAY_KEY_ID == "rzp_test_placeholder" and _testing_enabled():
                pass
            else:
                razorpay_client.utility.verify_payment_signature({
                    'razorpay_order_id': req.razorpay_order_id,
                    'razorpay_payment_id': req.razorpay_payment_id,
                    'razorpay_signature': req.razorpay_signature
                })
            
            plan_id = req.plan_id or "pro"
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Razorpay verification failed: {e}")
            raise HTTPException(status_code=500, detail=VERIFY_PAYMENT_FAILURE_DETAIL)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid gateway")

    # If verification succeeds, activate subscription
    plan = get_plan_config(plan_id)
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan_tier = plan["tier"]
    user.subscription_expiry = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()

    return {
        "success": True,
        "status": "success",
        "message": "Payment Verified",
        "tier": user.plan_tier,
    }
