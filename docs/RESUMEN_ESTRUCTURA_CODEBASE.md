# RESUMEN COMPLETO DE ESTRUCTURA DEL SISTEMA SAC
## Sistema de Automatización de Consultas - CEDIS Cancún 427

---

## 1. ARCHIVOS PRINCIPALES (ENTRY POINTS)

### 1.1 main.py (18KB)
**Propósito**: Punto de entrada principal del sistema

**Funcionalidades**:
- Interfaz CLI con argumentos (--oc, --reporte-diario, --validar-todas)
- Menú interactivo con 5+ opciones principales
- Integración de todos los módulos del sistema
- Configuración de logging
- Manejo de errores global

**Dependencias**:
- config.py (configuración centralizada)
- monitor.py (validaciones)
- modules/reportes_excel.py (reportes)
- modules/db_connection.py (conexión DB2)
- gestor_correos.py (envío de correos)
- notificaciones_telegram.py (alertas Telegram)
- queries/__init__.py (carga de queries)

**Funciones principales**:
- `configurar_logging()`: Configura el logging
- `menu_interactivo()`: Menú principal del sistema
- CLI con argparse para ejecución automática

---

### 1.2 monitor.py (29KB)
**Propósito**: Sistema de monitoreo y detección de errores en tiempo real

**Funcionalidades**:
- Clase `MonitorTiempoReal`: 15+ validaciones de OC, distribuciones y ASN
- Clase `ValidadorProactivo`: Validaciones preventivas
- Clase `ErrorSeverity`: Enum con 5 niveles (CRÍTICO, ALTO, MEDIO, BAJO, INFO)
- Dataclass `ErrorDetectado`: Estructura de errores
- Función `imprimir_resumen_errores()`: Formateo de reportes

**Validaciones principales**:
1. Conexión a DB2
2. Existencia de OC
3. Expiración de OC
4. Distribución excede OC (CRÍTICO)
5. Distribuciones incompletas
6. Sin distribuciones
7. SKU sin inner pack
8. ASN sin actualizar
9. Excel inválido
10. Columnas faltantes
11. Datos nulos
12. Prefijo 'C' en OC
13. Prefijo 'C' en distribuciones
14. Prefijo 'C' en ASN
15. Otras validaciones específicas

**Retorna**: Lista de `ErrorDetectado` con timestamp, severidad, detalles y soluciones

---

### 1.3 gestor_correos.py (31KB)
**Propósito**: Sistema de envío automático de correos

**Funcionalidades**:
- Clase `GestorCorreos`: Gestor de correos con 8 tipos
- Integración con sistema de templates profesionales
- Cola de envío con reintentos
- Programación de notificaciones
- Gestión de destinatarios por categoría

**Tipos de correos soportados**:
1. Reporte Planning Diario
2. Alerta Crítica
3. Validación OC
4. Programa de Recibo
5. Resumen Semanal
6. Notificación de Error
7. Recordatorio
8. Confirmación de Proceso

**Métodos principales**:
- `enviar_reporte_planning_diario()`
- `enviar_alerta_critica()`
- `enviar_validacion_oc()`
- `enviar_programa_recibo()`
- `_generar_tabla_html()`: Convierte DataFrame a HTML
- `_enviar_correo()`: Envío interno

**Dependencias internas**:
- `modules/email/EmailClient`
- `modules/email/EmailTemplateEngine`
- `modules/email/RecipientsManager`
- `modules/email/EmailQueue`

---

### 1.4 dashboard.py (Web UI)
**Propósito**: Dashboard web para visualización en tiempo real

**Funcionalidades**:
- Interfaz web con Flask
- Visualización de OCs y distribuciones
- Métricas en tiempo real
- Histórico de validaciones
- Alertas y errores
- Reportes interactivos

**URL**: http://localhost:5000

**Dependencias**:
- Flask para UI web
- modules/db_local.py para caché local
- Bootstrap 5 para estilo
- Chart.js para gráficos

---

### 1.5 examples.py (19KB)
**Propósito**: Ejemplos prácticos e interactivos

**Ejemplos incluidos**:
1. Monitor básico y validación de OC
2. Validación de distribuciones
3. Detección de errores
4. Generación de reportes Excel
5. Envío de notificaciones por email
6. Workflow completo

