# 🚀 GUÍA DE PRODUCCIÓN - SAC v1.0

## Checklist de Producción Completo

Sistema de Automatización de Consultas - CEDIS Cancún 427
Tiendas Chedraui S.A. de C.V.

---

## ✅ PRE-REQUISITOS

### 1. Python e Instalación
- [x] Python 3.8+ instalado
- [x] pip actualizado
- [x] virtualenv (recomendado)

**Verificar:**
```bash
python --version          # Debe ser 3.8+
pip --version             # Actualizar si es necesario
```

---

## 🔧 SETUP INICIAL (PRIMERA VEZ)

### PASO 1: Clonar el Repositorio
```bash
git clone https://github.com/sistemascancunjefe-ai/SAC_V01_427_ADMJAJA.git
cd SAC_V01_427_ADMJAJA
```

### PASO 2: Crear Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### PASO 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### PASO 4: Configurar Variables de Entorno
```bash
# Ejecutar setup seguro de credenciales
python setup_env_seguro.py
```

Este script solicitará:
- Usuario y contraseña de DB2
- Correo corporativo y contraseña
- Configuración opcional de Telegram/WhatsApp

**Resultado:** Se crea archivo `.env` con permisos 600 (lectura solo para usuario)

### PASO 5: Ejecutar Health Check
```bash
python health_check.py --detailed
```

Verifica:
- ✅ Python version
- ✅ Dependencias instaladas
- ✅ Archivo .env y permisos
- ✅ Directorios necesarios
- ✅ Configuración válida
- ✅ .gitignore correcto

**Salida:** "✅ LISTO PARA PRODUCCIÓN"

---

## 🚀 INICIANDO PRODUCCIÓN

### Opción 1: Startup Automático (Recomendado)
```bash
python production_startup.py
```

Realiza:
- ✅ Verificación de Python
- ✅ Carga de configuración
- ✅ Preparación de directorios
- ✅ Inicialización de logging
- ✅ Validación de dependencias
- ✅ Mostrar información del sistema

### Opción 2: Solo Verificaciones
```bash
python production_startup.py --check
```

Ejecuta solo los checks sin iniciar servicios.

### Opción 3: Con Monitoreo en Tiempo Real
```bash
python production_startup.py --monitor
```

Inicia el sistema con monitoreo continuo activo.

---

## 📋 FLUJOS DE OPERACIÓN

### Flujo 1: Menú Interactivo (Estándar)
```bash
python main.py
```

Presenta menú con opciones:
1. Validar Orden de Compra (OC)
2. Generar Reporte Diario
3. Enviar Alerta Crítica
4. Validar Múltiples OCs
5. Programa de Recibo
6. Ver Logs
7. Salir

### Flujo 2: Operación Específica desde CLI
```bash
# Validar una OC específica
python main.py --oc OC123456789

# Generar reporte diario
python main.py --reporte-diario

# Ver menú explícitamente
python main.py --menu
```

### Flujo 3: Ejecución de Ejemplos
```bash
python examples.py
```

Demuestra 6 escenarios completos del sistema.

### Flujo 4: Monitoreo Continuo
```bash
python monitor.py
```

Inicia monitoreo en tiempo real con detección proactiva de errores.

---

## 🔒 SEGURIDAD EN PRODUCCIÓN

### ✅ Medidas Implementadas

1. **Credenciales Seguras**
   - Variables de entorno en `.env`
   - Archivo `.env` ignorado en Git
   - Permisos restrictivos (600)
   - Setup interactivo sin exposición de contraseñas

2. **Encriptación**
   - Credenciales en memoria solo mientras se usan
   - Conexión SMTP/IMAP con TLS
   - Soporte para JWT tokens en APIs

3. **Auditoría**
   - Logging completo de operaciones
   - Archivos de log en `output/logs/`
   - Rotación automática (5 archivos de 10MB)

4. **Control de Acceso**
   - Validación de usuarios
   - Roles y permisos (framework preparado)

### 🔐 Checklist de Seguridad

```
[ ] .env existe y tiene permisos 600
[ ] .env NO está en Git (en .gitignore)
[ ] Credenciales NO hardcodeadas en código
[ ] SMTP usa TLS (puerto 587)
[ ] Logs no contienen credenciales sensibles
[ ] Backups encriptados (recomendado)
[ ] Acceso a BD restringido por usuario/IP
[ ] Email configurado solo para destinatarios autorizados
```

---

## 📊 MONITOREO Y LOGS

### Ubicación de Logs
```
output/logs/
├── sac_427.log                    # Log principal
├── sac_production_YYYYMMDD.log   # Log de producción
└── health_check_YYYYMMDD_HHMMSS.json
```

### Ver Logs en Tiempo Real
```bash
# Linux/Mac
tail -f output/logs/sac_427.log

# Windows PowerShell
Get-Content output/logs/sac_427.log -Wait -Tail 20
```

### Niveles de Log
- `DEBUG` - Información detallada
- `INFO` - Operaciones normales ✅
- `WARNING` - Advertencias ⚠️
- `ERROR` - Errores ❌
- `CRITICAL` - Errores críticos 🚨

### Configurar Nivel de Log
```bash
# En .env
LOG_LEVEL=INFO              # Cambiar a DEBUG, WARNING, etc.
```

---

## 🔄 OPERACIONES DIARIAS

### Inicio del Día
```bash
# 1. Ejecutar startup
python production_startup.py

# 2. Si todo OK, iniciar monitoreo
python production_startup.py --monitor
```

### Durante el Día
```bash
# Validar OC
python main.py --oc OC123456789

# Generar reporte
python main.py --reporte-diario

# Ver estado
tail -f output/logs/sac_427.log
```

