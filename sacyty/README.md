# SACYTY - Sistema de Automatización Chedraui (Modelo TinY)

```
███████╗ █████╗  ██████╗██╗   ██╗████████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝╚══██╔══╝╚██╗ ██╔╝
███████╗███████║██║      ╚████╔╝    ██║    ╚████╔╝
╚════██║██╔══██║██║       ╚██╔╝     ██║     ╚██╔╝
███████║██║  ██║╚██████╗   ██║      ██║      ██║
╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝      ╚═╝      ╚═╝
```

## Descripción

SACYTY es la versión **ligera** del Sistema SAC (Sistema de Automatización de Consultas), diseñada específicamente para:

- **Despliegue rápido** en dispositivos a recuperar
- **Mínimo consumo de recursos** (~35% del sistema completo)
- **Funcionalidad esencial** sin dependencias pesadas
- **Integración** con la suite SAC principal

## Características

| Característica | SACYTY (Ligero) | SAC (Completo) |
|----------------|-----------------|----------------|
| Tamaño | ~100KB | ~3MB |
| Dependencias | 1-3 | 40+ |
| GUI | No | Sí |
| Dashboard Web | No | Sí |
| Telegram/WhatsApp | No | Sí |
| Animaciones | No | Sí |
| Conexión DB2 | Sí | Sí |
| Validaciones | Esenciales | Completas |
| Reportes Excel | Básicos | Avanzados |

## Estructura del Módulo

```
sacyty/
├── __init__.py           # Inicializador del paquete
├── sacyty_core.py        # Núcleo del sistema
├── sacyty_config.py      # Configuración ligera
├── sacyty_validator.py   # Validador esencial
├── sacyty_installer.py   # Instalador para dispositivos
├── requirements_sacyty.txt # Dependencias mínimas
└── README.md             # Este archivo
```

## Instalación

### Método 1: Desde el repositorio SAC

```bash
# Clonar repositorio
git clone https://github.com/tu-org/SAC_V01_427_ADMJAJA.git
cd SAC_V01_427_ADMJAJA

# Ejecutar SACYTY directamente
python SACYTY.py
```

### Método 2: Instalación independiente

```bash
# Instalar en ubicación por defecto
python SACYTY.py --install

# Instalar en ubicación específica
python SACYTY.py --install --path /opt/sacyty

# Incluir dependencias opcionales (pandas, openpyxl)
python SACYTY.py --install --optional
```

### Método 3: Instalación manual mínima

```bash
# Solo dependencia esencial
pip install python-dotenv

# Con reportes Excel
pip install python-dotenv pandas openpyxl
```

## Uso

### Modo Interactivo

```bash
python SACYTY.py
```

### Línea de Comandos

```bash
# Ver estado del sistema
python SACYTY.py --status

# Verificación de salud completa
python SACYTY.py --health

# Validar OC específica
python SACYTY.py --validate OC750384123456

# Exportar reporte a JSON
python SACYTY.py --export

# Exportar a ubicación específica
python SACYTY.py --export /tmp/reporte.json
```

### Uso Programático

```python
from sacyty import SACYTYCore, SACYTYConfig, SACYTYValidator

# Crear instancia
sacyty = SACYTYCore()

# Inicializar
success, messages = sacyty.initialize()

# Obtener estado
status = sacyty.get_status()

# Ejecutar verificación de salud
health = sacyty.run_health_check()

# Validar OC
result = sacyty.validate_oc("750384123456")

# Generar reporte
report = sacyty.generate_status_report()
print(report)

# Cerrar conexiones
sacyty.close()
```

### Context Manager

```python
with SACYTYCore() as sacyty:
    health = sacyty.run_health_check()
    print(f"Estado: {'OK' if health['all_passed'] else 'ERROR'}")
```

## Configuración

### Archivo .env

Crear archivo `.env` en la raíz del proyecto:

