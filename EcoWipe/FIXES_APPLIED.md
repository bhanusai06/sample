# EcoWipe - Fixes Applied

## Summary of Changes

This document outlines all fixes applied to resolve the Administrator privilege and device detection issues.

---

## Problem 1: Application Not Elevating to Admin

### Issue
When running the application, it would check for admin privileges but fail to properly elevate the process.

### Solution
**File: `main.py`**
- Implemented automatic privilege elevation using `ShellExecuteW` with the "runas" verb
- When not running as admin, the application now:
  1. Attempts automatic elevation via Windows UAC (User Account Control)
  2. User sees the UAC prompt and can approve the elevation
  3. Application restarts with full admin privileges
  4. If user denies UAC prompt, shows a helpful error message

### Technical Details
```python
# Uses ShellExecute with 'runas' verb to request admin privileges
ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)

# If ShellExecute returns > 32, it was successful
if ret > 32:
    sys.exit(0)  # Admin elevation successful
```

---

## Problem 2: Device Detection Not Working

### Issue
Device detection returned 0 drives even with admin privileges, due to:
- Missing admin privilege pre-check in engine.py
- Poor error handling and debugging information
- No timeout handling for PowerShell commands
- Incomplete error recovery logic

### Solution
**File: `engine.py`**

#### Added Admin Check Function
```python
def is_admin():
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception as e:
        print(f"[DEBUG] Failed to check admin status: {e}")
        return False
```

#### Enhanced get_available_drives() Function
1. **Pre-flight Admin Check**
   - Function now checks if running as admin at the start
   - Returns empty list with clear error message if not admin
   - Prevents wasting time on PowerShell commands that will fail

2. **Improved PowerShell Execution**
   - Added `timeout` parameter (15 seconds) to prevent hung processes
   - Added `subprocess.TimeoutExpired` exception handling
   - Added proper error handling for command failures

3. **Better Fallback Strategy**
   - Primary method (Get-Disk) now returns early if successful
   - Only attempts fallback if primary fails
   - More granular error reporting at each stage

4. **Enhanced Debug Output**
   - Detailed logging at each step
   - Clear error messages for troubleshooting
   - Warnings when no drives are detected with possible causes

### Error Handling Improvements
- Timeout handling: Commands that take too long are properly terminated
- CalledProcessError: Captures PowerShell return codes and stderr
- FileNotFoundError: Indicates if PowerShell is missing
- JSONDecodeError: Shows raw output for debugging

---

## Problem 3: Missing Admin Helpers

### Solution
**File: `engine.py`**
- Imported necessary modules: `sys` and `ctypes`
- Added independent `is_admin()` function in engine.py (not reliant on utils.py)
- This ensures device detection can validate admin status even in edge cases

---

## Testing the Fixes

### Test 1: Automatic Admin Elevation
1. Run `EcoWipe.exe` or `python main.py` as regular user
2. **Expected**: UAC prompt appears asking for admin permission
3. **Expected**: After approving UAC, app runs with admin privileges

### Test 2: Device Detection
1. Once running with admin privileges, devices should be detected
2. **Expected**: Multiple fallback methods tried (Get-Disk, then Get-CimInstance)
3. **Expected**: Debug output shows which method succeeded

### Test 3: Device Detection Debugging
Option A: Using batch file (recommended)
```bash
RUN_AS_ADMIN.bat
```

Option B: Manual PowerShell test
```powershell
# Run PowerShell as Administrator first, then:
cd "c:\path\to\EcoWipe"
python test_devices.py
```

---

## Files Modified

1. **main.py**
   - Added automatic UAC elevation using ShellExecute
   - Improved error messages for users

2. **engine.py**
   - Added `is_admin()` function
   - Enhanced `get_available_drives()` with:
     - Admin privilege pre-check
     - Timeout handling
     - Better error messages
     - Improved fallback logic

## Files Added

1. **RUN_AS_ADMIN.bat**
   - Batch script to ensure admin elevation
   - Convenient way to launch the application properly

---

## How Device Detection Works Now

### Diagram
```
Application Start
    ↓
[Admin Check] ← Is running as admin?
    ├─ NO → Elevate via UAC → Restart as admin
    └─ YES → Continue
    ↓
[Device Detection]
    ↓
[Method 1: Get-Disk] ← Trial PowerShell Get-Disk command
    ├─ Success → Parse JSON → Return drives → Done ✓
    ├─ Timeout → Log warning → Try next method
    └─ Error → Log error → Try next method
    ↓
[Method 2: Get-CimInstance] ← Fallback WMI query
    ├─ Success → Parse JSON → Return drives → Done ✓
    ├─ Error → Log details → Return empty
    └─ No drives found → Notify user
    ↓
[Boot Drive Identification]
    └─ Mark system drive so it can't be accidentally wiped
```

---

## Troubleshooting

### "Device detection requires Administrator privileges"
**Solution**: The application is not running as admin.
- Ensure you ran it with admin privileges
- Try using `RUN_AS_ADMIN.bat` file
- Or right-click EcoWipe.exe → "Run as administrator"

### "No devices detected" even with admin privileges
**Possible causes**:
1. No removable drives/USB drives connected
2. PowerShell is not properly installed or accessible
3. Windows permissions are blocking device enumeration
4. Device drivers are missing (update chipset drivers)

**Solutions**:
- Connect a USB drive and try again
- Reinstall PowerShell
- Restart computer and try again
- Check Windows Update for driver updates

### "PowerShell command timed out"
**Possible causes**:
1. System is under heavy load
2. Many devices connected causing enumeration to take long
3. Network drives causing slowdown

**Solutions**:
- Close other applications
- Disconnect network drives
- Restart computer

---

## UAC (User Account Control) Configuration

The PyInstaller configuration already includes:
```python
uac_admin=True
```

This ensures the compiled executable requests admin privileges automatically when installed properly.

---

## Additional Notes

- **SIMULATION_MODE = True**: Current configuration doesn't actually wipe disks. This is safe for testing.
- **TEST_MODE_ALLOW_SYSTEM_DRIVE = False**: System drive cannot be accidentally selected for wiping (safety feature).
- All changes are backward compatible with existing code.
- Debug logging is enabled by default for troubleshooting.

---

## Summary

The application should now:
✅ Automatically request admin privileges on first run  
✅ Properly detect connected USB and external drives  
✅ Provide clear error messages if something goes wrong  
✅ Handle edge cases and timeouts gracefully  
✅ Log detailed debug information for troubleshooting  

**To run properly**: Execute with admin privileges (automatic via UAC or use RUN_AS_ADMIN.bat)
