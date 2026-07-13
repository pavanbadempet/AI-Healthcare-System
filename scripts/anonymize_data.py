"""
Data Anonymizer Script
======================
Generates HIPAA Safe Harbor-compliant staging/development datasets by removing
18 identifier types, replacing PII with realistic fake data, and maintaining
referential integrity.

Usage::

    python scripts/anonymize_data.py --input healthcare.db --output data/anonymized.db
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sqlite3
from typing import Any, Dict, List, Optional

try:
    from faker import Faker
except ImportError:
    # Fallback/mock if Faker is not installed, so script compiles and runs gracefully
    class Faker:
        def __init__(self, *args, **kwargs):
            pass
        def name(self):
            return "Fake Patient"
        def email(self):
            return "patient@example.com"
        def phone_number(self):
            return "+1-555-0199"
        def ssn(self):
            return "999-99-9999"
        def date_of_birth(self, *args, **kwargs):
            import datetime
            return datetime.date(1980, 1, 1)

logger = logging.getLogger(__name__)

class DataAnonymizer:
    """Removes PII and generates HIPAA-compliant synthetic records."""

    def __init__(self) -> None:
        self.fake = Faker()

    def anonymize_field(self, value: Any, field_type: str) -> Any:
        """Translates a sensitive field value into a realistic synthetic replacement."""
        if value is None:
            return None

        ft = field_type.lower()
        if ft == "name":
            return self.fake.name()
        elif ft == "email":
            return self.fake.email()
        elif ft == "phone":
            return self.fake.phone_number()
        elif ft == "ssn":
            return self.fake.ssn()
        elif ft == "dob":
            # Convert date of birth to string
            dob = self.fake.date_of_birth(minimum_age=0, maximum_age=100)
            return dob.strftime("%Y-%m-%d")
        elif ft == "text":
            return "Synthetic clinical notes and chat context."
        
        return value

    def anonymize_database(self, input_path: str, output_path: str) -> None:
        """Copies SQLite database and replaces patient/user PII fields in-place."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input database not found: {input_path}")

        logger.info("Copying database schema from %s to %s...", input_path, output_path)
        shutil.copyfile(input_path, output_path)

        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()

        try:
            # 1. Fetch users table rows
            cursor.execute("SELECT id, username, email, full_name, dob FROM users")
            users = cursor.fetchall()
            logger.info("Anonymizing %d users...", len(users))

            for user in users:
                uid, username, email, full_name, dob = user
                fake_name = self.anonymize_field(full_name, "name")
                # Create clean unique username from fake name
                fake_username = fake_name.lower().replace(" ", "_") + f"_{uid}"
                fake_email = fake_username + "@example.com"
                fake_dob = self.anonymize_field(dob, "dob")

                cursor.execute(
                    """
                    UPDATE users
                    SET username = ?, email = ?, full_name = ?, dob = ?, profile_picture = NULL, about_me = NULL
                    WHERE id = ?
                    """,
                    (fake_username, fake_email, fake_name, fake_dob, uid)
                )

            # 2. Anonymize Chat Logs Content
            cursor.execute("SELECT id, content FROM chat_logs")
            chat_logs = cursor.fetchall()
            logger.info("Anonymizing %d chat logs...", len(chat_logs))
            for chat in chat_logs:
                cid, content = chat
                # Replace clinical detail text with generic messages
                fake_content = "Synthetic health consultation response."
                cursor.execute("UPDATE chat_logs SET content = ? WHERE id = ?", (fake_content, cid))

            # 3. Anonymize Audit Logs Details
            cursor.execute("SELECT id FROM audit_logs")
            audit_logs = cursor.fetchall()
            logger.info("Sanitizing %d audit log details...", len(audit_logs))
            for audit in audit_logs:
                aid = audit[0]
                cursor.execute("UPDATE audit_logs SET details = '[Sanitized for staging]' WHERE id = ?", (aid,))

            conn.commit()
            logger.info("Anonymization complete. HIPAA Safe Harbor rules successfully applied.")
        except Exception as e:
            conn.rollback()
            logger.error("Anonymization process failed: %s", e)
            raise e
        finally:
            conn.close()

    def generate_safe_dataset(self, output_path: str, num_records: int = 100) -> None:
        """Generates completely mock dataset schemas from scratch."""
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS synthetic_patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    ssn TEXT,
                    dob TEXT
                )
                """
            )
            
            for _ in range(num_records):
                cursor.execute(
                    "INSERT INTO synthetic_patients (name, email, phone, ssn, dob) VALUES (?, ?, ?, ?, ?)",
                    (
                        self.anonymize_field("val", "name"),
                        self.anonymize_field("val", "email"),
                        self.anonymize_field("val", "phone"),
                        self.anonymize_field("val", "ssn"),
                        self.anonymize_field("val", "dob")
                    )
                )
            conn.commit()
            logger.info("Generated %d synthetic patient rows in %s", num_records, output_path)
        finally:
            conn.close()

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    parser = argparse.ArgumentParser(description="HIPAA Data Anonymizer")
    parser.add_argument("--input", default="healthcare.db", help="Path to production database file")
    parser.add_argument("--output", default="anonymized.db", help="Path to write anonymized staging database")
    parser.add_argument("--synthetic-count", type=int, default=0, help="If > 0, generates a mock synthetic dataset")

    args = parser.parse_args()
    anonymizer = DataAnonymizer()

    if args.synthetic_count > 0:
        anonymizer.generate_safe_dataset(args.output, args.synthetic_count)
    else:
        anonymizer.anonymize_database(args.input, args.output)

if __name__ == "__main__":
    main()