```env
# Base de Datos DB2 (Manhattan WMS)
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# CEDIS
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancún
CEDIS_REGION=Sureste

# Sistema
LOG_LEVEL=INFO
DEBUG=false
```

### Uso sin .env

```python
from sacyty import SACYTYConfig

config = SACYTYConfig()
config.database.user = "mi_usuario"
config.database.password = "mi_password"

sacyty = SACYTYCore(config)
```

## Validaciones Disponibles

### Sistema
- Versión de Python
- Módulos esenciales
- Módulos opcionales

### Configuración
- Credenciales de base de datos
- Código de CEDIS
- Rutas del sistema
- Configuración de email

### Conexión
- Conectividad DB2
- Query de prueba

### Datos
- Formato de OC
- Estructura de DataFrame
- Comparación OC vs Distribuciones

## API Reference

### SACYTYCore

```python
class SACYTYCore:
    def initialize() -> Tuple[bool, List[str]]
    def execute_query(query: str) -> Tuple[bool, Any]
    def validate_oc(oc_number: str) -> ValidationResult
    def run_health_check() -> Dict[str, Any]
    def generate_status_report() -> str
    def export_health_report(path: Path) -> str
    def get_status() -> Dict[str, Any]
    def close() -> None
```

### SACYTYValidator

```python
class SACYTYValidator:
    def validate_system() -> ValidationResult
    def validate_config(config) -> ValidationResult
    def validate_db_connection(connection) -> ValidationResult
    def validate_oc_number(oc: str) -> ValidationResult
    def validate_dataframe(df, columns, name) -> ValidationResult
    def validate_oc_vs_distributions(oc_total, dist_total, oc) -> ValidationResult
    def run_all_validations(config, connection) -> Dict[str, ValidationResult]
```

### SACYTYConfig

```python
class SACYTYConfig:
    database: DatabaseConfig
    cedis: CEDISConfig
    email: EmailConfig
    paths: PathsConfig
    logging: LoggingConfig

    def validate() -> Tuple[bool, List[str]]
    def to_dict() -> Dict[str, Any]
    def print_status() -> None
```

## Severidades de Error

| Severidad | Código | Descripción |
|-----------|--------|-------------|
| CRITICO | CRITICAL | Requiere acción inmediata |
| ALTO | HIGH | Prioridad alta |
| MEDIO | MEDIUM | Prioridad media |
| BAJO | LOW | Prioridad baja |
| INFO | INFO | Informativo |

## Comparación con SAC Completo

### Lo que incluye SACYTY:
- Conexión básica a DB2
- Validación de OC
- Validación de datos
- Reportes de texto
- Exportación JSON
- Configuración vía .env

### Lo que NO incluye SACYTY:
- Dashboard web (Flask)
- GUI interactivo
- Notificaciones Telegram/WhatsApp
- Animaciones de terminal
- Agente IA
- Módulos de dispositivos específicos
- UPS backup
- Generación avanzada de Excel
- Charts y gráficos

## Casos de Uso

### 1. Recuperación de Dispositivo
```bash
# En dispositivo recién formateado
pip install python-dotenv
python SACYTY.py --install
python SACYTY.py --health
```

### 2. Verificación Rápida
```bash
# Verificar estado en menos de 5 segundos
python SACYTY.py --status --quiet
```

### 3. Validación de OC
```bash
# Antes de procesar una OC
python SACYTY.py --validate 750384123456
```

### 4. Monitoreo Básico
```python
# Script de monitoreo simple
from sacyty import SACYTYCore

with SACYTYCore() as s:
    health = s.run_health_check()
    if not health['all_passed']:
        print("ALERTA: Sistema con errores")
```

## Contribución

SACYTY es código abierto para la comunidad de Chedraui. Las contribuciones son bienvenidas.

## Licencia

Desarrollado por Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún

© 2025 Tiendas Chedraui S.A. de C.V.

---

> "Las máquinas y los sistemas al servicio de los analistas"
