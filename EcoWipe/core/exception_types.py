"""
Enterprise Data Sanitization Platform
Custom Exception Types
"""

class EcoWipeError(Exception):
    """Base exception for all EcoWipe errors."""
    pass

class SecurityViolationError(EcoWipeError):
    """Raised when a critical security boundary is breached."""
    pass

class DeviceValidationError(EcoWipeError):
    """Raised when a device fails strict validation checks."""
    pass

class SystemDriveError(DeviceValidationError):
    """Raised when an operation is attempted on a system or boot drive."""
    pass

class InvalidInputError(EcoWipeError):
    """Raised when user input fails validation."""
    pass

class WipeEngineError(EcoWipeError):
    """Raised when the wipe engine encounters a critical failure."""
    pass

class StateMachineError(EcoWipeError):
    """Raised when an invalid state transition is attempted."""
    pass

class CertificateError(EcoWipeError):
    """Raised when certificate generation or signing fails."""
    pass
