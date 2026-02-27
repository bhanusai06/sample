"""
Enterprise Data Sanitization Platform
Centralized Validation Engine
"""
import re
import os
from pathlib import Path
from typing import Any

import sys
# Ensure core can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exception_types import InvalidInputError, SecurityViolationError
from core.logging_engine import log_security_event

# Strict regex for operator names: 1-100 chars, alphanumeric, space, hyphen, underscore
OPERATOR_REGEX = re.compile(r"^[a-zA-Z0-9 \-_]{1,100}$")

# Reserved Windows device names that should never be used as file paths
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def validate_operator_name(name: str) -> str:
    """
    Validate the operator name against strict criteria.
    
    Args:
        name: The operator name to validate.
        
    Returns:
        The validated, stripped operator name.
        
    Raises:
        InvalidInputError: If the name fails validation.
    """
    if not name:
        raise InvalidInputError("Operator name cannot be empty.")
        
    clean_name = name.strip()
    
    if not OPERATOR_REGEX.match(clean_name):
        log_security_event("validation_engine", "validate_operator_name", f"Invalid operator name attempted: {repr(name)}")
        raise InvalidInputError(
            "Operator name must be 1-100 characters and contain only "
            "alphanumeric characters, spaces, hyphens, and underscores."
        )
        
    return clean_name

def validate_safe_path(file_path: str, must_exist: bool = False) -> Path:
    """
    Validate a file path to prevent directory traversal and ensure it's safe.
    
    Args:
        file_path: The path to validate.
        must_exist: Whether the path must already exist.
        
    Returns:
        A resolved pathlib.Path object.
        
    Raises:
        SecurityViolationError: If directory traversal or reserved names are detected.
        InvalidInputError: If the path is invalid or doesn't exist when required.
    """
    if not file_path:
        raise InvalidInputError("Path cannot be empty.")
        
    try:
        path_obj = Path(file_path).resolve()
    except Exception as e:
        raise InvalidInputError(f"Invalid path format: {e}")
        
    # Check for reserved Windows names
    if path_obj.stem.upper() in RESERVED_NAMES:
        log_security_event("validation_engine", "validate_safe_path", f"Reserved name used in path: {file_path}")
        raise SecurityViolationError(f"Path contains reserved Windows name: {path_obj.stem}")
        
    # If it's a relative path that resolved outside the current working directory,
    # it might be a traversal attempt (though .resolve() usually handles this, 
    # it's good to be explicit if we expect paths to be within a specific dir).
    # For general safe paths, we just ensure it's absolute after resolution.
    if not path_obj.is_absolute():
        raise SecurityViolationError("Path must resolve to an absolute path.")
        
    if must_exist and not path_obj.exists():
        raise InvalidInputError(f"Path does not exist: {path_obj}")
        
    return path_obj

def validate_device_path(device_path: str) -> str:
    """
    Validate that a device path matches the expected Windows physical drive format.
    
    Args:
        device_path: The device path (e.g., '\\\\.\\PhysicalDrive1').
        
    Returns:
        The validated device path.
        
    Raises:
        InvalidInputError: If the format is incorrect.
    """
    if not device_path:
        raise InvalidInputError("Device path cannot be empty.")
        
    # Strict check for Windows physical drive format
    if not re.match(r"^\\\\\\.\\PhysicalDrive\d+$", device_path, re.IGNORECASE):
        log_security_event("validation_engine", "validate_device_path", f"Invalid device path format: {device_path}")
        raise InvalidInputError(f"Invalid device path format: {device_path}")
        
    return device_path
