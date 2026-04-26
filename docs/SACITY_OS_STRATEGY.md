# SACITY OS - Firmware Strategy

## Objective
Create a minimal, "stripped" Windows CE 6.0 environment for the Symbol MC9190 that runs **only** the SACITY Client, maximizing performance and battery life while minimizing distractions and resource usage.

## Architecture: "Stripped WinCE"

The goal is to remove the Windows Explorer shell (`explorer.exe`) and replace it with a custom bootloader that launches the Python environment and our `sacity_client_ce.py`.

### 1. Boot Process
1.  **Kernel Load**: Standard WinCE Kernel (`nk.exe`) loads.
2.  **Driver Load**: Essential drivers load (Display, Keypad, WiFi, Scanner).
3.  **Shell Override**: Instead of `explorer.exe`, the registry is modified to launch our startup script.

### 2. Registry Modifications
To replace the shell, modify `HKLM\Init`:

```reg
[HKEY_LOCAL_MACHINE\init]
"Launch50"="explorer.exe"  <-- DELETE or RENAME
"Launch50"="\\Program Files\\Python\\python.exe"
"Depend50"=hex:14,00, 1e,00
```

**Command Line Arguments**:
The Python executable should be called with the path to our client:
`\Program Files\Python\python.exe \Program Files\SACITY\sacity_client_ce.py`

### 3. Essential Drivers
We must retain these specific drivers from the OEM BSP (Board Support Package):
*   `ddi.dll` (Display)
*   `keypad.dll` (Keyboard)
*   `ndis.dll` (Network Stack)
*   `symbol_scanner.dll` (Barcode Scanner - Proprietary)
*   `wlan_adapter.dll` (WiFi - Proprietary)

### 4. Python Environment
Since WinCE does not have native Python, we deploy a portable Python 2.7 or 3.x build compiled for ARM/WinCE (e.g., `PythonCE`).
*   **Location**: `\Program Files\Python`
*   **Size**: ~4MB (stripped standard library)

## Deployment Strategy

1.  **Clean Boot**: Perform a cold boot to reset device.
2.  **Push Files**: Use `sacity_installer_suite.py` to push:
    *   Python Runtime
    *   SACITY Client (`sacity_client_ce.py`, `sacity_tui.py`, `sacity_shell.py`)
3.  **Registry Patch**: Push a `.reg` file to modify the startup process.
4.  **Reboot**: Device boots directly into SACITY OS (Black screen, Red text).

## Fallback / Recovery
*   **Safe Mode**: Hold specific key combo (e.g., `1` + `9` + `Power`) to skip custom shell and load Explorer for maintenance.
