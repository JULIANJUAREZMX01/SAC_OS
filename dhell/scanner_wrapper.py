"""
SACITY OS - Scanner Wrapper
Provides abstraction for Symbol MC9190 barcode scanner hardware.
Falls back to simulation mode if hardware is unavailable.
"""

import sys
import time
import threading
from typing import Callable, Optional

# Try to import ctypes for Windows CE DLL access
try:
    import ctypes
    CTYPES_AVAILABLE = True
except ImportError:
    CTYPES_AVAILABLE = False

class ScannerMode:
    """Scanner operation modes"""
    HARDWARE = "hardware"
    SIMULATION = "simulation"
    DISABLED = "disabled"

class SymbolScanner:
    """
    Wrapper for Symbol MC9190 Scanner Hardware
    
    Supports:
    - 1D Barcodes (Code 39, Code 128, EAN, UPC)
    - 2D Barcodes (QR, DataMatrix) if hardware supports
    - Async callback-based scanning
    - Graceful fallback to simulation
    """
    
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.scanning = False
        self.last_code = None
        self.callback = None
        self.scanner_thread = None
        self._dll = None
        
        # Auto-detect mode
        if mode == "auto":
            self.mode = self._detect_hardware()
        
        if self.mode == ScannerMode.HARDWARE:
            self._init_hardware()
    
    def _detect_hardware(self) -> str:
        """Detect if we're running on real MC9190 hardware"""
        # Check for Windows CE
        if sys.platform == 'win32':
            try:
                # Try to load Symbol Scanner DLL
                if CTYPES_AVAILABLE:
                    # Common paths for Symbol Scanner SDK on WinCE
                    dll_paths = [
                        "\\Windows\\symbol_scanner.dll",
                        "\\Program Files\\Symbol\\scanner.dll",
                        "scanner.dll"
                    ]
                    
                    for path in dll_paths:
                        try:
                            ctypes.WinDLL(path)
                            return ScannerMode.HARDWARE
                        except:
                            continue
            except:
                pass
        
        # Fallback to simulation
        return ScannerMode.SIMULATION
    
    def _init_hardware(self):
        """Initialize hardware scanner via DLL"""
        if not CTYPES_AVAILABLE:
            print("[SCANNER] ctypes not available, falling back to simulation")
            self.mode = ScannerMode.SIMULATION
            return
        
        try:
            # Load the DLL (path may vary)
            self._dll = ctypes.WinDLL("scanner.dll")
            
            # Define function signatures (example - adjust based on actual SDK)
            # int Scanner_Open(void)
            self._dll.Scanner_Open.restype = ctypes.c_int
            
            # int Scanner_Read(char* buffer, int maxlen)
            self._dll.Scanner_Read.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self._dll.Scanner_Read.restype = ctypes.c_int
            
            # void Scanner_Close(void)
            self._dll.Scanner_Close.restype = None
            
            # Open scanner
            result = self._dll.Scanner_Open()
            if result != 0:
                raise Exception(f"Scanner_Open failed with code {result}")
                
        except Exception as e:
            print(f"[SCANNER] Hardware init failed: {e}")
            print("[SCANNER] Falling back to simulation mode")
            self.mode = ScannerMode.SIMULATION
            self._dll = None
    
    def start_scan(self, callback: Optional[Callable[[str], None]] = None):
        """
        Start scanning for barcodes
        
        Args:
            callback: Function to call when barcode is scanned (receives code as string)
        """
        if self.scanning:
            return
        
        self.scanning = True
        self.callback = callback
        
        if self.mode == ScannerMode.HARDWARE:
            self._start_hardware_scan()
        else:
            self._start_simulation_scan()
    
    def _start_hardware_scan(self):
        """Start hardware scanner thread"""
        def scan_loop():
            buffer = ctypes.create_string_buffer(256)
            
            while self.scanning:
                try:
                    # Read from scanner (blocking call with timeout)
                    result = self._dll.Scanner_Read(buffer, 256)
                    
                    if result > 0:
                        code = buffer.value.decode('ascii', errors='ignore')
                        self.last_code = code
                        
                        if self.callback:
                            self.callback(code)
                    
                    time.sleep(0.1)  # Prevent CPU spinning
                    
                except Exception as e:
                    print(f"[SCANNER] Read error: {e}")
                    time.sleep(0.5)
        
        self.scanner_thread = threading.Thread(target=scan_loop, daemon=True)
        self.scanner_thread.start()
    
    def _start_simulation_scan(self):
        """Start simulation mode (for testing without hardware)"""
        # In simulation, scanning is manual via trigger_simulation()
        pass
    
    def trigger_simulation(self, code: Optional[str] = None):
        """
        Manually trigger a scan in simulation mode
        
        Args:
            code: Barcode to simulate, or None for random
        """
        if self.mode != ScannerMode.SIMULATION:
            return
        
        if code is None:
            # Generate random barcode
            import random
            code = f"SIM-{random.randint(100000, 999999)}"
        
        self.last_code = code
        
        if self.callback:
            self.callback(code)
    
    def stop_scan(self):
        """Stop scanning"""
        self.scanning = False
        
        if self.scanner_thread:
            self.scanner_thread.join(timeout=2.0)
            self.scanner_thread = None
    
    def get_last_code(self) -> Optional[str]:
        """Get the last scanned barcode"""
        return self.last_code
    
    def get_status(self) -> dict:
        """Get scanner status"""
        return {
            "mode": self.mode,
            "scanning": self.scanning,
            "last_code": self.last_code,
            "hardware_available": self._dll is not None
        }
    
    def close(self):
        """Close scanner and release resources"""
        self.stop_scan()
        
        if self._dll and self.mode == ScannerMode.HARDWARE:
            try:
                self._dll.Scanner_Close()
            except:
                pass
        
        self._dll = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Global scanner instance
_scanner_instance = None

def get_scanner() -> SymbolScanner:
    """Get global scanner instance (singleton)"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SymbolScanner(mode="auto")
    return _scanner_instance


if __name__ == "__main__":
    # Test the scanner
    print("=== SACITY Scanner Test ===")
    
    scanner = get_scanner()
    status = scanner.get_status()
    
    print(f"Mode: {status['mode']}")
    print(f"Hardware Available: {status['hardware_available']}")
    
    def on_scan(code):
        print(f"[SCANNED] {code}")
    
    scanner.start_scan(callback=on_scan)
    
    if status['mode'] == ScannerMode.SIMULATION:
        print("\nSimulation mode - triggering test scans...")
        for i in range(3):
            time.sleep(1)
            scanner.trigger_simulation()
    else:
        print("\nHardware mode - waiting for scans (press Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    scanner.stop_scan()
    print("\nTest complete.")
