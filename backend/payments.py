"""
Payments Module (Razorpay)
==========================
Handles order creation and signature verification.
"""
import os
import razorpay
import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from . import database, models, auth
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Razorpay Client
KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder") 
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

# --- Schemas ---
class OrderRequest(BaseModel):
    amount: int # In smallest currency unit (paise)
    currency: str = "INR"
    plan_id: str = "pro_monthly" # pro, clinic

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str

# --- Endpoints ---

@router.post("/create-order")
def create_order(
    req: OrderRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a Razorpay Order."""
    try:
        data = {
            "amount": req.amount,
            "currency": req.currency,
            "receipt": f"receipt_{current_user.id}_{datetime.now().timestamp()}",
            "notes": {
                "user_id": current_user.id,
                "plan": req.plan_id
            }
        }
        order = client.order.create(data=data)
        return {
            "id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": KEY_ID
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        # Verify Signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': req.razorpay_order_id,
            'razorpay_payment_id': req.razorpay_payment_id,
            'razorpay_signature': req.razorpay_signature
        })
        
        # If successful, update user
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        user.plan_tier = "pro" if "pro" in req.plan_id else "clinic"
        
        # Set expiry to 30 days from now (Mock logic, real recurring needs webhook)
        user.subscription_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        
        db.commit()
        
        return {"status": "success", "message": "Payment Verified", "tier": user.plan_tier}
        
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Signature Verification Failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
