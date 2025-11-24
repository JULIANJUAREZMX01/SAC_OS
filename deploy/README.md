# Despliegue Empresarial SAC v2.0

## CEDIS Chedraui Cancún 427 - Guía de Despliegue

---

## Contenido

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Métodos de Instalación](#métodos-de-instalación)
3. [Instalación Silenciosa (PowerShell)](#instalación-silenciosa-powershell)
4. [Configuración como Servicio Windows](#configuración-como-servicio-windows)
5. [Despliegue via GPO/SCCM](#despliegue-via-gposccm)
6. [Configuración Post-Instalación](#configuración-post-instalación)
7. [Verificación y Troubleshooting](#verificación-y-troubleshooting)

---

## Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel Core i3 o equivalente (2+ cores)
- **RAM**: 4 GB mínimo (8 GB recomendado)
- **Disco**: 500 MB espacio libre
- **Red**: Conexión a red corporativa gcch.com

### Software Requerido
- **Sistema Operativo**: Windows 10/11 Enterprise
- **Python**: 3.8 o superior
- **Driver**: IBM DB2 ODBC Driver (para conexión a Manhattan WMS)

### Conectividad de Red
- Acceso a servidor DB2: `WM260BASD:50000`
- Acceso a servidor SMTP: `smtp.office365.com:587`
- Acceso a internet (para instalación de dependencias)

---

## Métodos de Instalación

### Opción 1: Instalación Interactiva (Recomendada para equipos individuales)
```batch
python instalar_sac.py
```

### Opción 2: Instalación Silenciosa PowerShell (Para despliegue masivo)
```powershell
.\Install-SAC.ps1 -Silent -ConfigFile "\\servidor\share\sac.env"
```

### Opción 3: Como Servicio Windows
```powershell
.\Install-SAC.ps1 -Silent -CreateService -ConfigFile "\\servidor\share\sac.env"
```

---

## Instalación Silenciosa (PowerShell)

### Sintaxis Completa

```powershell
.\Install-SAC.ps1
    [-InstallPath <ruta>]        # Por defecto: C:\SAC
    [-Silent]                     # Modo sin interacción
    [-ConfigFile <ruta.env>]      # Archivo .env pre-configurado
    [-CreateService]              # Instalar como servicio Windows
    [-ServiceName <nombre>]       # Por defecto: SACMonitor
    [-LogPath <ruta>]             # Por defecto: %TEMP%\SAC_Install.log
    [-Uninstall]                  # Desinstalar SAC
    [-Force]                      # Forzar sin confirmaciones
```

### Ejemplos de Uso

#### Instalación básica silenciosa
```powershell
.\Install-SAC.ps1 -Silent
```

#### Instalación con configuración pre-definida
```powershell
.\Install-SAC.ps1 -Silent -ConfigFile "C:\Config\sac_cedis427.env"
```

#### Instalación en ruta personalizada con servicio
```powershell
.\Install-SAC.ps1 -InstallPath "D:\Sistemas\SAC" -Silent -CreateService
```

#### Desinstalación completa
```powershell
.\Install-SAC.ps1 -Uninstall -Force
```

### Archivo de Configuración (.env)

Crear archivo con las credenciales antes del despliegue:

```ini
# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN SAC - CEDIS 427
# ═══════════════════════════════════════════════════════════════

# Base de Datos DB2
DB_USER=ADMJAJA
DB_PASSWORD=contraseña_segura
DB_HOST=WM260BASD
DB_PORT=50000

# Correo Office 365
EMAIL_USER=usuario@chedraui.com.mx
EMAIL_PASSWORD=contraseña_correo

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_IDS=
```

---

## Configuración como Servicio Windows

### Usando el Script Python

```powershell
# Navegar al directorio de instalación
cd C:\SAC\deploy

# Instalar servicio
python sac_windows_service.py install

# Iniciar servicio
python sac_windows_service.py start

# Verificar estado
python sac_windows_service.py status

# Detener servicio
python sac_windows_service.py stop

# Eliminar servicio
python sac_windows_service.py remove
```

### Comandos sc.exe (Alternativo)

```batch
# Crear servicio manualmente
sc create SACMonitor binPath= "C:\SAC\sac_service.bat" start= auto displayname= "SAC Monitor - CEDIS 427"

# Configurar descripción
sc description SACMonitor "Sistema de Automatización de Consultas - Monitoreo continuo"

# Configurar reinicio automático ante fallos
sc failure SACMonitor reset= 86400 actions= restart/60000/restart/60000/restart/60000

# Iniciar servicio
net start SACMonitor

# Detener servicio
net stop SACMonitor
```

### Verificar Servicio

```powershell
# Ver estado
Get-Service SACMonitor

# Ver logs
Get-Content C:\SAC\output\logs\sac_service_*.log -Tail 50
```

---

## Despliegue via GPO/SCCM

### Preparación del Paquete

1. **Crear carpeta compartida** en servidor de archivos:
   ```
   \\servidor\Instaladores\SAC\
   ```

2. **Copiar archivos necesarios**:
   ```
   SAC\
   ├── Install-SAC.ps1
   ├── sac_windows_service.py
   ├── config\
   │   └── sac_cedis427.env
   ├── modules\
   ├── queries\
   ├── requirements.txt
   └── *.py
   ```

3. **Crear script de despliegue** (`deploy.bat`):
   ```batch
   @echo off
   PowerShell -ExecutionPolicy Bypass -File "\\servidor\Instaladores\SAC\Install-SAC.ps1" -Silent -ConfigFile "\\servidor\Instaladores\SAC\config\sac_cedis427.env" -CreateService
   ```

### GPO (Group Policy Object)

1. Abrir **Group Policy Management**
2. Crear nueva GPO: `SAC_Deployment_CEDIS427`
3. Editar → Computer Configuration → Policies → Windows Settings → Scripts
4. Agregar script de inicio: `deploy.bat`
5. Vincular GPO a OU de equipos del CEDIS

### SCCM/Endpoint Configuration Manager

1. **Crear Aplicación**:
   - Nombre: `SAC - Sistema de Automatización de Consultas`
   - Versión: `2.0.0`
   - Fabricante: `CEDIS 427 - Sistemas`

2. **Tipo de Implementación**: Script
   - Programa de instalación:
     ```
     PowerShell.exe -ExecutionPolicy Bypass -File Install-SAC.ps1 -Silent -CreateService
     ```
   - Programa de desinstalación:
     ```
     PowerShell.exe -ExecutionPolicy Bypass -File Install-SAC.ps1 -Uninstall -Force
     ```

3. **Método de Detección**:
   - Archivo: `C:\SAC\config\.instalado`
   - Servicio: `SACMonitor` (Running)

4. **Requisitos**:
   - Sistema operativo: Windows 10/11 Enterprise
   - RAM: >= 4096 MB
   - Espacio en disco: >= 500 MB

---

## Configuración Post-Instalación

### Verificar Instalación

```powershell
# Verificar archivos instalados
Test-Path C:\SAC\main.py
Test-Path C:\SAC\.env
Test-Path C:\SAC\config\.instalado

# Verificar servicio (si se instaló)
Get-Service SACMonitor

# Probar ejecución
cd C:\SAC
python main.py --verificar
```

### Registrar Equipo

```python
# Ejecutar desde Python
from modules.modulo_admin_config import AdministradorSAC, RolUsuario

admin = AdministradorSAC()
admin.registrar_equipo_actual(RolUsuario.ANALISTA)
```

O desde línea de comandos:
```batch
cd C:\SAC
python -c "from modules.modulo_admin_config import registrar_equipo_actual; registrar_equipo_actual('analista')"
```

### Configurar Credenciales (si no se incluyeron en .env)

```batch
cd C:\SAC
python instalar_sac.py --reinstalar
```

---

## Verificación y Troubleshooting

### Lista de Verificación Post-Instalación

| Componente | Comando de Verificación | Estado Esperado |
|------------|-------------------------|-----------------|
| Python | `python --version` | Python 3.8+ |
| Archivos SAC | `dir C:\SAC\*.py` | Múltiples archivos .py |
| Configuración | `type C:\SAC\.env` | Credenciales configuradas |
| Dependencias | `pip list` | pandas, openpyxl, etc. |
| Servicio | `sc query SACMonitor` | RUNNING (si aplica) |
| Conectividad DB | `python -c "from config import DB_CONFIG; print(DB_CONFIG)"` | Sin errores |

### Errores Comunes

#### Error: Python no encontrado
```
Solución: Instalar Python 3.8+ desde python.org
          O usar el instalador con -InstallPython
```

#### Error: Dependencias no instaladas
```powershell
cd C:\SAC
python -m pip install -r requirements.txt
```

#### Error: Servicio no inicia
```powershell
# Ver logs del servicio
Get-Content C:\SAC\output\logs\sac_service_*.log -Tail 100

# Verificar permisos
icacls C:\SAC /t

# Reiniciar servicio
Restart-Service SACMonitor
```

#### Error: Conexión a DB2 fallida
```
1. Verificar driver IBM DB2 ODBC instalado
2. Verificar credenciales en .env
3. Verificar conectividad de red a WM260BASD:50000
4. Verificar firewall no bloquea conexión
```

### Logs Importantes

| Log | Ubicación | Descripción |
|-----|-----------|-------------|
| Instalación | `%TEMP%\SAC_Install.log` | Log del instalador PowerShell |
| Servicio | `C:\SAC\output\logs\sac_service_*.log` | Log del servicio Windows |
| Aplicación | `C:\SAC\output\logs\sac_427.log` | Log principal de SAC |
| Auditoría | `C:\SAC\config\admin\audit_log.json` | Registro de accesos |

### Soporte

Para soporte técnico contactar:
- **Jefe de Sistemas**: Julián Alexander Juárez Alvarado (ADMJAJA)
- **Email**: sistemas_cedis427@chedraui.com.mx
- **Extensión**: [Tu extensión]

---

## Notas de Seguridad

1. **Credenciales**: El archivo `.env` contiene credenciales sensibles. Asegurar permisos apropiados.
2. **Servicio**: El servicio Windows se ejecuta bajo cuenta LOCAL SYSTEM por defecto.
3. **Red**: SAC solo requiere acceso a los servidores DB2 y SMTP especificados.
4. **Auditoría**: Todas las operaciones quedan registradas en `audit_log.json`.

---

**Versión del documento**: 2.0.0
**Última actualización**: Noviembre 2025
**Autor**: Julián Alexander Juárez Alvarado (ADMJAJA)
