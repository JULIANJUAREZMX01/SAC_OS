# SACITY - Emulador Telnet/Velocity

> **Emulador completo para dispositivos Symbol MC9190 con interfaz ASCII animada**
> CEDIS Cancún 427 - Tiendas Chedraui

---

## Descripción

SACITY es un sistema completo de emulación Telnet/Velocity para dispositivos Symbol MC9000/MC9100/MC9200/MC93 que incluye:

1. **Interfaz gráfica ASCII animada** con paleta de colores Chedraui
2. **Shell emulador VT100/VT220** completo con buffer de pantalla
3. **Suite de instalación** para desplegar en dispositivos via base de carga
4. **Cliente CE** optimizado para Windows CE/Embedded

---

## Inicio Rápido

```bash
# 1. Ejecutar aplicación principal con interfaz completa
cd sacity
python sacity_main.py

# 2. O ejecutar solo el instalador
python sacity_installer_suite.py

# 3. O ejecutar solo el emulador (requiere conexión)
python sacity_shell.py

# 4. O ver demo de la interfaz
python sacity_ui.py
```

---

## Paleta de Colores Chedraui

El emulador utiliza la paleta corporativa de Chedraui:

| Color | Código RGB | Uso |
|-------|------------|-----|
| **ROJO** | `#E31837` (227, 24, 55) | Marca, menús, cabeceras estáticas |
| **VERDE** | `#00FF88` (0, 255, 136) | Estados OK, conexión, checks |
| **CYAN** | `#00C8FF` (0, 200, 255) | Alertas, instrucciones, límites |
| **NEGRO** | `#000000` | Fondo (siempre) |
| **GRIS** | `#808080` | Elementos secundarios |

### Características

- **Detección automática** de dispositivos conectados via USB/Serial/Ethernet
- **Análisis de hardware** para verificar compatibilidad
- **Instalación de drivers** necesarios automáticamente
- **Optimización** del dispositivo (limpieza de archivos temporales)
- **Despliegue** del cliente SACITY en el dispositivo
- **Configuración** de conexión al servidor WMS
- **Interfaz ASCII animada** con efectos visuales
- **Shell VT100/VT220** con emulación completa
- **Reconexión automática** con backoff exponencial
- **Heartbeat** para mantener sesión activa

---

## Dispositivos Soportados

### Familias de Dispositivos

| Familia | Modelos | OS | RAM Mín | Flash Mín |
|---------|---------|-------|---------|-----------|
| MC9000 | MC9090, MC9094, MC9096, MC9097 | Windows CE 5.0 | 64MB | 128MB |
| MC9100 | MC9190, MC9196 | Windows CE 6.0 / WEH | 256MB | 1GB |
| MC9200 | MC9290, MC9296 | Windows Embedded 7 | 256MB | 2GB |
| MC93 | MC9300, MC9306, MC9308 | Android / Windows | 2GB | 32GB |

### Bases de Carga (Muela Conectora)

| Modelo | Nombre | Slots | Conexión |
|--------|--------|-------|----------|
| ADP9000-100R | Single Slot Adapter | 1 | USB |
| CRD9000-1000 | 4-Slot Ethernet Cradle | 4 | Ethernet/USB |
| CRD9000-1001SR | 1-Slot Serial Cradle | 1 | Serial/USB |

---

## Instalación Rápida

### Requisitos

- Python 3.8+
- Windows 10 o superior (para instalación de drivers)
- Dispositivo Symbol en base de carga
- Cable USB conectando base al PC

### Instalación

```bash
# Desde el directorio raíz del proyecto
cd sacity

# Ejecutar instalador
python sacity_installer_suite.py

# O instalación automática
python sacity_installer_suite.py --auto --host 192.168.1.1 --port 23
```

### Menú Interactivo

```
SACITY INSTALLER SUITE - MENÚ PRINCIPAL
========================================

1. Instalación completa (recomendado)
2. Solo detectar dispositivos
3. Solo analizar hardware
4. Solo instalar drivers
5. Solo optimizar dispositivo
6. Solo desplegar SACITY
7. Configurar servidor WMS
8. Ver dispositivos detectados
9. Ayuda
0. Salir
```

---

## Flujo de Instalación

### Fase 1: Detección de Dispositivos

```
ESCANEANDO DISPOSITIVOS SYMBOL MC9000/MC93
==========================================
  [OK] USB/Serial: 1 dispositivo(s)
  [--] Red/Ethernet: Sin dispositivos
  [--] TelnetCE: Sin dispositivos
------------------------------------------
  TOTAL: 1 dispositivo(s) detectado(s)
```

### Fase 2: Análisis de Hardware

```
Analizando: MC9190 (COM3)
  [OK] Firmware: 5.2.5312.47000
  [OK] Batería: 78%
  [OK] RAM: 256MB
```

### Fase 3: Instalación de Drivers

```
  [OK] WMDC ya instalado
  [OK] Driver Symbol ya instalado
```

### Fase 4: Optimización

```
  [OK] Limpiar archivos temporales
  [OK] Limpiar cache
  [OK] Detener apps innecesarias
  [OK] Optimizar memoria
  [INFO] Espacio disponible: 845MB
```

### Fase 5: Despliegue de SACITY

```
  [OK] Configuración generada: sacity_config.json
  [OK] Paquete CAB preparado: sacity_mc9100.cab
  [OK] Archivos transferidos al dispositivo
  [OK] SACITY configurado para auto-inicio
```

### Fase 6 & 7: Configuración y Verificación

```
  [OK] Configuración aplicada
  [INFO] Servidor WMS: 192.168.1.1:23
  [OK] Instalación completada
```

