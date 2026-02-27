#!/usr/bin/env python3
"""
EcoWipe Pre-Launch Validation Script
Diagnoses issues before running the main application
"""

import sys
import os
import ctypes
import subprocess

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_check(status, message):
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {message}")

def main():
    print_header("EcoWipe Pre-Launch Validation")
    
    # 1. Check Python version
    print("\n[1] Python Environment")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_check(True, f"Python {python_version}")
    
    # 2. Check if running as admin
    print("\n[2] Administrator Privileges")
    is_admin = False
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception as e:
        print(f"  Error checking admin: {e}")
    
    print_check(is_admin, "Running as Administrator" if is_admin else "NOT running as Administrator")
    
    if not is_admin:
        print("\n  ⚠️  WARNING: Device detection will not work without admin privileges!")
        print("  To run with admin privileges:")
        print("    1. Right-click EcoWipe.exe → 'Run as administrator'")
        print("    2. Or use RUN_AS_ADMIN.bat")
        print("    3. Or run: python main.py (from admin PowerShell)")
    
    # 3. Check required packages
    print("\n[3] Required Python Packages")
    required_packages = {
        'PyQt6': 'PyQt6',
        'PyQt6.QtCore': 'PyQt6',
        'PyQt6.QtGui': 'PyQt6',
        'PyQt6.QtWidgets': 'PyQt6',
    }
    
    all_imports_ok = True
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print_check(True, f"{package_name}")
        except ImportError:
            print_check(False, f"{package_name} (NOT FOUND)")
            all_imports_ok = False
    
    # 4. Check PowerShell availability
    print("\n[4] PowerShell for Device Detection")
    powershell_available = False
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Write-Host 'ok'"],
            capture_output=True,
            text=True,
            timeout=5
        )
        powershell_available = result.returncode == 0
    except Exception as e:
        pass
    
    print_check(powershell_available, "PowerShell is available")
    
    if powershell_available and is_admin:
        # 5. Test device detection
        print("\n[5] Device Detection Test")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", 
                 "Get-Disk | Select-Object Number, FriendlyName, Size | ConvertTo-Json -Compress"],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout:
                import json
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        data = [data]
                    device_count = len(data)
                    print_check(True, f"Device detection working ({device_count} device(s) found)")
                except json.JSONDecodeError:
                    print_check(False, "Device detection returned invalid JSON")
            else:
                print_check(False, "Device detection returned no data")
        except subprocess.TimeoutExpired:
            print_check(False, "Device detection timed out")
        except Exception as e:
            print_check(False, f"Device detection error: {e}")
    
    # 6. Check application files
    print("\n[6] Application Files")
    required_files = [
        "main.py",
        "engine.py",
        "ui.py",
        "utils.py",
        "models.py",
        "styles.py",
        "requirements.txt",
        "EcoWipe.spec"
    ]
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    all_files_ok = True
    for filename in required_files:
        filepath = os.path.join(app_dir, filename)
        exists = os.path.isfile(filepath)
        print_check(exists, filename)
        if not exists:
            all_files_ok = False
    
    # Final summary
    print_header("Validation Summary")
    
    if is_admin and powershell_available and all_imports_ok and all_files_ok:
        print("\n✓ All checks passed! Application is ready to run.")
        print("\nYou can now:")
        print("  1. Start the application: python main.py")
        print("  2. Or use: RUN_AS_ADMIN.bat")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the following issues:")
        if not is_admin:
            print("  - Run as Administrator")
        if not powershell_available:
            print("  - Install/enable PowerShell")
        if not all_imports_ok:
            print("  - Install missing Python packages: pip install -r requirements.txt")
        if not all_files_ok:
            print("  - Verify all application files are present")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
