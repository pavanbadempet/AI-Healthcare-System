"""FHIR Subscription and Webhook Dispatcher.

Enables client applications to register webhooks for clinical events
(e.g., vital observations recorded) and dispatches async FHIR notifications.
"""

import logging
import threading
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

# Thread-safe in-memory subscription registry
_subscriptions_lock = threading.Lock()
_subscriptions: List[Dict[str, Any]] = []

def clear_subscriptions() -> None:
    """Clears all registered subscriptions (useful for unit tests)."""
    with _subscriptions_lock:
        _subscriptions.clear()

def register_fhir_subscription(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registers a new FHIR Subscription resource.
    Example payload:
    {
        "resourceType": "Subscription",
        "status": "requested",
        "criteria": "Observation?code=8867-4",
        "channel": {
            "type": "rest-hook",
            "endpoint": "http://example.com/callback",
            "payload": "application/fhir+json"
        }
    }
    """
    if payload.get("resourceType") != "Subscription":
        raise ValueError("Invalid resourceType: must be Subscription")

    criteria = payload.get("criteria", "")
    channel = payload.get("channel", {})
    endpoint = channel.get("endpoint", "")
    channel_type = channel.get("type", "")

    if not criteria or not endpoint or channel_type != "rest-hook":
        raise ValueError("Subscription must specify 'criteria' and a 'rest-hook' channel endpoint")

    subscription_id = f"sub-{len(_subscriptions) + 1}"
    registered_sub = {
        "resourceType": "Subscription",
        "id": subscription_id,
        "status": "active",
        "criteria": criteria,
        "channel": {
            "type": "rest-hook",
            "endpoint": endpoint,
            "payload": channel.get("payload", "application/fhir+json")
        }
    }

    with _subscriptions_lock:
        _subscriptions.append(registered_sub)

    return registered_sub

def get_active_subscriptions() -> List[Dict[str, Any]]:
    """Returns a list of all active registered subscriptions."""
    with _subscriptions_lock:
        return list(_subscriptions)

def _async_dispatch(endpoint: str, payload: Dict[str, Any]) -> None:
    """Helper to execute the webhook POST in a background thread."""
    try:
        res = requests.post(endpoint, json=payload, timeout=5)
        logger.info("Subscription webhook dispatched to %s, status: %d", endpoint, res.status_code)
    except Exception as e:
        logger.error("Failed to dispatch subscription webhook to %s: %s", endpoint, e)

def dispatch_observation_notifications(patient_id: int, observation_id: int, vitals_dict: Dict[str, float]) -> int:
    """
    Evaluates active subscriptions against a new vital observation event.
    Triggers asynchronous background notifications to matching endpoints.
    """
    subs = get_active_subscriptions()
    dispatched_count = 0

    for sub in subs:
        criteria = sub["criteria"]
        endpoint = sub["channel"]["endpoint"]

        # Parse criteria (e.g. "Observation" or "Observation?code=8867-4")
        match = False
        if criteria == "Observation":
            match = True
        elif "Observation?code=" in criteria:
            target_code = criteria.split("code=")[-1].strip()
            
            # Vital sign code mapping (LOINC)
            loinc_map = {
                "heart_rate": "8867-4",
                "systolic_bp": "8480-6",
                "diastolic_bp": "8462-4",
                "spo2": "59408-5",
                "temperature_c": "8310-5",
                "respiratory_rate": "9279-1",
                "blood_glucose": "2339-0"
            }
            
            # Check if the target vital sign was populated in this observation
            for key, code in loinc_map.items():
                if code == target_code and vitals_dict.get(key) is not None:
                    match = True
                    break

        if match:
            # Construct a FHIR Observation representation for the payload
            fhir_observation = {
                "resourceType": "Observation",
                "id": str(observation_id),
                "status": "final",
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "component": []
            }

            # Map the vitals to FHIR components
            for key, val in vitals_dict.items():
                if val is None:
                    continue
                # Mapping code to system/display
                # In standard FHIR, observations can have multiple components or values
                fhir_observation["component"].append({
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": key,  # Simplifying representation for interop tests
                        }]
                    },
                    "valueQuantity": {
                        "value": val
                    }
                })

            # Fire the webhook asynchronously
            threading.Thread(
                target=_async_dispatch,
                args=(endpoint, fhir_observation),
                daemon=True
            ).start()
            dispatched_count += 1

    return dispatched_count
