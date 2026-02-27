"""
Enterprise Data Sanitization Platform
Cryptographic Security Engine
"""
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

import sys
# Ensure core and utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exception_types import SecurityViolationError
from core.logging_engine import security_logger, log_error_event
from utils.constants import RSA_KEY_SIZE

class SecurityEngine:
    """
    Handles RSA-4096 key generation, signing, and verification.
    Ensures forensic integrity of generated certificates.
    """
    def __init__(self, key_dir: str = "keys"):
        self.key_dir = key_dir
        self.private_key_path = os.path.join(key_dir, "ecowipe_private.pem")
        self.public_key_path = os.path.join(key_dir, "ecowipe_public.pem")
        self._private_key = None
        self._public_key = None
        
        self._initialize_keys()

    def _initialize_keys(self) -> None:
        """Load existing keys or generate new RSA-4096 keys if they don't exist."""
        os.makedirs(self.key_dir, exist_ok=True)
        
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            self._load_keys()
        else:
            self._generate_keys()

    def _generate_keys(self) -> None:
        """Generate a new RSA-4096 key pair."""
        security_logger.info(f"Generating new RSA-{RSA_KEY_SIZE} key pair...")
        
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE,
        )
        self._public_key = self._private_key.public_key()
        
        # Save Private Key
        with open(self.private_key_path, "wb") as f:
            f.write(self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption() # In production, this should be encrypted
            ))
            
        # Save Public Key
        with open(self.public_key_path, "wb") as f:
            f.write(self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
            
        security_logger.info("RSA key pair generated and saved successfully.")

    def _load_keys(self) -> None:
        """Load existing RSA keys from disk."""
        try:
            with open(self.private_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
            with open(self.public_key_path, "rb") as f:
                self._public_key = serialization.load_pem_public_key(
                    f.read()
                )
        except Exception as e:
            log_error_event("security_engine", "_load_keys", f"Failed to load RSA keys: {e}")
            raise SecurityViolationError("Cryptographic keys are corrupted or inaccessible.")

    def sign_data(self, data: bytes) -> str:
        """
        Sign data using the RSA-4096 private key.
        
        Args:
            data: The raw bytes to sign.
            
        Returns:
            Base64 encoded signature string.
        """
        if not self._private_key:
            raise SecurityViolationError("Private key not loaded.")
            
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, data: bytes, signature_b64: str) -> bool:
        """
        Verify a signature using the public key.
        
        Args:
            data: The original raw bytes.
            signature_b64: The Base64 encoded signature.
            
        Returns:
            True if valid, False otherwise.
        """
        if not self._public_key:
            raise SecurityViolationError("Public key not loaded.")
            
        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            security_logger.warning("Signature verification failed: Invalid signature.")
            return False
        except Exception as e:
            log_error_event("security_engine", "verify_signature", f"Verification error: {e}")
            return False
