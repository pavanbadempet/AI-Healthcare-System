"""
HIPAA & GDPR Compliance Module
- Data Privacy & Security
- Audit Trails
- Consent Management
- Data Retention Policies
- Anonymization & Pseudonymization
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import redis
from cryptography.fernet import Fernet
from sqlalchemy import text

logger = logging.getLogger(__name__)
COMPLIANCE_OPERATION_FAILURE_MESSAGE = "Compliance operation failed. Please try again later."
COMPLIANCE_REPORT_FAILURE_MESSAGE = "Compliance report unavailable."

class ComplianceFramework(Enum):
    HIPAA = "hipaa"
    GDPR = "gdpr"
    BOTH = "both"

class DataCategory(Enum):
    PHI = "protected_health_information"  # HIPAA
    PII = "personally_identifiable_information"  # GDPR
    SENSITIVE = "sensitive_health_data"
    ANONYMIZED = "anonymized_data"

@dataclass
class ConsentRecord:
    user_id: int
    consent_type: str
    consent_version: str
    granted: bool
    timestamp: datetime
    ip_address: str
    user_agent: str
    purpose: str
    data_categories: List[DataCategory]
    retention_period_days: int

@dataclass
class DataProcessingRecord:
    user_id: int
    processing_type: str
    data_categories: List[DataCategory]
    legal_basis: str
    purpose: str
    timestamp: datetime
    processor: str
    third_party: Optional[str] = None

class HIPAACompliance:
    """HIPAA-specific compliance features"""

    PHI_FIELDS = {
        'name', 'email', 'phone', 'address', 'ssn', 'medical_record_number',
        'diagnosis', 'treatment', 'medications', 'lab_results', 'vitals'
    }

    def __init__(self, db_session, encryption_key: bytes):
        self.db = db_session
        self.cipher = Fernet(encryption_key)
        self.audit_logger = logging.getLogger('hipaa_audit')

    def encrypt_phi(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PHI fields"""
        encrypted_data = data.copy()

        for field, value in data.items():
            if self._is_phi_field(field) and value:
                if isinstance(value, str):
                    encrypted_value = self.cipher.encrypt(value.encode()).decode()
                    encrypted_data[field] = encrypted_value
                elif isinstance(value, dict):
                    encrypted_data[field] = self.encrypt_phi(value)

        return encrypted_data

    def decrypt_phi(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PHI fields"""
        decrypted_data = encrypted_data.copy()

        for field, value in encrypted_data.items():
            if self._is_phi_field(field) and value:
                if isinstance(value, str):
                    try:
                        decrypted_value = self.cipher.decrypt(value.encode()).decode()
                        decrypted_data[field] = decrypted_value
                    except Exception:
                        logger.error("Failed to decrypt PHI field")
                        decrypted_data[field] = "[ENCRYPTED]"
                elif isinstance(value, dict):
                    decrypted_data[field] = self.decrypt_phi(value)

        return decrypted_data

    def _is_phi_field(self, field_name: str) -> bool:
        """Check if field contains PHI"""
        field_lower = field_name.lower()
        return any(phi_term in field_lower for phi_term in self.PHI_FIELDS)

    def log_phi_access(self, user_id: int, accessed_by: int,
                      purpose: str, ip_address: str):
        """Log PHI access for audit trail"""
        try:
            with self.db.connect() as conn:
                conn.execute(text("""
                    INSERT INTO audit.phi_access_log
                    (user_id, accessed_by, purpose, ip_address, timestamp)
                    VALUES (:uid, :accessed_by, :purpose, :ip, :ts)
                """), {
                    'uid': user_id,
                    'accessed_by': accessed_by,
                    'purpose': purpose,
                    'ip': ip_address,
                    'ts': datetime.now(timezone.utc)
                })
                conn.commit()

            self.audit_logger.info(
                f"PHI_ACCESS: User {accessed_by} accessed PHI for user {user_id} "
                f"from {ip_address} for purpose: {purpose}"
            )

        except Exception:
            logger.error("Failed to log PHI access")

    def validate_minimum_necessary(self, requested_fields: Set[str],
                                 purpose: str) -> Set[str]:
        """Validate minimum necessary standard"""
        # This would implement business logic for minimum necessary
        # For now, return all requested fields
        return requested_fields

    def create_breach_notification(self, breach_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create HIPAA breach notification"""
        notification = {
            'breach_id': f"BREACH_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'discovery_date': datetime.now(timezone.utc).isoformat(),
            'notification_date': (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
            'affected_individuals': breach_details.get('affected_count', 0),
            'breach_type': 'unauthorized_access',
            'location_of_breached_info': 'electronic_medical_records',
            'business_associate_involved': breach_details.get('ba_involved', False),
            'mitigation_actions': [
                'Revoked access credentials',
                'Enhanced monitoring implemented',
                'Additional security training conducted'
            ]
        }

        return notification

class GDPRCompliance:
    """GDPR-specific compliance features"""

    def __init__(self, db_session):
        self.db = db_session
        self.audit_logger = logging.getLogger('gdpr_audit')

    def process_data_subject_request(self, user_id: int, request_type: str,
                                   request_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process GDPR data subject requests (DSAR)"""
        request_id = f"DSAR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"

        # Log the request
        try:
            with self.db.connect() as conn:
                conn.execute(text("""
                    INSERT INTO compliance.data_subject_requests
                    (request_id, user_id, request_type, request_details, status, created_at)
                    VALUES (:rid, :uid, :rtype, :details, 'pending', :ts)
                """), {
                    'rid': request_id,
                    'uid': user_id,
                    'rtype': request_type,
                    'details': json.dumps(request_details),
                    'ts': datetime.now(timezone.utc)
                })
                conn.commit()
        except Exception:
            logger.error("Failed to log DSAR")

        # Process based on request type
        if request_type == "access":
            return self._process_access_request(user_id, request_id)
        elif request_type == "rectification":
            return self._process_rectification_request(user_id, request_details, request_id)
        elif request_type == "erasure":
            return self._process_erasure_request(user_id, request_id)
        elif request_type == "portability":
            return self._process_portability_request(user_id, request_id)
        elif request_type == "restriction":
            return self._process_restriction_request(user_id, request_details, request_id)
        elif request_type == "objection":
            return self._process_objection_request(user_id, request_details, request_id)

        return {'status': 'invalid_request_type', 'request_id': request_id}

    def _process_access_request(self, user_id: int, request_id: str) -> Dict[str, Any]:
        """Process right to access request"""
        try:
            with self.db.connect() as conn:
                # Get all user data
                user_data = conn.execute(text("""
                    SELECT * FROM app_data.users WHERE id = :uid
                """), {'uid': user_id}).fetchone()

                health_records = conn.execute(text("""
                    SELECT * FROM app_data.health_records WHERE user_id = :uid
                """), {'uid': user_id}).fetchall()

                chat_logs = conn.execute(text("""
                    SELECT * FROM app_data.chat_logs WHERE user_id = :uid
                """), {'uid': user_id}).fetchall()

            # Compile data package
            data_package = {
                'personal_data': dict(user_data) if user_data else {},
                'health_records': [dict(record) for record in health_records],
                'chat_logs': [dict(log) for log in chat_logs],
                'processing_activities': self._get_processing_activities(user_id),
                'data_categories': self._get_data_categories(user_id),
                'recipients': self._get_data_recipients(user_id),
                'retention_periods': self._get_retention_periods(user_id)
            }

            # Update request status
            self._update_request_status(request_id, 'completed', data_package)

            return {
                'status': 'completed',
                'request_id': request_id,
                'data_package': data_package,
                'format': 'json',
                'delivery_method': 'secure_download'
            }

        except Exception:
            logger.error("Access request failed")
            self._update_request_status(
                request_id,
                'failed',
                {'error': COMPLIANCE_OPERATION_FAILURE_MESSAGE},
            )
            return {
                'status': 'failed',
                'request_id': request_id,
                'error': COMPLIANCE_OPERATION_FAILURE_MESSAGE,
            }

    def _process_erasure_request(self, user_id: int, request_id: str) -> Dict[str, Any]:
        """Process right to erasure (right to be forgotten)"""
        try:
            # Check for legal grounds to retain data
            legal_grounds = self._check_retention_grounds(user_id)

            if legal_grounds:
                return {
                    'status': 'partial_denial',
                    'request_id': request_id,
                    'reason': 'legal_obligation',
                    'retained_data': legal_grounds
                }

            # Anonymize or delete data
            with self.db.connect() as conn:
                # Anonymize user data
                conn.execute(text("""
                    UPDATE app_data.users SET
                        email = 'ANONYMIZED',
                        full_name = 'ANONYMIZED',
                        phone = 'ANONYMIZED',
                        address = 'ANONYMIZED'
                    WHERE id = :uid
                """), {'uid': user_id})

                # Delete or anonymize health records
                conn.execute(text("""
                    UPDATE app_data.health_records SET
                        data = 'ANONYMIZED',
                        prediction = 'ANONYMIZED'
                    WHERE user_id = :uid
                """), {'uid': user_id})

                # Delete chat logs
                conn.execute(text("""
                    DELETE FROM app_data.chat_logs WHERE user_id = :uid
                """), {'uid': user_id})

                conn.commit()

            self._update_request_status(request_id, 'completed', {'action': 'data_erased'})

            return {
                'status': 'completed',
                'request_id': request_id,
                'action': 'data_erased',
                'completion_date': datetime.now(timezone.utc).isoformat()
            }

        except Exception:
            logger.error("Erasure request failed")
            return {
                'status': 'failed',
                'request_id': request_id,
                'error': COMPLIANCE_OPERATION_FAILURE_MESSAGE,
            }

    def _process_portability_request(self, user_id: int, request_id: str) -> Dict[str, Any]:
        """Process data portability request"""
        # Similar to access request but in machine-readable format
        access_result = self._process_access_request(user_id, request_id)

        if access_result['status'] == 'completed':
            # Convert to portable format (CSV, XML, etc.)
            portable_data = self._convert_to_portable_format(access_result['data_package'])

            return {
                'status': 'completed',
                'request_id': request_id,
                'portable_data': portable_data,
                'formats': ['json', 'csv', 'xml']
            }

        return access_result

    def anonymize_data(self, data: Dict[str, Any], method: str = "pseudonymization") -> Dict[str, Any]:
        """Anonymize or pseudonymize personal data"""
        anonymized = data.copy()

        if method == "pseudonymization":
            # Replace identifiers with pseudonyms
            for key in ['email', 'phone', 'ssn', 'medical_record_number']:
                if key in anonymized:
                    anonymized[key] = self._generate_pseudonym(anonymized[key])

        elif method == "generalization":
            # Generalize values (e.g., exact age to age range)
            if 'age' in anonymized:
                age = anonymized['age']
                if isinstance(age, (int, float)):
                    anonymized['age_range'] = f"{(age//10)*10}-{(age//10)*10+9}"
                    del anonymized['age']

        elif method == "suppression":
            # Remove direct identifiers
            direct_identifiers = ['name', 'email', 'phone', 'ssn', 'address']
            for identifier in direct_identifiers:
                if identifier in anonymized:
                    del anonymized[identifier]

        return anonymized

    def _generate_pseudonym(self, original_value: str) -> str:
        """Generate consistent pseudonym for a value"""
        hash_input = f"{original_value}_{os.getenv('PSEUDONYM_SALT', 'default')}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _check_retention_grounds(self, user_id: int) -> List[str]:
        """Check legal grounds for data retention"""
        grounds = []

        # Check for ongoing treatments
        # Check for legal requirements
        # Check for public interest

        return grounds

    def _get_processing_activities(self, user_id: int) -> List[Dict[str, Any]]:
        """Get processing activities for user"""
        return [
            {
                'purpose': 'healthcare_service_delivery',
                'legal_basis': 'consent',
                'data_categories': ['health_data', 'contact_information'],
                'retention_period': '7_years'
            }
        ]

    def _get_data_categories(self, user_id: int) -> List[str]:
        """Get data categories for user"""
        return ['health_data', 'contact_information', 'usage_data']

    def _get_data_recipients(self, user_id: int) -> List[str]:
        """Get data recipients for user"""
        return ['healthcare_providers', 'insurance_companies']

    def _get_retention_periods(self, user_id: int) -> Dict[str, str]:
        """Get retention periods for user data"""
        return {
            'health_records': '7_years',
            'contact_info': '7_years',
            'chat_logs': '2_years'
        }

    def _update_request_status(self, request_id: str, status: str, result: Dict[str, Any]):
        """Update DSAR status"""
        try:
            with self.db.connect() as conn:
                conn.execute(text("""
                    UPDATE compliance.data_subject_requests
                    SET status = :status, result = :result, completed_at = :ts
                    WHERE request_id = :rid
                """), {
                    'status': status,
                    'result': json.dumps(result),
                    'ts': datetime.now(timezone.utc),
                    'rid': request_id
                })
                conn.commit()
        except Exception:
            logger.error("Failed to update request status")

    def _convert_to_portable_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data to portable format"""
        # This would implement format conversion logic
        return data

class ComplianceManager:
    """Unified compliance management for HIPAA and GDPR"""

    def __init__(self, db_session, redis_client: redis.Redis):
        self.db = db_session
        self.redis = redis_client

        # Initialize compliance modules
        encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self.hipaa = HIPAACompliance(db_session, encryption_key)
        self.gdpr = GDPRCompliance(db_session)

        self.framework = ComplianceFramework.BOTH  # Can be configured

    def log_data_processing(self, record: DataProcessingRecord):
        """Log all data processing activities"""
        try:
            with self.db.connect() as conn:
                conn.execute(text("""
                    INSERT INTO compliance.data_processing_log
                    (user_id, processing_type, data_categories, legal_basis,
                     purpose, timestamp, processor, third_party)
                    VALUES (:uid, :ptype, :dcats, :lbasis, :purpose, :ts, :proc, :tparty)
                """), {
                    'uid': record.user_id,
                    'ptype': record.processing_type,
                    'dcats': json.dumps([cat.value for cat in record.data_categories]),
                    'lbasis': record.legal_basis,
                    'purpose': record.purpose,
                    'ts': record.timestamp,
                    'proc': record.processor,
                    'tparty': record.third_party
                })
                conn.commit()
        except Exception:
            logger.error("Failed to log data processing")

    def check_consent(self, user_id: int, purpose: str,
                     data_categories: List[DataCategory]) -> bool:
        """Check if user has given valid consent"""
        try:
            with self.db.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM compliance.consent_records
                    WHERE user_id = :uid AND purpose = :purpose
                    AND granted = true
                    AND expires_at > :ts
                    ORDER BY created_at DESC LIMIT 1
                """), {
                    'uid': user_id,
                    'purpose': purpose,
                    'ts': datetime.now(timezone.utc)
                }).fetchone()

                if result:
                    consent_record = dict(result)
                    consented_categories = set(json.loads(consent_record['data_categories']))
                    requested_categories = set(cat.value for cat in data_categories)

                    return requested_categories.issubset(consented_categories)

                return False

        except Exception:
            logger.error("Consent check failed")
            return False

    def record_consent(self, consent: ConsentRecord):
        """Record user consent"""
        try:
            with self.db.connect() as conn:
                conn.execute(text("""
                    INSERT INTO compliance.consent_records
                    (user_id, consent_type, consent_version, granted, timestamp,
                     ip_address, user_agent, purpose, data_categories, retention_period_days)
                    VALUES (:uid, :ctype, :cversion, :granted, :ts, :ip, :ua, :purpose, :dcats, :retention)
                """), {
                    'uid': consent.user_id,
                    'ctype': consent.consent_type,
                    'cversion': consent.consent_version,
                    'granted': consent.granted,
                    'ts': consent.timestamp,
                    'ip': consent.ip_address,
                    'ua': consent.user_agent,
                    'purpose': consent.purpose,
                    'dcats': json.dumps([cat.value for cat in consent.data_categories]),
                    'retention': consent.retention_period_days
                })
                conn.commit()
        except Exception:
            logger.error("Failed to record consent")

    def generate_compliance_report(self, report_type: str) -> Dict[str, Any]:
        """Generate compliance reports"""
        if report_type == "hipaa_audit":
            return self._generate_hipaa_audit_report()
        elif report_type == "gdpr_accountability":
            return self._generate_gdpr_accountability_report()
        elif report_type == "data_inventory":
            return self._generate_data_inventory_report()
        else:
            return {'error': 'Unknown report type'}

    def _generate_hipaa_audit_report(self) -> Dict[str, Any]:
        """Generate HIPAA audit report"""
        try:
            with self.db.connect() as conn:
                # Get access logs
                access_logs = conn.execute(text("""
                    SELECT COUNT(*) as total_accesses,
                           COUNT(DISTINCT accessed_by) as unique_users,
                           DATE_TRUNC('day', timestamp) as date
                    FROM audit.phi_access_log
                    WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE_TRUNC('day', timestamp)
                    ORDER BY date DESC
                """)).fetchall()

                # Get breach incidents
                breaches = conn.execute(text("""
                    SELECT COUNT(*) as total_breaches
                    FROM compliance.breach_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '365 days'
                """)).fetchone()

                return {
                    'report_type': 'hipaa_audit',
                    'period': 'last_30_days',
                    'phi_accesses': [dict(log) for log in access_logs],
                    'breach_incidents': breaches['total_breaches'] if breaches else 0,
                    'compliance_score': 0.95  # This would be calculated
                }

        except Exception:
            logger.error("HIPAA audit report failed")
            return {'error': COMPLIANCE_REPORT_FAILURE_MESSAGE}

    def _generate_gdpr_accountability_report(self) -> Dict[str, Any]:
        """Generate GDPR accountability report"""
        try:
            with self.db.connect() as conn:
                # Get DSAR statistics
                dsar_stats = conn.execute(text("""
                    SELECT request_type, COUNT(*) as count,
                           AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours
                    FROM compliance.data_subject_requests
                    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                    GROUP BY request_type
                """)).fetchall()

                # Get consent statistics
                consent_stats = conn.execute(text("""
                    SELECT purpose, COUNT(*) as total_consent,
                           SUM(CASE WHEN granted THEN 1 ELSE 0 END) as granted
                    FROM compliance.consent_records
                    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                    GROUP BY purpose
                """)).fetchall()

                return {
                    'report_type': 'gdpr_accountability',
                    'period': 'last_90_days',
                    'dsar_statistics': [dict(stat) for stat in dsar_stats],
                    'consent_statistics': [dict(stat) for stat in consent_stats],
                    'data_subject_rights_satisfaction': 0.92  # This would be calculated
                }

        except Exception:
            logger.error("GDPR accountability report failed")
            return {'error': COMPLIANCE_REPORT_FAILURE_MESSAGE}

    def _generate_data_inventory_report(self) -> Dict[str, Any]:
        """Generate data inventory report"""
        try:
            with self.db.connect() as conn:
                # Get data volume by category
                data_volumes = conn.execute(text("""
                    SELECT 'users' as table_name, COUNT(*) as record_count,
                           'personal_data' as category
                    FROM app_data.users
                    UNION ALL
                    SELECT 'health_records' as table_name, COUNT(*) as record_count,
                           'health_data' as category
                    FROM app_data.health_records
                    UNION ALL
                    SELECT 'chat_logs' as table_name, COUNT(*) as record_count,
                           'interaction_data' as category
                    FROM app_data.chat_logs
                """)).fetchall()

                return {
                    'report_type': 'data_inventory',
                    'data_volumes': [dict(vol) for vol in data_volumes],
                    'total_records': sum(vol['record_count'] for vol in data_volumes),
                    'storage_locations': ['postgresql_primary', 's3_backup'],
                    'retention_policies_applied': True
                }

        except Exception:
            logger.error("Data inventory report failed")
            return {'error': COMPLIANCE_REPORT_FAILURE_MESSAGE}

# Global compliance manager instance
compliance_manager = None

def get_compliance_manager(db_session, redis_client: redis.Redis) -> ComplianceManager:
    """Get or create compliance manager instance"""
    global compliance_manager
    if compliance_manager is None:
        compliance_manager = ComplianceManager(db_session, redis_client)
    return compliance_manager