### Fin del Día
```bash
# Generar reporte final
python main.py --reporte-diario

# Revisar logs de errores
grep ERROR output/logs/sac_427.log

# Backup de resultados (recomendado)
cp -r output/resultados output/backups/$(date +%Y%m%d)
```

---

## 📧 NOTIFICACIONES AUTOMÁTICAS

### Email
- **Reporte diario**: 7:00 AM (configurable)
- **Alertas críticas**: Inmediatas
- **Resumen semanal**: Viernes 5:00 PM

### Telegram (Si configurado)
- Alertas críticas
- Resumen diario
- Notificaciones de errores

### WhatsApp (Si configurado)
- Alertas críticas urgentes
- Confirmaciones de proceso

### Configurar Notificaciones
```bash
# En .env
EMAIL_TO=planning@chedraui.com.mx
EMAIL_CC=supervisor@chedraui.com.mx

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_IDS=123456789

WHATSAPP_ENABLED=true
WHATSAPP_API_TOKEN=tu_token
```

---

## 🐛 RESOLUCIÓN DE PROBLEMAS

### Problema: "ModuleNotFoundError: No module named 'config'"
**Solución:**
```bash
# Verificar que estás en la carpeta correcta
cd SAC_V01_427_ADMJAJA

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema: "Error de credenciales"
**Solución:**
```bash
# Ejecutar setup nuevamente
python setup_env_seguro.py

# Verificar que .env existe
ls -la .env

# Verificar permisos
stat .env  # Debe mostrar 600
```

### Problema: "No se puede conectar a BD"
**Solución:**
```bash
# Verificar datos de BD en .env
grep DB_ .env

# Verificar que DB está disponible
# Contactar a administrador de BD

# Mientras tanto, usar modo demo
python main.py --demo
```

### Problema: "Error enviando emails"
**Solución:**
```bash
# Verificar credenciales de email
python health_check.py --detailed

# Verificar que tienes conexión a Internet
ping smtp.office365.com

# Deshabilitar email temporalmente
# En .env: ENABLE_EMAIL=false
```

### Problema: Los logs no se crean
**Solución:**
```bash
# Verificar permisos en output/
chmod -R 755 output/

# Ejecutar health_check --fix
python health_check.py --fix

# Crear directorios manualmente
mkdir -p output/logs
mkdir -p output/resultados
```

---

## 📈 ESCALAR A MAYOR CAPACIDAD

### Para Múltiples OCs Simultáneamente
```python
from main import validar_multiples_ocs

ocas = ['OC123456789', 'OC987654321', ...]
resultados = validar_multiples_ocs(ocas)
```

### Para Procesamiento Batch
```python
# En .env
BATCH_MODE=true
BATCH_SIZE=100
```

### Para Alta Concurrencia
```bash
# Aumentar pool de conexiones en .env
DB_POOL_SIZE=10
DB_POOL_MAX_SIZE=20

# Aumentar timeouts
DB_TIMEOUT=60
```

---

## 🧹 MANTENIMIENTO REGULAR

### Limpieza Semanal
```bash
# Limpiar archivos temporales
rm -rf __pycache__
find . -name "*.pyc" -delete

# Rotación de logs (automática pero verifica)
ls -lh output/logs/
```

### Limpieza Mensual
```bash
# Archivar reportes antiguos
mkdir -p output/archivos/$(date +%Y%m)
mv output/resultados/*.xlsx output/archivos/$(date +%Y%m)/

# Limpiar cache
rm -rf .pytest_cache
```

### Actualización de Dependencias
```bash
# Ver actualizaciones disponibles
pip list --outdated

# Actualizar (con cuidado en producción)
pip install -U pandas openpyxl pytest --dry-run
```

---

## 📞 CONTACTO Y SOPORTE

**CEDIS Cancún 427 - Tiendas Chedraui**

**Equipo de Sistemas:**
- Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Díaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas

**Supervisor Regional:**
- Itza Vera Reyes Sarubí (Villahermosa)

**Para reportar problemas:**
1. Generar health check: `python health_check.py --detailed > report.txt`
2. Enviar a: sistemas427@chedraui.com.mx
3. Incluir: Descripción del problema, timestamp del error, logs relevantes

---

## 📚 DOCUMENTACIÓN ADICIONAL

- `CLAUDE.md` - Guía para desarrolladores IA
- `README.md` - Documentación principal
- `docs/` - Documentación completa del proyecto
- `config/README.md` - Detalles de configuración

---

## ✅ CHECKLIST FINAL DE PRODUCCIÓN

```
Antes de poner en producción, verificar:

[ ] Python 3.8+ instalado
[ ] Todas las dependencias instaladas (pip install -r requirements.txt)
[ ] Archivo .env configurado y con permisos 600
[ ] health_check.py pasa todos los checks
[ ] production_startup.py ejecuta exitosamente
[ ] Logs se crean correctamente
[ ] Se pueden validar OCs (con datos de prueba si es necesario)
[ ] Emails se envían correctamente
[ ] Monitoreo detecta errores
[ ] Reportes Excel se generan correctamente
[ ] .gitignore contiene .env
[ ] No hay credenciales en código
[ ] Documentación está actualizada
[ ] Equipo capacitado en operación
```

---

## 🎉 ¡LISTO PARA PRODUCCIÓN!

Una vez completados todos los pasos:

```bash
# Iniciar sistema
python production_startup.py

# O si todo está bien
python main.py
```

Sistema SAC v1.0 está listo para servir.

**¡Buena suerte!**

---

**Última actualización:** 22 de Noviembre, 2025
**Autor:** Julián Alexander Juárez Alvarado (ADMJAJA)
**Sistema:** SAC v1.0 - CEDIS Cancún 427
