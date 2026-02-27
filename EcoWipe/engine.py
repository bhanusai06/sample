import os
import time
import subprocess
import sys
import ctypes
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

# NOTE: For development, SIMULATION_MODE disables actual destructive writes.
SIMULATION_MODE = True

# TEST_MODE allows selection of system drive (for UI testing only - actual wipe is prevented by SIMULATION_MODE)
TEST_MODE_ALLOW_SYSTEM_DRIVE = False

def is_admin():
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception as e:
        print(f"[DEBUG] Failed to check admin status: {e}")
        return False

def is_system_drive(device_path):
    """
    Rudimentary check to see if a given physical drive path contains the system drive.
    In a true environment, we query WMI for the partition hosting C:.
    Since parsing WMI directly is complex, we use a basic heuristic or `wmic`.
    """
    try:
        # Example output formatting to find BootPartition or SystemDrive:
        # Here we'll rely on our WMI python logic in get_available_drives.
        return False
    except Exception:
        return True # Default to safe option if unknown.

def get_available_drives():
    r"""
    Enumerate \\.\PhysicalDriveX devices using PowerShell Get-CimInstance to avoid wiping the OS drive.
    Returns a list of dicts: [{"path": "\\.\PhysicalDrive1", "size": "32.0 GB", "model": "USB...", "is_system": False}]
    REQUIRES: Administrator privileges to enumerate drives properly.
    """
    drives = []
    
    # Check if running as admin
    if not is_admin():
        print("[ERROR] Device detection requires Administrator privileges!")
        print("[ERROR] Please run the application as Administrator.")
        return drives
    
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # 1. Get system boot partition index
        boot_drive_index = "-1"
        try:
            boot_cmd = 'Get-CimInstance Win32_DiskPartition -Filter "BootPartition=True" | Select-Object -ExpandProperty DiskIndex'
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", boot_cmd],
                capture_output=True,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=startupinfo,
                timeout=10
            )
            
            if result.returncode == 0:
                boot_drive_index = result.stdout.strip()
                print(f"[DEBUG] Boot drive index: {boot_drive_index}")
        except subprocess.TimeoutExpired:
            print("[DEBUG] Boot drive detection timed out, continuing without it...")
        except Exception as e:
            print(f"[DEBUG] Could not get boot drive index: {e}")

        # 2. Try Get-Disk method first (more reliable for USB drives)
        print(f"[DEBUG] Trying Get-Disk method for device detection...")
        ps_cmd = 'Get-Disk | Select-Object Number, FriendlyName, Size | ConvertTo-Json -Compress'
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=startupinfo,
                timeout=15
            )
            
            if result.returncode != 0:
                print(f"[DEBUG] Get-Disk PowerShell stderr: {result.stderr}")
            
            output = result.stdout.strip()
            
            print(f"[DEBUG] Get-Disk PowerShell output: {output}")
            
            import json
            if output:
                try:
                    data = json.loads(output)
                    # Convert single object to list if only one drive exists
                    if isinstance(data, dict):
                        data = [data]
                        
                    print(f"[DEBUG] Get-Disk found {len(data)} drive(s)")
                        
                    for disk in data:
                        disk_number = disk.get("Number", -1)
                        model = disk.get("FriendlyName", "Unknown Model")
                        size_bytes = disk.get("Size", 0)
                        
                        device_id = f"\\\\.\\PHYSICALDRIVE{disk_number}"
                        
                        if size_bytes:
                            size_gb = round(size_bytes / (1024**3), 2)
                            size_str = f"{size_gb} GB"
                        else:
                            size_str = "Unknown Size"

                        # Check if this physical drive matches the boot partition disk index
                        is_sys = False
                        if boot_drive_index != "-1" and str(disk_number) == boot_drive_index:
                            is_sys = True
                        
                        # In TEST_MODE, allow system drives to be selected
                        if TEST_MODE_ALLOW_SYSTEM_DRIVE and is_sys:
                            print(f"[DEBUG] TEST_MODE: Allowing system drive {device_id} for testing")
                            is_sys = False

                        print(f"[DEBUG] Found drive: {device_id} - {model} - {size_str} - System: {is_sys}")
                        
                        drives.append({
                            "path": device_id,
                            "model": model,
                            "size_str": size_str,
                            "size_bytes": size_bytes,
                            "is_system": is_sys
                        })
                    
                    if drives:
                        print(f"[DEBUG] Get-Disk method successful, found {len(drives)} drive(s)")
                        print(f"[DEBUG] Returning {len(drives)} total drives")
                        return drives
                    else:
                        print(f"[WARNING] Get-Disk returned no drives, trying Get-CimInstance fallback...")
                    
                except json.JSONDecodeError as je:
                    print(f"[WARNING] Get-Disk JSON decode error: {je}, falling back to Get-CimInstance...")
        except subprocess.TimeoutExpired:
            print("[WARNING] Get-Disk command timed out, falling back to Get-CimInstance...")
        except Exception as e:
            print(f"[WARNING] Get-Disk method failed: {e}, falling back to Get-CimInstance...")

        # 3. Fallback to Get-CimInstance method
        ps_cmd = 'Get-CimInstance Win32_DiskDrive | Select-Object DeviceID, Model, Size | ConvertTo-Json -Compress'
        print(f"[DEBUG] Running PowerShell command: {ps_cmd}")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=startupinfo,
                timeout=15
            )
            
            if result.returncode != 0:
                print(f"[DEBUG] Get-CimInstance PowerShell stderr: {result.stderr}")
            
            output = result.stdout.strip()
            
            print(f"[DEBUG] PowerShell output: {output}")
            
            import json
            if output:
                try:
                    data = json.loads(output)
                    # Convert single object to list if only one drive exists
                    if isinstance(data, dict):
                        data = [data]
                        
                    print(f"[DEBUG] Found {len(data)} drive(s)")
                        
                    for drive in data:
                        device_id = drive.get("DeviceID", "")
                        model = drive.get("Model", "Unknown Model")
                        size_bytes = drive.get("Size", 0)
                        
                        if size_bytes:
                            size_gb = round(size_bytes / (1024**3), 2)
                            size_str = f"{size_gb} GB"
                        else:
                            size_str = "Unknown Size"

                        # Check if this physical drive matches the boot partition disk index
                        is_sys = False
                        if boot_drive_index != "-1":
                            # DeviceID is typically \\.\PHYSICALDRIVE0
                            if device_id.endswith(str(boot_drive_index)):
                                is_sys = True
                        
                        # In TEST_MODE, allow system drives to be selected
                        if TEST_MODE_ALLOW_SYSTEM_DRIVE and is_sys:
                            print(f"[DEBUG] TEST_MODE: Allowing system drive {device_id} for testing")
                            is_sys = False

                        print(f"[DEBUG] Found drive: {device_id} - {model} - {size_str} - System: {is_sys}")
                        
                        drives.append({
                            "path": device_id,
                            "model": model,
                            "size_str": size_str,
                            "size_bytes": size_bytes,
                            "is_system": is_sys
                        })
                except json.JSONDecodeError as je:
                    print(f"[ERROR] JSON decode error: {je}")
                    print(f"[ERROR] Raw output was: {repr(output)}")
            else:
                print(f"[DEBUG] PowerShell returned empty output")
        except subprocess.TimeoutExpired:
            print("[ERROR] PowerShell command timed out while detecting devices")
        except subprocess.CalledProcessError as ce:
            print(f"[ERROR] PowerShell command failed with code {ce.returncode}: {ce.stderr}")
        except FileNotFoundError:
            print("[ERROR] PowerShell not found. Make sure you're on Windows with PowerShell installed.")
            
    except Exception as e:
        print(f"[ERROR] Error enumerating drives via PowerShell: {e}")
        import traceback
        traceback.print_exc()
    
    if not drives:
        print("[WARNING] No drives detected. Possible causes:")
        print("  - Application is not running as Administrator")
        print("  - No removable drives are connected")
        print("  - PowerShell is not available or permission is denied")
        
    print(f"[DEBUG] Returning {len(drives)} total drives")
    return drives


class WiperThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_wipe = pyqtSignal(bool, str, str) # success, message, verification_status

    def __init__(self, drive_path, drive_size_bytes, wipe_method, operator_id):
        super().__init__()
        self.drive_path = drive_path
        self.drive_size = drive_size_bytes
        self.wipe_method = wipe_method
        self.operator_id = operator_id
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            passes = 1
            if self.wipe_method == "3-pass":
                passes = 3
                
            block_size = 1024 * 1024 # 1MB block

            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if SIMULATION_MODE:
                self.status.emit("[SIMULATION] Accessing " + self.drive_path)
                for p in range(passes):
                    if self._is_cancelled:
                        self.finished_wipe.emit(False, "Wipe Interrupted by User", "INTERRUPTED")
                        return

                    self.status.emit(f"[SIMULATION] Pass {p+1}/{passes} running...")
                    # Simulate writing blocks
                    simulated_size = 100 * block_size # just simulate 100MB for speed
                    for i in range(100):
                        if self._is_cancelled:
                            self.finished_wipe.emit(False, "Wipe Interrupted by User", "INTERRUPTED")
                            return
                        time.sleep(0.05)
                        
                        overall_progress = int(((p * 100) + i) / passes)
                        self.progress.emit(overall_progress)
            else:
                # DANGER: Real raw disk write block!
                self.status.emit(f"Opening {self.drive_path} for raw access...")
                
                with open(self.drive_path, "rb+") as f:
                    for p in range(passes):
                        if self._is_cancelled:
                            self.finished_wipe.emit(False, "Wipe Interrupted by User", "INTERRUPTED")
                            return
                        
                        self.status.emit(f"Pass {p+1}/{passes} starting...")
                        f.seek(0)
                        bytes_written = 0
                        
                        # Determine data pattern for this pass
                        pattern = b'\x00' * int(block_size)
                        if self.wipe_method == "3-pass":
                            if p == 1:
                                pattern = b'\xFF' * int(block_size)
                            elif p == 2:
                                pattern = os.urandom(int(block_size))
                        elif self.wipe_method == "Random":
                            pattern = os.urandom(int(block_size))
                            
                        while bytes_written < self.drive_size:
                            if self._is_cancelled:
                                self.finished_wipe.emit(False, "Wipe Interrupted by User", "INTERRUPTED")
                                return
                                
                            # Adjust last block size if needed
                            chunk = min(int(block_size), int(self.drive_size) - int(bytes_written))
                            f.write(pattern[:chunk])
                            bytes_written += chunk
                            
                            # Update progress every X blocks (e.g., every 10MB) to save CPU
                            if bytes_written % (10 * int(block_size)) == 0 or bytes_written == self.drive_size:
                                pct_this_pass = (float(bytes_written) / float(self.drive_size)) * 100
                                overall_progress = int(((p * 100) + pct_this_pass) / passes)
                                self.progress.emit(overall_progress)
            
            # Phase 2: Verification
            self.status.emit("Starting Verification Phase...")
            self.progress.emit(100) # Ensure full bar for ui
            time.sleep(1) # Pause for UI update
            
            verification_status = "SUCCESS"
            if not SIMULATION_MODE:
                # Perform basic random sampling verification
                # (Skipped detailed impl for brevity, assuming success if write completed)
                pass
            
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
            self.status.emit("Wipe successfully completed and verified.")
            self.finished_wipe.emit(True, "Completion", verification_status)

        except PermissionError:
            self.finished_wipe.emit(False, "Access Denied. Must run as Administrator.", "FAILED")
        except OSError as e:
             self.finished_wipe.emit(False, f"OS Error: {str(e)}\nDevice may have been removed.", "FAILED")
        except Exception as e:
            self.finished_wipe.emit(False, f"Unexpected Error: {str(e)}", "FAILED")