---

## Arquitectura de Componentes

### Archivos del Instalador (PC)

| Archivo | Descripción |
|---------|-------------|
| `sacity_installer_suite.py` | Instalador maestro |
| `sacity/__init__.py` | Módulo de exportación |
| `sacity_config_template.json` | Template de configuración |

### Archivos del Cliente (Dispositivo)

| Archivo | Descripción |
|---------|-------------|
| `sacity_client_ce.py` | Cliente emulador VT100 |
| `sacity_config.json` | Configuración generada |

---

## Componentes Principales

### InstaladorSacity

Clase principal que coordina todas las fases de instalación.

```python
from sacity import InstaladorSacity, ConfiguracionSacity

# Crear instalador
instalador = InstaladorSacity()

# Configuración
config = ConfiguracionSacity(
    wms_host="192.168.1.1",
    wms_port=23,
    reconexion_automatica=True
)

# Ejecutar instalación completa
reporte = instalador.ejecutar_instalacion_completa(config)
```

### DetectorDispositivos

Detecta dispositivos Symbol conectados por múltiples métodos.

```python
from sacity import DetectorDispositivos

detector = DetectorDispositivos()
dispositivos = detector.escanear_todos(timeout=10)

for d in dispositivos:
    print(f"{d.modelo} - {d.puerto_conexion}")
```

### ConfiguracionSacity

Configuración del cliente SACITY.

```python
from sacity import ConfiguracionSacity

config = ConfiguracionSacity(
    # Servidor WMS
    wms_host="192.168.1.1",
    wms_port=23,
    wms_usuario="",
    wms_password="",

    # Sesión
    sesion_timeout=300,
    reconexion_automatica=True,
    heartbeat_intervalo=30,

    # Display
    pantalla_filas=24,
    pantalla_columnas=80,
    fuente_tamano=12,

    # Escáner
    scanner_habilitado=True,
    scanner_sufijo="\r",

    # WiFi
    wifi_ssid="CEDIS_427",
    wifi_password="***"
)
```

---

## Cliente SACITY (En Dispositivo)

### SacityClient

Cliente de emulación que corre en el dispositivo Windows CE.

```python
from sacity.sacity_client_ce import SacityClient

# Configuración
config = {
    'server': {
        'host': '192.168.1.1',
        'port': 23,
        'timeout': 30
    },
    'display': {
        'rows': 24,
        'cols': 80
    },
    'scanner': {
        'enabled': True,
        'suffix': '\r'
    }
}

# Crear y ejecutar cliente
client = SacityClient(config)
client.connect()
client.run_console()
```

### Características del Cliente

- **Emulación VT100/VT220** completa
- **Soporte de escáner** de códigos de barras
- **Reconexión automática** con backoff exponencial
- **Heartbeat** para mantener conexión
- **Compatible** con Python 2.7 y 3.x

---

## Configuración de Red

### Via WiFi

```json
{
    "network": {
        "wifi": {
            "enabled": true,
            "ssid": "CEDIS_427",
            "security": "WPA2",
            "password": "***",
            "auto_connect": true
        }
    }
}
```

### Via Ethernet (Cradle de Red)

```json
{
    "network": {
        "ethernet": {
            "enabled": true,
            "dhcp": true
        }
    }
}
```

---

## Troubleshooting

### "No se detectaron dispositivos"

1. Verificar que el dispositivo está en la base de carga
2. Verificar que la base está conectada al PC via USB
3. Verificar que el dispositivo está encendido
4. Instalar Windows Mobile Device Center (WMDC)

### "Error de conexión Telnet"

1. Verificar IP del servidor WMS
2. Verificar puerto (usualmente 23)
3. Verificar firewall no bloquea el puerto
4. Probar conectividad con: `telnet IP 23`

### "Drivers no instalados"

1. Descargar drivers de: https://www.zebra.com/drivers
2. Ejecutar instalador de drivers manualmente
3. Reiniciar PC después de instalar

### "El escáner no funciona"

1. Verificar scanner habilitado en configuración
2. Verificar sufijo correcto (usualmente `\r`)
3. Verificar batería del dispositivo

---

## Información del Dispositivo MC9190

Según las imágenes proporcionadas:

| Componente | Especificación |
|------------|----------------|
| Modelo | ADP9000-100R |
| S/N | YDJ10R |
| MFD | 07Nov14 C |
| Fabricante | Symbol Tech, N.Y. |
| Origen | Made in Mexico |
| Scanner | SE960 |
| Display | PJ037PD-01A CMI |
| Keyboard | 53-Key Keyboard |
| UART | External DUart |
| Platform | Windows Embedded |
| Trigger | Trigger 1,2 |
| Audio | CODEC (No Beeper) |
| Touch | Power Micro Touch |
| Bluetooth | BCM2046 |
| USB | Processor USB |
| WLAN Radio | Jedi 802.11bga |
| Flash | 1GB |
| RAM | 256MB |
| Accelerometer | 3 Axis 3G Kionix |
| Region | MC9190 RoW4 |
| Locale | English |

**Software Versions**: 5.2.5312.47000
- OemXIPKernel
- OemPlatform
- OemDrivers
- Fusion
- Datawedge
- OemBluetooth
- OemApps
- ProductCfg

---

## Soporte

Para problemas con la instalación:

1. Ejecutar `python sacity_installer_suite.py --help`
2. Revisar logs en `output/logs/`
3. Contactar: Equipo de Sistemas CEDIS 427

---

## Licencia

© 2025 Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados.

---

**SACITY v1.0.0** - Emulador Telnet/Velocity para Symbol MC9190
