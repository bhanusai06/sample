#!/usr/bin/env python3
"""
Test script to diagnose device detection issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import get_available_drives

print("[TEST] Starting device detection test...")
print("[TEST] Current working directory:", os.getcwd())
print("[TEST] Python version:", sys.version)

drives = get_available_drives()

print(f"\n[TEST] Device detection returned {len(drives)} drive(s)")

if drives:
    for i, drive in enumerate(drives):
        print(f"\n[TEST] Drive {i+1}:")
        for key, value in drive.items():
            print(f"  {key}: {value}")
else:
    print("[TEST] ERROR: No devices detected!")
    print("[TEST] Make sure you are running this with Administrator privileges!")
    print("[TEST] Try right-clicking on PowerShell and selecting 'Run as Administrator'")

print("\n[TEST] Test completed.")
