import datetime
import logging
from typing import Dict, Optional, Tuple

import jwt
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class LicenseManager:
    """Offline cryptographic license key verification manager."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        trial_keys: Optional[Dict[str, Dict[str, str]]] = None,
        tier_hierarchy: Optional[Dict[str, int]] = None,
        env_var_name: str = "LICENSE_KEY",
        testing_env_var: str = "TESTING",
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.trial_keys = trial_keys or {}
        self.tier_hierarchy = tier_hierarchy or {"trial": 0, "community": 1, "enterprise": 2}
        self.env_var_name = env_var_name
        self.testing_env_var = testing_env_var

    def verify_license_key(self, license_key: str) -> Tuple[bool, str]:
        """Verify the validity of a license key.

        Returns:
            (is_valid: bool, reason_or_holder: str)
        """
        # 1. Check trial keys
        if license_key in self.trial_keys:
            details = self.trial_keys[license_key]
            expires_at = details.get("expires_at")
            if expires_at:
                try:
                    expiry = datetime.datetime.fromisoformat(expires_at)
                    if datetime.datetime.now() > expiry:
                        return False, f"Trial key expired on {expires_at}"
                except Exception:
                    return False, "Trial key expiration date is invalid"
            return True, f"Valid Trial License (Holder: {details.get('holder', 'Trial')})"

        # 2. Decode cryptographical key
        try:
            payload = jwt.decode(license_key, self.secret_key, algorithms=[self.algorithm])
            holder = payload.get("holder", "Unknown Licensee")
            tier = payload.get("tier", "community")
            return True, f"Valid {tier.capitalize()} License (Holder: {holder})"
        except jwt.ExpiredSignatureError:
            return False, "License expired"
        except jwt.PyJWTError as e:
            logger.error("Cryptographic license verification failed: %s", str(e))
            return False, "Cryptographic signature validation failed"

    def generate_license_key(self, holder: str, tier: str, days_valid: int) -> str:
        """Utility to generate a signed license key for a customer."""
        expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_valid)
        payload = {
            "holder": holder,
            "tier": tier,
            "exp": int(expiry.timestamp()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def get_active_license_tier(self) -> str:
        """Retrieve the tier of the currently configured license key.

        Returns 'none' if no valid license key is configured.
        """
        import os

        license_key = os.getenv(self.env_var_name, "").strip()
        if not license_key:
            return "none"

        if license_key in self.trial_keys:
            details = self.trial_keys[license_key]
            expires_at = details.get("expires_at")
            if expires_at:
                try:
                    expiry = datetime.datetime.fromisoformat(expires_at)
                    if datetime.datetime.now() > expiry:
                        return "none"
                except Exception:
                    return "none"
            return details.get("tier", "trial")

        try:
            payload = jwt.decode(license_key, self.secret_key, algorithms=[self.algorithm])
            return payload.get("tier", "community")
        except jwt.PyJWTError:
            return "none"

    def enforce_license_tier(self, required_tier: str):
        """Dependency helper to enforce a minimum license tier for specific endpoints."""
        import os

        def dependency():
            # During unit testing of general app paths, we can bypass general check if TESTING is active.
            if os.getenv(self.testing_env_var) == "1" or os.getenv(self.testing_env_var) == "true":
                return

            tier = self.get_active_license_tier()
            if tier == "none":
                raise HTTPException(
                    status_code=402,
                    detail="License Key is missing or invalid. Please configure a valid license key.",
                )

            user_level = self.tier_hierarchy.get(tier, 0)
            required_level = self.tier_hierarchy.get(required_tier, 1)

            if user_level < required_level:
                raise HTTPException(
                    status_code=402,
                    detail=f"This premium feature requires a minimum license tier of '{required_tier}'. Your active tier is '{tier}'.",
                )

        return dependency
