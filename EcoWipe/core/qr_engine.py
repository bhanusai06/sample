"""
Enterprise Data Sanitization Platform
High-Reliability QR Code Engine
"""
import qrcode
import cv2
import numpy as np
from typing import Optional
import os

import sys
# Ensure core and utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exception_types import CertificateError
from core.logging_engine import certificate_logger, log_error_event
from utils.constants import QR_BOX_SIZE, QR_BORDER

class QREngine:
    """
    Generates high-reliability QR codes with strict parameters.
    Includes auto-decode verification to guarantee readability.
    """
    
    @staticmethod
    def generate_and_verify(data: str, output_path: str) -> str:
        """
        Generate a QR code and immediately verify it can be decoded.
        
        Args:
            data: The string data to encode.
            output_path: The file path to save the image.
            
        Returns:
            The path to the saved QR code.
            
        Raises:
            CertificateError: If generation or verification fails.
        """
        if not data:
            raise CertificateError("Cannot generate QR code with empty data.")
            
        try:
            # 1. Generate QR Code with strict parameters
            qr = qrcode.QRCode(
                version=None, # Auto-detect
                error_correction=qrcode.constants.ERROR_CORRECT_H, # High (30%)
                box_size=QR_BOX_SIZE, # Must be >= 12
                border=QR_BORDER,
            )
            qr.add_data(data.encode('utf-8'))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            
            # 2. Auto-decode verification using OpenCV
            if not QREngine._verify_qr(output_path, data):
                # If verification fails, delete the bad file and raise
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise CertificateError("QR Code generated but failed auto-decode verification.")
                
            certificate_logger.info(f"QR code generated and verified successfully: {output_path}")
            return output_path
            
        except Exception as e:
            log_error_event("qr_engine", "generate_and_verify", f"QR generation failed: {e}")
            raise CertificateError(f"Failed to generate QR code: {e}")

    @staticmethod
    def _verify_qr(image_path: str, expected_data: str) -> bool:
        """
        Attempt to decode the saved QR code image to verify readability.
        """
        try:
            # Read image using OpenCV
            img = cv2.imread(image_path)
            if img is None:
                return False
                
            # Initialize OpenCV QR Code detector
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            
            if bbox is not None and data == expected_data:
                return True
                
            certificate_logger.warning(f"QR verification mismatch. Expected: {expected_data[:20]}..., Got: {data[:20]}...")
            return False
            
        except Exception as e:
            log_error_event("qr_engine", "_verify_qr", f"QR verification error: {e}")
            return False