**Uso**: `python examples.py`

---

### 1.6 verificar_sistema.py (15KB)
**Propósito**: Script de verificación integral del sistema

**Verificaciones**:
- Estructura de carpetas
- Existencia de archivos
- Imports correctos
- Configuración válida
- Documentación completa
- Conexión a DB2
- Configuración de email

**Uso**: `python verificar_sistema.py`

---

## 2. CONFIGURACIÓN CENTRAL

### 2.1 config.py (12KB)
**Propósito**: Centralización de toda la configuración

**Secciones principales**:

#### Base de Datos DB2:
```python
DB_CONFIG = {
    'host': 'WM260BASD',
    'port': 50000,
    'database': 'WM260BASD',
    'user': 'ADMJAJA',  # Variable de entorno
    'password': '***',  # Variable de entorno
    'driver': '{IBM DB2 ODBC DRIVER}',
    'timeout': 30
}
```

#### Pool de Conexiones:
```python
DB_POOL_CONFIG = {
    'min_size': 1,
    'max_size': 5,
    'acquire_timeout': 30.0,
    'max_idle_time': 300.0,
    'health_check_interval': 60.0,
    'max_lifetime': 3600.0
}
```

#### CEDIS:
```python
CEDIS = {
    'code': '427',
    'name': 'CEDIS Cancún',
    'region': 'Sureste',
    'almacen': 'C22',
    'warehouse': 'WM260BASD'
}
```

