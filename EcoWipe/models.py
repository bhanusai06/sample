import sqlite3
import uuid
import hashlib
import json
import os
import base64
from datetime import datetime
import qrcode
from qrcode.image.pure import PyPNGImage

LOG_DB_FILE = "ecowipe_logs.db"

def init_db():
    """Initialize the SQLite logging database."""
    conn = sqlite3.connect(LOG_DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wipes (
            id TEXT PRIMARY KEY,
            device TEXT,
            operator TEXT,
            method TEXT,
            status TEXT,
            hash TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_wipe(cert_id, device, operator, method, status, cert_hash, timestamp):
    """Log a wipe operation to the SQLite database."""
    try:
        conn = sqlite3.connect(LOG_DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wipes (id, device, operator, method, status, hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cert_id, device, operator, method, status, cert_hash, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging to DB: {e}")

def generate_certificate(device_path, device_model, device_serial, device_size, wipe_method, operator_id, start_time, end_time, verification_status):
    """Generate the certificate JSON in the new EcoWIPE-v2 format."""
    import time
    
    # Extract size in GB from device_size string (e.g., "476.94 GB" -> "476.94G")
    size_str = device_size.replace(" GB", "G").replace(" B", "") if "GB" in device_size else device_size
    
    # Map wipe methods to passes
    wipe_passes = 1
    nist_standard = "Clear"
    if "3-Pass" in wipe_method or "DoD" in wipe_method:
        wipe_passes = 3
        nist_standard = "DoD 5220.22-M"
    elif "Random" in wipe_method:
        wipe_passes = 1
        nist_standard = "Clear"
    else:
        wipe_passes = 1
        nist_standard = "Clear"
    
    # Convert timestamp to Unix time
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        unix_timestamp = int(start_dt.timestamp())
    except:
        unix_timestamp = int(time.time())
    
    # Parse datetime
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        datetime_str = start_dt.isoformat() + ".355606"
    except:
        datetime_str = datetime.now().isoformat() + ".355606"
    
    # Build certificate data in EcoWIPE-v2 format
    cert_data_for_hash = {
        "schema": "EcoWIPE-v2",
        "timestamp": unix_timestamp,
        "datetime": datetime_str,
        "machine_id": "ecowipe-session",
        "drive_path": device_path,
        "drive_model": device_model,
        "drive_serial": device_serial if device_serial else "UNKNOWN",
        "drive_size": size_str,
        "wipe_method": wipe_method,
        "wipe_passes": wipe_passes,
        "nist_standard": nist_standard,
        "verification": verification_status,
        "status": "SUCCESS" if verification_status == "SUCCESS" else "FAILED"
    }
    # Generate SHA-256 hash of the data (excluding record_hash)
    cert_string = json.dumps(cert_data_for_hash, sort_keys=True)
    record_hash = hashlib.sha256(cert_string.encode('utf-8')).hexdigest()
    
    # Add the record hash to the final certificate
    cert_data_for_hash["record_hash"] = record_hash
    
    # Save certificate JSON
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    cert_filename = f"ecowipe_certificate_{timestamp_str}.json"
    with open(cert_filename, "w") as f:
        json.dump(cert_data_for_hash, f, indent=2)
    
    print(f"[DEBUG] Certificate saved: {cert_filename}")
    print(f"[DEBUG] Record Hash: {record_hash}")
        
    # Generate QR Code - Using Base64 encoded JSON for website compatibility
    import urllib.parse
    import base64
    
    # Create compact certificate data for QR code
    # Use only essential fields to reduce QR code size
    qr_cert_data = {
        "schema": "EcoWIPE-v2",
        "timestamp": unix_timestamp,
        "datetime": datetime_str,
        "drive_path": device_path,
        "drive_model": device_model,
        "drive_serial": device_serial if device_serial else "UNKNOWN",
        "drive_size": size_str,
        "wipe_method": wipe_method,
        "wipe_passes": wipe_passes,
        "nist_standard": nist_standard,
        "verification": verification_status,
        "status": "SUCCESS" if verification_status == "SUCCESS" else "FAILED",
        "record_hash": record_hash,
        "operator": operator_id
    }
    
    # Encode as Base64 for URL safety
    cert_json_compact = json.dumps(qr_cert_data, separators=(',', ':'), sort_keys=True)
    encoded_cert = base64.b64encode(cert_json_compact.encode('utf-8')).decode('utf-8')
    
    # Create scannable URL with Base64 data
    qr_url = f"https://charan242726.github.io/e-waste?cert={encoded_cert}"
    
    print(f"[DEBUG] QR URL: {qr_url}")
    print(f"[DEBUG] QR URL Length: {len(qr_url)}")
    print(f"[DEBUG] Cert JSON (compact): {cert_json_compact}")
    
    # Create QR code with URL
    qr = qrcode.QRCode(
        version=None,  # Auto-detect version
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    qr_filename = f"ecowipe_qr_{timestamp_str}.png"
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_filename)
    
    print(f"[DEBUG] QR Code saved: {qr_filename}")
        
    # Log to DB
    log_wipe("ecowipe-cert", device_path, operator_id, wipe_method, verification_status, record_hash, datetime_str)
    
    return cert_filename, qr_filename, record_hash, "ecowipe-cert"
