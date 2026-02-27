"""
Enterprise Data Sanitization Platform
Forensic Certificate Engine
"""
import json
import uuid
import hashlib
import base64
from datetime import datetime, timezone
from typing import Dict, Any
import os

import sys
# Ensure core can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.security_engine import SecurityEngine
from core.qr_engine import QREngine
from core.exception_types import CertificateError
from core.logging_engine import certificate_logger, log_error_event

class CertificateEngine:
    """
    Generates cryptographically signed, forensic-grade JSON certificates.
    """
    def __init__(self):
        self.security_engine = SecurityEngine()
        self.qr_engine = QREngine()
        self.app_version = "2.0.0-Enterprise"

    def generate_certificate(self, wipe_result: Dict[str, Any], output_dir: str = "certificates") -> Dict[str, str]:
        """
        Generate a signed JSON certificate and corresponding QR code.
        
        Args:
            wipe_result: The dictionary emitted by the WipeEngine upon completion.
            output_dir: Directory to save the certificate files.
            
        Returns:
            Dict containing paths to the generated files.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 1. Generate UUIDv4 and strict UTC timestamp
            cert_id = str(uuid.uuid4())
            timestamp_iso = datetime.now(timezone.utc).isoformat()
            
            # 2. Construct the strict JSON schema
            cert_data = {
                "schema_version": "EcoWIPE-Enterprise-v2",
                "certificate_id": cert_id,
                "timestamp_utc": timestamp_iso,
                "app_version": self.app_version,
                "operator": wipe_result["operator"],
                "device": {
                    "id": wipe_result["device_id"],
                    "model": wipe_result["model"],
                    "serial_number": wipe_result["serial"],
                    "size_bytes": wipe_result["size_bytes"]
                },
                "wipe_details": {
                    "method": wipe_result["method"],
                    "passes": wipe_result["passes"],
                    "nist_standard": wipe_result["nist_standard"],
                    "pre_hash_sha256": wipe_result["pre_hash"],
                    "post_hash_sha256": wipe_result["post_hash"],
                    "start_time_unix": wipe_result["start_time"],
                    "end_time_unix": wipe_result["end_time"],
                    "status": wipe_result["status"]
                }
            }
            
            # 3. Serialize deterministically for hashing
            cert_json_str = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
            cert_bytes = cert_json_str.encode('utf-8')
            
            # 4. Compute SHA-256 of the payload
            payload_hash = hashlib.sha256(cert_bytes).hexdigest()
            cert_data["payload_hash"] = payload_hash
            
            # 5. Sign the hash using RSA-4096
            signature = self.security_engine.sign_data(payload_hash.encode('utf-8'))
            cert_data["rsa_signature"] = signature
            
            # 6. Save JSON to disk
            safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"cert_{safe_timestamp}_{cert_id[:8]}.json"
            json_path = os.path.join(output_dir, json_filename)
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(cert_data, f, indent=4)
                
            # 7. Generate QR Code (using a compact base64 version of the signed data)
            # We encode the JSON to base64 to make it URL safe if needed later
            compact_json = json.dumps(cert_data, separators=(',', ':'))
            b64_cert = base64.b64encode(compact_json.encode('utf-8')).decode('utf-8')
            
            qr_filename = f"qr_{safe_timestamp}_{cert_id[:8]}.png"
            qr_path = os.path.join(output_dir, qr_filename)
            
            # This will raise CertificateError if verification fails
            self.qr_engine.generate_and_verify(b64_cert, qr_path)
            
            certificate_logger.info(f"Successfully generated signed certificate {cert_id}")
            
            return {
                "certificate_id": cert_id,
                "json_path": json_path,
                "qr_path": qr_path
            }
            
        except Exception as e:
            log_error_event("certificate_engine", "generate_certificate", f"Certificate generation failed: {e}", exc_info=True)
            raise CertificateError(f"Failed to generate secure certificate: {e}")
