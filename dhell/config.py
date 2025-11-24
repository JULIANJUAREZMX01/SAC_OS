# Configuración Global de SACITY OS / DHELL

# Import device detection (with fallback if not available)
try:
    from .device_info import get_device_info
    _device = get_device_info()
    _recommended = _device.get_recommended_config()
    AUTO_DETECT = True
except:
    _recommended = {}
    AUTO_DETECT = False

# Modo de ahorro de energía / recursos
# True: Animaciones simplificadas, menos refrescos de pantalla
# False: Animaciones completas, efectos visuales máximos
ECO_MODE = _recommended.get('eco_mode', False)

# Velocidad de animaciones (segundos)
# Aumentar si el dispositivo es muy lento
SPEED_MULTIPLIER = _recommended.get('speed_multiplier', 1.0)

# Configuración de Red
DEFAULT_PORT = 23
CONNECTION_TIMEOUT = 5.0

# Configuración de UI
THEME = "VIRUS"  # Opciones: VIRUS, STANDARD (Futuro)
MAX_ANIMATION_FPS = _recommended.get('max_animation_fps', 30)

# Configuración de Batería
DISABLE_ANIMATIONS_ON_LOW_BATTERY = _recommended.get('disable_animations_on_low_battery', False)
LOW_BATTERY_THRESHOLD = _recommended.get('low_battery_threshold', 20)  # percent

# Device Detection
DEVICE_AUTO_DETECTED = AUTO_DETECT

def get_current_config():
    """Get current configuration as dict"""
    return {
        'eco_mode': ECO_MODE,
        'speed_multiplier': SPEED_MULTIPLIER,
        'default_port': DEFAULT_PORT,
        'connection_timeout': CONNECTION_TIMEOUT,
        'theme': THEME,
        'max_animation_fps': MAX_ANIMATION_FPS,
        'disable_animations_on_low_battery': DISABLE_ANIMATIONS_ON_LOW_BATTERY,
        'low_battery_threshold': LOW_BATTERY_THRESHOLD,
        'auto_detected': DEVICE_AUTO_DETECTED
    }

def should_disable_animations():
    """Check if animations should be disabled based on battery"""
    if not DISABLE_ANIMATIONS_ON_LOW_BATTERY:
        return False
    
    try:
        from .device_info import get_device_info
        device = get_device_info()
        battery = device.get_battery()
        
        if battery['present'] and battery['percent'] < LOW_BATTERY_THRESHOLD:
            return True
    except:
        pass
    
    return False

