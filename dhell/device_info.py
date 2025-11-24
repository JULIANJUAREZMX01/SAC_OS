"""
SACITY OS - Device Information Module
Detects device capabilities and provides adaptive configuration
"""

import sys
import os
import platform

class DeviceInfo:
    """Device capability detection and system information"""
    
    def __init__(self):
        self._cache = {}
        self._detect_all()
    
    def _detect_all(self):
        """Run all detection routines"""
        self._cache['platform'] = self._detect_platform()
        self._cache['cpu_arch'] = self._detect_cpu_arch()
        self._cache['memory'] = self._detect_memory()
        self._cache['battery'] = self._detect_battery()
        self._cache['os_version'] = self._detect_os_version()
        self._cache['device_model'] = self._detect_device_model()
        self._cache['is_mc9190'] = self._is_mc9190()
    
    def _detect_platform(self) -> str:
        """Detect operating system platform"""
        plat = sys.platform.lower()
        
        if 'win' in plat:
            # Check if Windows CE
            if hasattr(os, 'environ') and 'PROCESSOR_ARCHITECTURE' in os.environ:
                arch = os.environ.get('PROCESSOR_ARCHITECTURE', '').lower()
                if 'arm' in arch:
                    return 'wince'
            return 'windows'
        elif 'linux' in plat:
            return 'linux'
        else:
            return plat
    
    def _detect_cpu_arch(self) -> str:
        """Detect CPU architecture"""
        try:
            machine = platform.machine().lower()
            
            if 'arm' in machine or 'aarch' in machine:
                return 'arm'
            elif 'x86_64' in machine or 'amd64' in machine:
                return 'x86_64'
            elif 'i386' in machine or 'i686' in machine:
                return 'x86'
            else:
                return machine
        except:
            return 'unknown'
    
    def _detect_memory(self) -> dict:
        """Detect memory information (MB)"""
        memory_info = {
            'total': 0,
            'available': 0,
            'percent_used': 0
        }
        
        try:
            if self._cache.get('platform') == 'wince':
                # Windows CE memory detection
                # This would require ctypes and kernel32.dll calls
                # Placeholder values for MC9190
                memory_info['total'] = 256
                memory_info['available'] = 128
                memory_info['percent_used'] = 50
            else:
                # Try psutil for desktop systems
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    memory_info['total'] = mem.total // (1024 * 1024)
                    memory_info['available'] = mem.available // (1024 * 1024)
                    memory_info['percent_used'] = mem.percent
                except ImportError:
                    # Fallback: read from /proc/meminfo on Linux
                    if os.path.exists('/proc/meminfo'):
                        with open('/proc/meminfo', 'r') as f:
                            lines = f.readlines()
                            for line in lines:
                                if 'MemTotal' in line:
                                    memory_info['total'] = int(line.split()[1]) // 1024
                                elif 'MemAvailable' in line:
                                    memory_info['available'] = int(line.split()[1]) // 1024
        except:
            pass
        
        return memory_info
    
    def _detect_battery(self) -> dict:
        """Detect battery status"""
        battery_info = {
            'present': False,
            'percent': 100,
            'charging': False,
            'ac_connected': True
        }
        
        try:
            if self._cache.get('platform') == 'wince':
                # Windows CE battery detection via ctypes
                # Placeholder for MC9190
                battery_info['present'] = True
                battery_info['percent'] = 85
                battery_info['charging'] = False
                battery_info['ac_connected'] = False
            else:
                # Try psutil for desktop
                try:
                    import psutil
                    battery = psutil.sensors_battery()
                    if battery:
                        battery_info['present'] = True
                        battery_info['percent'] = battery.percent
                        battery_info['charging'] = battery.power_plugged
                        battery_info['ac_connected'] = battery.power_plugged
                except:
                    pass
        except:
            pass
        
        return battery_info
    
    def _detect_os_version(self) -> str:
        """Detect OS version"""
        try:
            if self._cache.get('platform') == 'wince':
                # Try to detect WinCE version
                # Typically 6.0 or 6.5 for MC9190
                return 'WinCE 6.0'
            else:
                return platform.version()
        except:
            return 'unknown'
    
    def _detect_device_model(self) -> str:
        """Detect device model"""
        try:
            if self._cache.get('platform') == 'wince':
                # Check for Symbol/Motorola specific registry or files
                # Placeholder detection
                if os.path.exists('\\Windows\\symbol_scanner.dll'):
                    return 'MC9190'
            
            # Fallback to generic platform
            return platform.machine()
        except:
            return 'unknown'
    
    def _is_mc9190(self) -> bool:
        """Check if running on MC9190"""
        model = self._cache.get('device_model', '').upper()
        return 'MC9190' in model or 'MC91' in model
    
    def get_recommended_config(self) -> dict:
        """Get recommended configuration based on device capabilities"""
        config = {
            'eco_mode': False,
            'speed_multiplier': 1.0,
            'max_animation_fps': 30,
            'disable_animations_on_low_battery': False,
            'low_battery_threshold': 20
        }
        
        # Adjust for MC9190
        if self.is_mc9190():
            config['eco_mode'] = True
            config['speed_multiplier'] = 1.5  # Slower animations
            config['max_animation_fps'] = 10
            config['disable_animations_on_low_battery'] = True
        
        # Adjust for low memory
        memory = self.get_memory()
        if memory['total'] < 512:  # Less than 512MB
            config['eco_mode'] = True
            config['max_animation_fps'] = 15
        
        # Adjust for battery
        battery = self.get_battery()
        if battery['present'] and battery['percent'] < 30:
            config['eco_mode'] = True
            config['speed_multiplier'] = 2.0  # Even slower
        
        return config
    
    # Public API
    def get_platform(self) -> str:
        return self._cache.get('platform', 'unknown')
    
    def get_cpu_arch(self) -> str:
        return self._cache.get('cpu_arch', 'unknown')
    
    def get_memory(self) -> dict:
        return self._cache.get('memory', {})
    
    def get_battery(self) -> dict:
        return self._cache.get('battery', {})
    
    def get_os_version(self) -> str:
        return self._cache.get('os_version', 'unknown')
    
    def get_device_model(self) -> str:
        return self._cache.get('device_model', 'unknown')
    
    def is_mc9190(self) -> bool:
        return self._cache.get('is_mc9190', False)
    
    def is_wince(self) -> bool:
        return self.get_platform() == 'wince'
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = []
        lines.append(f"Device Model: {self.get_device_model()}")
        lines.append(f"Platform: {self.get_platform()}")
        lines.append(f"OS Version: {self.get_os_version()}")
        lines.append(f"CPU Architecture: {self.get_cpu_arch()}")
        
        mem = self.get_memory()
        lines.append(f"Memory: {mem.get('available', 0)}MB / {mem.get('total', 0)}MB available")
        
        bat = self.get_battery()
        if bat['present']:
            status = "Charging" if bat['charging'] else "Discharging"
            lines.append(f"Battery: {bat['percent']}% ({status})")
        
        return "\n".join(lines)


# Global instance
_device_info = None

def get_device_info() -> DeviceInfo:
    """Get global device info instance (singleton)"""
    global _device_info
    if _device_info is None:
        _device_info = DeviceInfo()
    return _device_info


if __name__ == "__main__":
    print("=== SACITY Device Information ===\n")
    
    device = get_device_info()
    print(device.get_summary())
    
    print("\n=== Recommended Configuration ===\n")
    config = device.get_recommended_config()
    for key, value in config.items():
        print(f"{key}: {value}")
