# Guia de Compilacion - SAC Sistema de Automatizacion de Consultas

## Requisitos Previos

### Sistema Operativo
- **Windows 10/11** (recomendado para produccion)
- **Linux** (Ubuntu 20.04+, CentOS 7+)

### Dependencias del Sistema

#### Windows
```cmd
# Instalar driver IBM DB2 ODBC
# Descargar desde: https://www.ibm.com/docs/en/db2/11.5?topic=packages-ibm-data-server-driver-package

# Python 3.8+ con pip
python --version
pip --version
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev python3-dev python3-pip

# CentOS/RHEL
sudo yum install unixODBC unixODBC-devel python3-devel python3-pip
```

### Python y Dependencias
```bash
# Instalar dependencias del proyecto
pip install -r requirements.txt
```

---

## Compilacion Rapida

### Opcion 1: Usar el Script de Compilacion (Recomendado)

```bash
# Compilacion estandar
python build_exe.py

# Limpiar compilaciones anteriores y recompilar
python build_exe.py --clean

# Ver todas las opciones
python build_exe.py --help
```

### Opcion 2: Usar PyInstaller Directamente

```bash
# Usar archivo de especificacion
pyinstaller SAC.spec

# O generar ejecutable simple
pyinstaller --onefile --name=SAC_Chedraui_427 main.py
```

---

## Opciones del Script build_exe.py

| Opcion | Descripcion |
|--------|-------------|
| `--clean` | Elimina compilaciones anteriores antes de compilar |
| `--onedir` | Genera una carpeta en lugar de archivo unico |
| `--debug` | Incluye informacion de depuracion |
| `--no-spec` | No usa el archivo SAC.spec |
| `--clean-only` | Solo limpia, no compila |

### Ejemplos

```bash
# Compilacion limpia (recomendado para produccion)
python build_exe.py --clean

# Compilacion en modo directorio (mas facil de depurar)
python build_exe.py --onedir

# Solo limpiar archivos de compilacion
python build_exe.py --clean-only
```

---

## Estructura del Ejecutable Generado

```
dist/
├── SAC_Chedraui_427.exe    # Ejecutable principal (Windows)
├── SAC_Chedraui_427        # Ejecutable principal (Linux)
├── env.template            # Plantilla de configuracion
├── INSTRUCCIONES.txt       # Guia de uso
├── README.md               # Documentacion
└── output/
    ├── logs/               # Directorio para logs
    └── resultados/         # Directorio para reportes
```

---

## Configuracion Post-Compilacion

### 1. Crear archivo .env

```bash
# Copiar plantilla
cp env.template .env

# Editar con las credenciales reales
nano .env   # Linux
notepad .env  # Windows
```

### 2. Variables Obligatorias

```bash
# Base de datos DB2
DB_USER=tu_usuario_db2
DB_PASSWORD=tu_password_db2

# Correo electronico (Office 365)
EMAIL_USER=tu_correo@chedraui.com.mx
EMAIL_PASSWORD=tu_password_correo
```

### 3. Variables Opcionales

```bash
# Telegram (para alertas)
TELEGRAM_TOKEN=tu_token_bot
TELEGRAM_CHAT_ID=tu_chat_id

# Modo debug
DEBUG=false
LOG_LEVEL=INFO
```

---

## Ejecucion del Ejecutable

### Windows
```cmd
# Doble clic en SAC_Chedraui_427.exe
# O desde terminal:
SAC_Chedraui_427.exe

# Con opciones:
SAC_Chedraui_427.exe --oc OC12345
SAC_Chedraui_427.exe --reporte-diario
SAC_Chedraui_427.exe --menu
```

### Linux
```bash
# Dar permisos de ejecucion
chmod +x SAC_Chedraui_427

# Ejecutar
./SAC_Chedraui_427

# Con opciones:
./SAC_Chedraui_427 --oc OC12345
./SAC_Chedraui_427 --reporte-diario
```

---

## Solucion de Problemas

### Error: "libodbc.so.2 not found" (Linux)
```bash
sudo apt-get install unixodbc unixodbc-dev
```

### Error: "ODBC Driver not found"
- Instalar IBM DB2 ODBC Driver
- Verificar configuracion en odbcinst.ini y odbc.ini

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

### Error: "cryptography module error"
```bash
# Actualizar cryptography
pip install --upgrade cryptography

# O excluir en compilacion
pyinstaller --exclude-module=cryptography main.py
```

### Ejecutable muy grande
```bash
# Usar UPX para comprimir (requiere UPX instalado)
pyinstaller --onefile --upx-dir=/path/to/upx main.py
```

---

## Notas de Seguridad

1. **NUNCA incluir .env en el ejecutable** - contiene credenciales
2. **Distribuir env.template** como plantilla vacia
3. **Verificar permisos** del directorio output/
4. **Logs contienen informacion sensible** - gestionar rotacion

---

## Soporte

**CEDIS Cancun 427 - Equipo de Sistemas**
- Julian Alexander Juarez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Diaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas

---

*Documento generado automaticamente - SAC v1.0.0*
*Tiendas Chedraui S.A. de C.V.*
