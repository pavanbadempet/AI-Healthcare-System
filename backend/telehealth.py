import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TelehealthSession:
    def __init__(
        self,
        session_id: str,
        patient_id: str,
        provider_id: str,
        room_name: str
    ):
        self.session_id = session_id
        self.patient_id = patient_id
        self.provider_id = provider_id
        self.room_name = room_name
        self.status = "scheduled"
        self.started_at: Optional[float] = None
        self.ended_at: Optional[float] = None
        self.duration_minutes: float = 0.0
        self.quality_log: Dict[str, Any] = {
            "packet_loss_percentage": 0.0,
            "average_latency_ms": 0.0,
            "quality_rating": "EXCELLENT"
        }

    def start_session(self) -> None:
        self.status = "active"
        self.started_at = time.time()
        logger.info(f"Telehealth session {self.session_id} is now ACTIVE.")

    def end_session(self, duration_minutes: Optional[float] = None) -> None:
        self.status = "completed"
        self.ended_at = time.time()
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        elif self.started_at:
            self.duration_minutes = round((self.ended_at - self.started_at) / 60.0, 2)
        else:
            self.duration_minutes = 0.0
        logger.info(f"Telehealth session {self.session_id} COMPLETED. Duration: {self.duration_minutes} mins.")

    def generate_webrtc_token(self, user_id: str, role: str) -> Dict[str, Any]:
        """
        Generates a compliant access token configuration for secure WebRTC/signaling connection.
        """
        import os
        import hashlib
        import jwt as pyjwt
        from datetime import datetime, timedelta
        from backend.auth import SECRET_KEY, ALGORITHM

        # 1. Build a real secure JWT token for WebRTC signaling
        token_payload = {
            "sub": str(user_id),
            "role": role,
            "room": self.room_name,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        access_token = "jwt-webrtc-" + pyjwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

        # 2. Build live ICE server credentials
        ice_servers = []
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

        if twilio_sid and twilio_token:
            try:
                import requests
                # Live Twilio Network Traversal API call
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Tokens.json"
                resp = requests.post(url, auth=(twilio_sid, twilio_token), timeout=4)
                if resp.status_code == 201:
                    data = resp.json()
                    ice_servers = data.get("ice_servers", [])
            except Exception as e:
                logger.warning("Twilio ICE token request failed: %s", e)

        if not ice_servers:
            # Fallback to standard secure public ICE servers and local STUN configs
            ice_servers = [
                {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
                {
                    "urls": ["turn:127.0.0.1:3478?transport=udp", "turn:127.0.0.1:3478?transport=tcp"],
                    "username": f"webrtc-user-{user_id}",
                    "credential": hashlib.sha256(f"{user_id}:turn-secret-key-xyz".encode()).hexdigest()[:16]
                }
            ]

        return {
            "room_name": self.room_name,
            "user_id": user_id,
            "role": role,
            "token_type": "Bearer WebRTC-Signaling",
            "access_token": access_token,
            "ice_servers": ice_servers,
            "expires_in_seconds": 3600
        }


    def audit_quality_metrics(self, packet_loss: float, latency_ms: float) -> Dict[str, Any]:
        """
        Records clinical network quality statistics to verify telehealth session SLA compliance.
        """
        rating = "EXCELLENT"
        if packet_loss > 5.0 or latency_ms > 250.0:
            rating = "POOR"
        elif packet_loss > 1.0 or latency_ms > 100.0:
            rating = "FAIR"
            
        self.quality_log = {
            "packet_loss_percentage": packet_loss,
            "average_latency_ms": latency_ms,
            "quality_rating": rating
        }
        return self.quality_log