#### Email (Office 365):
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.office365.com',
    'smtp_port': 587,
    'user': '***',  # Variable de entorno
    'password': '***',  # Variable de entorno
    'from_email': 'sac_cedis427@chedraui.com.mx',
    'from_name': 'Sistema SAC - CEDIS 427',
    'to_emails': ['planning@chedraui.com.mx'],
    'cc_emails': [],
    'enable_ssl': True
}
```

#### Telegram:
```python
TELEGRAM_CONFIG = {
    'bot_token': '***',  # Variable de entorno
    'chat_ids': [],  # Variable de entorno
    'enabled': True
}
```

#### Rutas:
```python
PATHS = {
    'base': BASE_DIR,
    'output': BASE_DIR / 'output',
    'logs': BASE_DIR / 'output' / 'logs',
    'resultados': BASE_DIR / 'output' / 'resultados',
    'queries': BASE_DIR / 'queries',
    'docs': BASE_DIR / 'docs',
    'config': BASE_DIR / 'config',
    'modules': BASE_DIR / 'modules',
    'tests': BASE_DIR / 'tests'
}
```

#### Logging:
```python
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'file': PATHS['logs'] / f"sac_427.log",
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}
```

---

## 3. MÓDULOS (modules/)

### 3.1 Módulos de Base de Datos

#### db_connection.py (43KB)
**Propósito**: Gestión de conexiones a IBM DB2

**Clases principales**:
- `DB2Connection`: Conexión con retry automático
- `DB2ConnectionPool`: Pool de conexiones
- `QueryResult`: Resultado de queries
- `ConnectionStats`: Estadísticas

**Enums**:
- `ConnectionDriver`: PYODBC, IBM_DB, AUTO
- `ConnectionStatus`: DISCONNECTED, CONNECTED, ERROR, CONNECTING

**Características**:
- Retry automático con backoff exponencial
- Connection pooling
- Context manager (`with` statement)
- Soporte para pyodbc e ibm_db
- Estadísticas de conexión
- Health check automático

**Métodos principales**:
- `connect()`: Establecer conexión
- `disconnect()`: Cerrar conexión
- `execute_query(sql, params)`: Ejecutar query
- `execute_many(sql, params_list)`: Batch execution
- `get_stats()`: Obtener estadísticas

#### db_pool.py (23KB)
**Propósito**: Pool de conexiones thread-safe

**Características**:
- Pool de conexiones reutilizables
- Timeout y max lifetime
- Health check automático
- Thread-safe
- Estadísticas de uso

#### db_local.py (31KB)
**Propósito**: Base de datos local SQLite para caché

**Funcionalidades**:
- Almacenamiento local de resultados
- Caché de queries
- Sincronización con DB2
- Datos offline

#### db_schema.py (22KB)
**Propósito**: Esquema de la base de datos

**Contenido**:
- Definición de tablas de Manhattan WMS
- Relaciones entre entidades
- Índices principales
- Vistas importantes

---

### 3.2 Módulos de Reportes

#### reportes_excel.py (53KB)
**Propósito**: Generación de reportes profesionales en Excel

**Clases principales**:
- `GeneradorReportesExcel`: Genera 10+ tipos de reportes

**Colores corporativos Chedraui**:
```python
COLOR_HEADER = "E31837"      # Rojo Chedraui
COLOR_SUBHEADER = "F8CBAD"   # Peach
COLOR_CRITICO = "FF0000"     # Rojo crítico
COLOR_ALERTA = "FFC000"      # Naranja
COLOR_OK = "92D050"          # Verde
COLOR_INFO = "B4C7E7"        # Azul
```

**Tipos de reportes**:
1. `crear_reporte_validacion_oc()`: OC vs Distribuciones
2. `crear_reporte_distribuciones()`: Detalle por tienda y SKU
3. `crear_reporte_planning_diario()`: Resumen ejecutivo
4. `crear_reporte_asn()`: Estado de ASNs
5. `crear_reporte_errores()`: Detalle de errores
6. Otros especializados

**Características**:
- Formato corporativo Chedraui
- Tablas dinámicas y gráficos
- Validaciones y resaltado de errores
- Exportación automática
- Encabezados y pie de página

#### excel_styles.py (22KB)
**Propósito**: Sistema de estilos para Excel

**Clases**:
- `ChedrauiStyles`: Estilos predefinidos
- `ChedrauiColors`: Paleta de colores corporativa
- Funciones de aplicación de estilos

#### chart_generator.py (19KB)
**Propósito**: Generador de gráficos Excel

**Tipos de gráficos**:
- Barras
- Líneas
- Pie
- Combinados

#### pivot_generator.py (19KB)
**Propósito**: Generador de tablas dinámicas

**Características**:
- Análisis pivot automático
- Agregación de datos
- Resúmenes multidimensionales

---

### 3.3 Módulos de Email

#### modules/email/email_client.py (22KB)
**Propósito**: Cliente SMTP mejorado

**Características**:
- Soporte para Office 365
- Reintentos automáticos
- Attachments
- HTML/plain text

#### modules/email/email_message.py (15KB)
**Propósito**: Estructura de mensajes

**Clases**:
- `EmailMessage`: Estructura de mensaje
- `EmailPriority`: Enum de prioridades

#### modules/email/template_engine.py (16KB)
**Propósito**: Motor de templates HTML

**Características**:
- Templates Jinja2
- Variables dinámicas
- Estilos corporativos

#### modules/email/queue.py (20KB)
**Propósito**: Cola de envío con reintentos

**Características**:
- Encolamiento de correos
- Reintentos automáticos
- Gestión de fallos

#### modules/email/recipients.py (24KB)
**Propósito**: Gestión de destinatarios

**Categorías**:
- Directores
- Analistas
- Supervisores
- Jefes de turno
- Etc.

#### modules/email/scheduler.py (21KB)
**Propósito**: Programación de notificaciones

**Características**:
- Envío programado
- Notificaciones periódicas
- Alertas automáticas

---

### 3.4 Módulos de Datos (Repositories)

#### repositories/base_repository.py (Base)
**Propósito**: Base para repositorios CRUD

**Operaciones**:
- `find_by_id()`
- `find_all()`
- `find_where()`
- `insert()`
- `update()`
- `delete()`

#### repositories/oc_repository.py
**Propósito**: Acceso a datos de Órdenes de Compra

#### repositories/asn_repository.py
**Propósito**: Acceso a datos de Advanced Ship Notices

#### repositories/distribution_repository.py
**Propósito**: Acceso a datos de Distribuciones

---

### 3.5 Módulos Especializados

#### query_builder.py (29KB)
**Propósito**: Constructor de queries SQL dinámicas

**Características**:
- Construcción segura de queries
- Parámetros preparados
- Validación de sintaxis

#### export_manager.py (18KB)
**Propósito**: Gestor de exportación de datos

**Formatos**:
- Excel
- CSV
- PDF
- JSON

#### exportar_pdf.py (21KB)
**Propósito**: Generación de reportes en PDF

#### modulo_cartones.py (21KB)
**Propósito**: Gestión de cartones/LPNs

#### modulo_lpn.py (18KB)
**Propósito**: Gestión de License Plate Numbers

#### modulo_ubicaciones.py (18KB)
**Propósito**: Gestión de ubicaciones en almacén

#### modulo_usuarios.py (17KB)
**Propósito**: Administración de usuarios

---

## 4. SISTEMA DE QUERIES

### 4.1 Estructura de Queries
```
queries/
├── obligatorias/          # 8 queries - Ejecución diaria
│   ├── asn_pendientes.sql
│   ├── asn_status.sql
│   ├── distribuciones_dia.sql
│   ├── inventario_resumen.sql
│   ├── oc_diarias.sql
│   ├── oc_pendientes.sql
│   ├── oc_vencidas.sql
│   └── recibo_programado.sql
│
├── preventivas/           # 8 queries - Validaciones proactivas
│   ├── asn_sin_actualizar.sql
│   ├── distribuciones_excedentes.sql
│   ├── distribuciones_incompletas.sql
│   ├── oc_por_vencer.sql
│   ├── sku_sin_innerpack.sql
│   ├── ubicaciones_llenas.sql
│   └── usuarios_inactivos.sql
│
├── bajo_demanda/          # 8 queries - Búsquedas específicas
│   ├── auditoria_usuario.sql
│   ├── buscar_asn.sql
│   ├── buscar_lpn.sql
│   ├── buscar_oc.sql
│   ├── buscar_sku.sql
│   ├── detalle_distribucion.sql
│   ├── historial_oc.sql
│   └── movimientos_lpn.sql
│
├── templates/             # Queries reutilizables
└── ddl/                   # Creación de vistas y procedures
```

### 4.2 Total de Queries: 28 SQL + templates

### 4.3 query_loader.py (Query Manager)
**Propósito**: Cargador y gestor de queries

**Clases**:
- `QueryLoader`: Carga y valida queries
- `QueryCategory`: Enum de categorías
- `QueryMetadata`: Metadatos de queries

**Características**:
- Caché de queries
- Sustitución de parámetros
- Validación de sintaxis
- Templates Jinja2

---

## 5. NOTIFICACIONES

### notificaciones_telegram.py (Telegram Bot)
**Propósito**: Envío de alertas instantáneas vía Telegram

**Clases**:
- `NotificadorTelegram`: Gestor de notificaciones
- `TipoAlerta`: Enum de tipos (CRÍTICO, ALTO, MEDIO, BAJO, INFO, ÉXITO)
- `MensajeTelegram`: Estructura de mensaje

**Métodos principales**:
- `enviar_alerta_critica()`
- `enviar_resumen_diario()`
- `enviar_notificacion_estado()`
- `enviar_archivo()`

### notificaciones_whatsapp.py (Opcional)
**Propósito**: Notificaciones WhatsApp

---

## 6. DEPENDENCIAS Y RELACIONES

```
main.py (orquestador principal)
  ├── config.py (configuración centralizada)
  ├── monitor.py (validaciones)
  │   └── ErrorDetectado, ErrorSeverity
  ├── modules/reportes_excel.py (reportes)
  │   ├── modules/excel_styles.py
  │   ├── modules/chart_generator.py
  │   └── modules/pivot_generator.py
  ├── modules/db_connection.py (conexión DB2)
  │   ├── modules/db_pool.py
  │   └── modules/query_builder.py
  ├── gestor_correos.py (email)
  │   └── modules/email/* (email infrastructure)
  ├── notificaciones_telegram.py (Telegram)
  ├── queries/query_loader.py (queries)
  │   └── queries/{obligatorias,preventivas,bajo_demanda}/
  └── dashboard.py (UI web)
      └── modules/db_local.py
```

---

## 7. FLUJOS PRINCIPALES

### 7.1 Flujo de Validación de OC
```
main.py
  ↓
validar_oc() → monitor.validar_oc_existente()
  ↓
monitor.validar_distribuciones()
  ↓
monitor.validar_asn()
  ↓
lista de ErrorDetectado
  ↓
si errores críticos → enviar alerta vía Telegram + Email
  ↓
generar reporte Excel
  ↓
guardar en output/resultados/
```

### 7.2 Flujo de Reporte Diario
```
main.py --reporte-diario
  ↓
query_loader.load_query('oc_diarias')
  ↓
db_connection.execute_query()
  ↓
reportes_excel.crear_reporte_planning_diario()
  ↓
gestor_correos.enviar_reporte_planning_diario()
  ↓
notificaciones_telegram.enviar_resumen_diario()
```

### 7.3 Flujo de Monitoreo Continuo (monitor.py)
```
monitor.py (ejecución continua)
  ↓
cada N segundos/minutos
  ↓
ejecutar queries obligatorias
  ↓
ejecutar queries preventivas
  ↓
buscar errores críticos
  ↓
si encontrados → alertar vía Telegram + Email inmediato
  ↓
generar reporte de situación
```

---

## 8. PROCESOS Y EJECUCIÓN

### 8.1 Ejecución Manual
```bash
# Menú interactivo
python main.py

# Validar OC específica
python main.py --oc OC12345

# Generar reporte diario
python main.py --reporte-diario

# Validar múltiples OCs
python main.py --validar-todas

# Ver ejemplos
python examples.py

# Verificar sistema
python verificar_sistema.py

# Dashboard web
python dashboard.py
```

### 8.2 Ejecución Programada (Sugerencia para Script Maestro)
```
DIARIO:
- 06:00 AM: Reporte Planning Diario
- 12:00 PM: Validación de OCs pendientes
- 06:00 PM: Resumen del día
- 11:00 PM: Backup de datos

EN TIEMPO REAL:
- Monitoreo continuo de errores críticos
- Alertas instantáneas vía Telegram
- Dashboard actualizado

CADA 15 MINUTOS:
- Chequeo de queries preventivas
- Búsqueda de discrepancias

CADA HORA:
- Sincronización de caché local
```

---

## 9. ARCHIVOS IMPORTANTES NO MENCIONADOS

### env (Template de variables de entorno)
Contiene template de todas las variables necesarias.

### .env (No versionado - Crear localmente)
Copiar de `env` y llenar credenciales reales:
- DB_USER
- DB_PASSWORD
- EMAIL_USER
- EMAIL_PASSWORD
- TELEGRAM_BOT_TOKEN

### requirements.txt
Todas las dependencias Python necesarias

### .gitignore
Protege archivos sensibles como .env

### docs/
- QUICK_START.md
- FUNCIONALIDADES_COMPLETAS.md
- NUEVAS_FUNCIONALIDADES.md
- RESUMEN_PROYECTO.md
- LICENCIA.md

---

## 10. CONCLUSIONES PARA SCRIPT MAESTRO

### Qué debe hacer el script maestro:

1. **Inicialización**:
   - Validar configuración (verificar_sistema.py)
   - Establecer conexión a DB2
   - Inicializar logging

2. **Procesos Diarios** (Ejecutar en horarios específicos):
   - 06:00 AM: Reporte Planning Diario
   - 12:00 PM: Validación OCs pendientes
   - 06:00 PM: Resumen y alertas
   - 11:00 PM: Limpieza y backup

3. **Monitoreo Continuo** (24/7):
   - Ejecutar monitor.py en background
   - Chequear errores cada 15 minutos
   - Enviar alertas inmediatas

4. **Manejo de Errores**:
   - Reintentos automáticos
   - Logs detallados
   - Alertas sobre fallos críticos

5. **Reportes y Notificaciones**:
   - Email con Excel adjuntos
   - Alertas Telegram inmediatas
   - Dashboard web actualizado

---

## 11. DEPENDENCIAS CLAVE

```python
# Base de datos
ibm_db
ibm_db_dbi
pyodbc

# Web y CLI
flask
click
argparse

# Datos
pandas
numpy
openpyxl

# Email
email
smtplib

# Utilidades
python-dotenv
requests  # Telegram
jinja2    # Templates
```

---

