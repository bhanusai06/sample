"""
Enterprise Data Sanitization Platform
Wipe Strategies and Data Generation
"""
import os
from typing import Iterator, Tuple

import sys
# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constants import WIPE_BLOCK_SIZE_BYTES

class WipeStrategy:
    """Base class for wipe strategies."""
    name: str = "Unknown"
    passes: int = 0
    nist_standard: str = "Unknown"

    def get_block(self, pass_index: int, block_size: int = WIPE_BLOCK_SIZE_BYTES) -> bytes:
        """Generate a block of data for the given pass."""
        raise NotImplementedError("Must be implemented by subclass")

class ZeroPassStrategy(WipeStrategy):
    """NIST 800-88 Clear: Single pass of zeros."""
    name = "1-Pass Zero"
    passes = 1
    nist_standard = "Clear"

    def get_block(self, pass_index: int, block_size: int = WIPE_BLOCK_SIZE_BYTES) -> bytes:
        return b'\x00' * block_size

class RandomPassStrategy(WipeStrategy):
    """NIST 800-88 Clear: Single pass of random data."""
    name = "1-Pass Random"
    passes = 1
    nist_standard = "Clear"

    def get_block(self, pass_index: int, block_size: int = WIPE_BLOCK_SIZE_BYTES) -> bytes:
        return os.urandom(block_size)

class DoD522022MStrategy(WipeStrategy):
    """DoD 5220.22-M: 3 passes (Zeros, Ones, Random)."""
    name = "DoD 5220.22-M (3-Pass)"
    passes = 3
    nist_standard = "DoD 5220.22-M"

    def get_block(self, pass_index: int, block_size: int = WIPE_BLOCK_SIZE_BYTES) -> bytes:
        if pass_index == 0:
            return b'\x00' * block_size
        elif pass_index == 1:
            return b'\xFF' * block_size
        else:
            return os.urandom(block_size)

def get_strategy(method_name: str) -> WipeStrategy:
    """Factory function to get a strategy by name."""
    if "DoD" in method_name or "3-Pass" in method_name:
        return DoD522022MStrategy()
    elif "Random" in method_name:
        return RandomPassStrategy()
    else:
        return ZeroPassStrategy()
