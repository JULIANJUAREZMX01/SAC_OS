# ANÁLISIS EXHAUSTIVO DEL SISTEMA SAC v1.0.0
## Sistema de Automatización de Consultas - CEDIS Cancún 427

**Fecha del Análisis:** 21 de Noviembre de 2025  
**Desarrollador Lead:** Julián Alexander Juárez Alvarado (ADMJAJA)  
**Organización:** Tiendas Chedraui S.A. de C.V. - CEDIS Logística Cancún  
**Región:** Sureste  

---

## EXECUTIVE SUMMARY

El Sistema SAC es una solución empresarial completa de automatización que integra:

- **Validación automática** de Órdenes de Compra contra distribuciones en Manhattan WMS
- **Monitoreo proactivo** con detección de 15+ tipos de errores en tiempo real
- **Generación de reportes** profesionales en Excel con formato corporativo Chedraui
- **Sistema de notificaciones multi-canal** (Email, Telegram, WhatsApp)
- **Orquestación automática** de tareas mediante modo daemon con scheduling configurable

**Objetivo:** Reducir errores en la cadena de suministro, acelerar procesos de validación y proporcionar visibilidad en tiempo real de la operación.

---

# 1. FLUJO PRINCIPAL DE OPERACIONES

## 1.1 PUNTOS DE ENTRADA DEL SISTEMA

### A) MAIN.PY (1,009 líneas) - Interfaz Principal Interactiva
**Ubicación:** `/home/user/SAC_V01_427_ADMJAJA/main.py`

**Modos de Ejecución:**
```bash
# Menú interactivo (predeterminado)
python main.py

# Validar OC específica
python main.py --oc OC12345

# Generar reporte diario
python main.py --reporte-diario

# Menú interactivo explícito
python main.py --menu
```

**Funciones Principales:**
1. `menu_interactivo()` - Menú interactivo con 10 opciones
2. `conectar_db()` - Establece conexión a DB2 con retry automático
3. `validar_orden_compra()` - Valida OC completa (4 pasos)
4. `generar_reporte_diario()` - Genera y envía reporte Planning
5. `consultar_oc_desde_db()` - Consulta datos reales de DB2
6. `consultar_distribuciones_desde_db()` - Consulta distribuciones
7. `consultar_oc_diarias()` - Obtiene OC del día
8. `consultar_asn_status()` - Obtiene estado de ASN

### B) MAESTRO.PY (1,141 líneas) - Orquestador Central
**Ubicación:** `/home/user/SAC_V01_427_ADMJAJA/maestro.py`

**Clase Principal:** `MaestroSAC`

**Modos de Ejecución:**
```bash
# Menú interactivo
python maestro.py

# Modo daemon (servicio continuo)
python maestro.py --daemon

# Ejecutar ciclo completo ahora
python maestro.py --ejecutar-ahora

# Validar OC específica
python maestro.py --validar OC12345

# Generar reporte diario
python maestro.py --reporte-diario

# Ver estado del sistema
python maestro.py --status

# Ver configuración
python maestro.py --config
```

**Métodos de Ejecución Principales:**
- `inicializar()` - Inicializa conexiones (DB2, Email, Telegram)
- `ejecutar_ciclo_completo()` - Ejecuta secuencia completa de 4 tareas
- `ejecutar_validacion_oc()` - Valida OC individual
- `ejecutar_reporte_diario()` - Genera reporte diario
- `ejecutar_monitoreo()` - Monitoreo en tiempo real
- `ejecutar_validacion_preventiva()` - Validaciones preventivas
- `ejecutar_resumen_dia()` - Genera resumen diario
- `iniciar_daemon()` - Inicia modo servicio continuo

---

## 1.2 FLUJO DE VALIDACIÓN DE ORDEN DE COMPRA (OC)

```
VALIDAR ORDEN DE COMPRA
│
├─ ENTRADA: Número de OC
│
├─ PASO 1: Validar conexión DB2
│  ├─ ¿Conexión activa?
│  └─ Si CRÍTICO → Abortar validación
│
├─ PASO 2: Consultar datos de OC desde DB2
│  ├─ Query: buscar_oc (bajo_demanda)
│  ├─ Parámetros: oc_numero, storerkey (C22)
│  └─ Retorna: DataFrame con datos OC
│
├─ PASO 3: Validar datos de OC
│  ├─ ¿OC existe?
│  ├─ ¿OC está vencida?
│  ├─ ¿OC tiene letra 'C' en ID_CODE?
│  └─ Genera lista de errores por severidad
│
├─ PASO 4: Consultar y validar distribuciones
│  ├─ Query: detalle_distribucion (bajo_demanda)
│  ├─ Validaciones:
│  │  ├─ ¿Sin distribuciones? (CRÍTICO)
│  │  ├─ ¿Distribución excedente? (CRÍTICO)
│  │  ├─ ¿Distribución incompleta? (ALTO)
│  │  └─ ¿SKUs sin Inner Pack? (MEDIO)
│  └─ Suma totales y compara
│
├─ PASO 5: Consolidar errores y determinar severidad
│  ├─ Agrupar por: CRÍTICO, ALTO, MEDIO, BAJO, INFO
│  └─ ¿Hay errores CRÍTICOS?
│
├─ PASO 6: Generar Reporte Excel
│  ├─ Crear archivo: Validacion_OC_{OC}_{TIMESTAMP}.xlsx
│  ├─ Incluir:
│  │  ├─ Encabezado corporativo Chedraui
│  │  ├─ Datos de validación
│  │  ├─ Listado de errores por severidad
│  │  └─ Estadísticas de validación
│  └─ Guardar en: output/resultados/
│
├─ PASO 7: Enviar alertas (si hay CRÍTICOS)
│  ├─ Email a destinatarios configurados
│  └─ Telegram a chat_ids configurados
│
└─ SALIDA:
   ├─ bool: es_válida
   ├─ List[ErrorDetectado]: errores
   └─ archivo_excel: Ruta del reporte
```

---

## 1.3 FLUJO DE GENERACIÓN DE REPORTE DIARIO

```
GENERAR REPORTE PLANNING DIARIO
│
├─ ENTRADA: Fecha (default: hoy)
│
├─ PASO 1: Consultar OC del día
│  ├─ Query: oc_diarias (obligatorias)
│  ├─ Parámetros: fecha_inicio, fecha_fin, storerkey
│  ├─ Retorna: DataFrame con todas las OC del día
│  └─ Campos: oc_numero, status, proveedor, cantidades
│
├─ PASO 2: Consultar status de ASN
│  ├─ Query: asn_status (obligatorias)
│  ├─ Parámetros: fecha_inicio, fecha_fin, storerkey
│  ├─ Retorna: DataFrame con ASN actualizado
│  └─ Campos: ASN, OC, status, ETA
│
├─ PASO 3: Ejecutar validaciones preventivas
│  ├─ Detectar OC vencidas
│  ├─ Detectar distribuciones incompletas
│  ├─ Detectar ASN no actualizados
│  └─ Generar DataFrame de errores
│
├─ PASO 4: Generar reporte Excel
│  ├─ Archivo: Planning_Diario_{CEDIS}_{YYYYMMDD}.xlsx
│  ├─ Hojas:
│  │  ├─ Resumen: Estadísticas del día
│  │  ├─ OC: Listado de órdenes de compra
│  │  ├─ ASN: Status de llegadas
│  │  └─ Errores: Problemas detectados
│  └─ Formato: Colores Chedraui, gráficos, tablas dinámicas
│
├─ PASO 5: Enviar por email
│  ├─ Destinatarios: EMAIL_CONFIG.to_emails
│  ├─ CC: EMAIL_CONFIG.cc_emails
│  ├─ Asunto: [CEDIS {codigo}] Reporte Planning Diario {fecha}
│  ├─ Cuerpo HTML: Template profesional
│  └─ Adjunto: Excel con reporte
│
├─ PASO 6: Notificar por Telegram
│  ├─ Mensaje: Resumen de OC y ASN
│  └─ Destinatarios: TELEGRAM_CONFIG.chat_ids
│
└─ SALIDA:
   ├─ archivo_excel: Ruta del reporte
   ├─ email_enviado: bool
   └─ telegram_notificado: bool
```

---

## 1.4 FLUJO DE MONITOREO EN TIEMPO REAL

```
MONITOREO CONTINUO (CADA 15 MINUTOS - MODO DAEMON)
│
├─ PASO 1: Validar conexión a DB2
│  ├─ Query de prueba: SELECT 1 FROM SYSIBM.SYSDUMMY1
│  └─ Detectar: CONEXION_DB, QUERY_TEST_FAILED
│
├─ PASO 2: Verificar OC pendientes (si DB conectada)
│  ├─ Cargar queries preventivas
│  └─ Ejecutar y detectar anomalías
│
├─ PASO 3: Detectar errores
│  ├─ Por tipo: 15+ tipos de validación
│  ├─ Por severidad: CRÍTICO, ALTO, MEDIO, BAJO, INFO
│  └─ Registro en: self._errores_detectados
│
├─ PASO 4: Procesar alertas críticas
│  ├─ Si hay CRÍTICOS:
│  │  ├─ Enviar alerta por Email
│  │  ├─ Enviar alerta por Telegram
│  │  └─ Log en archivo de monitoreo
│  └─ Registrar en estadísticas
│
├─ PASO 5: Actualizar estado del sistema
│  └─ Campos actualizados:
│     ├─ ultimo_ciclo: datetime
│     ├─ errores_pendientes: count
│     └─ alertas_enviadas_hoy: count
│
└─ SALIDA:
   ├─ errores_detectados: List[ErrorDetectado]
   ├─ alertas_criticas_enviadas: bool
   └─ duracion: float (segundos)
```

---

## 1.5 CICLO COMPLETO DE EJECUCIÓN (MAESTRO)

```
EJECUTAR CICLO COMPLETO
│
├─ PASO 1: MONITOREO (5 min)
│  └─ Detectar problemas iniciales
│
├─ PASO 2: VALIDACIÓN PREVENTIVA (10 min)
│  ├─ Ejecutar queries de categoría 'preventivas'
│  └─ Identificar OC en riesgo
│
├─ PASO 3: REPORTE DIARIO (15 min)
│  ├─ Generar Excel con datos del día
│  └─ Enviar por email y Telegram
│
├─ PASO 4: RESUMEN DEL DÍA (5 min)
│  ├─ Compilar estadísticas del ciclo
│  └─ Enviar resumen por Telegram
│
└─ TOTAL: ~35 minutos por ciclo completo
```

---

## 1.6 MODO DAEMON - HORARIOS PROGRAMADOS

```
06:00 → REPORTE MATUTINO
        ├─ ejecutar_monitoreo()
        └─ ejecutar_reporte_diario()

09:00 → VALIDACIÓN DE OC PENDIENTES
        └─ ejecutar_validacion_preventiva()

12:00 → MONITOREO DE MEDIO DÍA
        └─ ejecutar_monitoreo()

15:00 → VALIDACIÓN PREVENTIVA
        └─ ejecutar_validacion_preventiva()

18:00 → REPORTE VESPERTINO
        └─ ejecutar_reporte_diario()

21:00 → RESUMEN DEL DÍA
        └─ ejecutar_resumen_dia()

CADA 15 MIN → MONITOREO CONTINUO
              └─ ejecutar_monitoreo()

00:00 → RESET DIARIO
        └─ Limpiar contadores: tareas, alertas, errores
```

---

# 2. MÓDULOS Y SUS RESPONSABILIDADES

## 2.1 ESTRUCTURA DE MÓDULOS

```
SAC_V01_427_ADMJAJA/
│
├── config.py (304 líneas)
│   └─ Configuración centralizada de todo el sistema
│      ├─ DB_CONFIG: Credenciales y conexión DB2
│      ├─ CEDIS: Información del centro de distribución
│      ├─ EMAIL_CONFIG: Configuración SMTP
│      ├─ TELEGRAM_CONFIG: Token y chat IDs
│      ├─ SYSTEM_CONFIG: Versión, ambiente, debug
│      ├─ PATHS: Rutas de directorios
│      └─ Validación y visualización de configuración
│
├── monitor.py (935 líneas)
│   ├─ MonitorTiempoReal (detección de errores)
│   │  ├─ validar_conexion_db()
│   │  ├─ validar_oc_existente()
│   │  ├─ validar_distribuciones()
│   │  ├─ validar_asn_status()
│   │  ├─ validar_datos_excel()
│   │  └─ generar_reporte_errores()
│   │
│   ├─ ValidadorProactivo
│   │  └─ validacion_completa_oc()
│   │
│   └─ ValidadorAvanzado (10+ validaciones)
│      ├─ validar_secuencia_oc()
│      ├─ validar_proveedor_activo()
│      ├─ validar_tienda_activa()
│      ├─ validar_ruta_entrega()
│      ├─ validar_capacidad_almacen()
│      ├─ validar_horario_recibo()
│      ├─ validar_documentacion_completa()
│      ├─ validar_aprobaciones()
│      ├─ validar_presupuesto()
│      └─ validar_prioridad()
│
├── modules/
│   │
│   ├─ db_connection.py (varies)
│   │  ├─ DB2Connection: Conexión simple a DB2
│   │  │  ├─ connect(): Establece conexión con retry
│   │  │  ├─ execute_query(): Ejecuta SQL y retorna DataFrame
│   │  │  └─ disconnect(): Cierra conexión
│   │  │
│   │  └─ DB2ConnectionPool: Pool de conexiones reutilizables
│   │     ├─ get_connection(): Obtiene conexión del pool
│   │     ├─ return_connection(): Devuelve conexión
│   │     └─ close_all(): Cierra todas las conexiones
│   │
│   ├─ reportes_excel.py (varies)
│   │  └─ GeneradorReportesExcel
│   │     ├─ crear_reporte_validacion_oc()
│   │     ├─ crear_reporte_distribuciones()
│   │     ├─ crear_reporte_planning_diario()
│   │     ├─ crear_reporte_errores()
│   │     ├─ _agregar_encabezado(): Formato corporativo
│   │     ├─ _formatear_tabla(): Estilos y colores
│   │     └─ _ajustar_columnas(): Auto-width
│   │
│   ├─ excel_styles.py
│   │  └─ Estilos corporativos Chedraui
│   │     ├─ ChedrauiStyles
│   │     ├─ ChedrauiColors
│   │     └─ apply_style_dict()
│   │
│   ├─ chart_generator.py
│   │  └─ ChartGenerator: Generador de gráficos
│   │     ├─ generar_grafico_barras()
│   │     ├─ generar_grafico_pie()
│   │     └─ generar_grafico_linea()
│   │
│   ├─ pivot_generator.py
│   │  └─ PivotGenerator: Tablas dinámicas
│   │     ├─ crear_pivot_tiendas()
│   │     └─ crear_pivot_sku()
│   │
│   ├─ email/
│   │  ├─ email_client.py: Cliente SMTP
│   │  ├─ template_engine.py: Templates Jinja2
│   │  ├─ queue.py: Cola de envío con reintentos
│   │  ├─ scheduler.py: Programación de emails
│   │  └─ recipients.py: Gestión de destinatarios
│   │
│   ├─ repositories/
│   │  ├─ oc_repository.py: Acceso a datos de OC
│   │  ├─ distribution_repository.py: Acceso a distribuciones
│   │  ├─ asn_repository.py: Acceso a ASN
│   │  └─ base_repository.py: Clase base
│   │
│   └─ validators/
│      ├─ oc_validator.py
│      ├─ distribution_validator.py
│      ├─ asn_validator.py
│      ├─ lpn_validator.py
│      ├─ sku_validator.py
│      └─ base_validator.py
│
├── gestor_correos.py (476 líneas)
│   └─ GestorCorreos: Gestor automático de emails
│      ├─ enviar_reporte_planning_diario()
│      ├─ enviar_alerta_critica()
│      ├─ enviar_validacion_oc()
│      ├─ enviar_programa_recibo()
│      ├─ enviar_resumen_semanal()
│      ├─ enviar_notificacion_error()
│      ├─ enviar_recordatorio()
│      └─ enviar_confirmacion_proceso()
│
├── notificaciones_telegram.py (920 líneas)
│   ├─ RateLimiter: Control de límites de API
│   ├─ TipoAlerta (Enum): CRITICO, ALTO, MEDIO, BAJO, INFO
│   └─ NotificadorTelegram
│      ├─ enviar_alerta()
│      ├─ enviar_alerta_critica()
│      ├─ enviar_estado_sistema()
│      ├─ enviar_resumen_diario()
│      └─ enviar_documento()
│
├── queries/
│   ├─ query_loader.py: Cargador de queries SQL
│   │  ├─ QueryCategory (Enum): OBLIGATORIAS, PREVENTIVAS, BAJO_DEMANDA, TEMPLATES, DDL
│   │  ├─ QueryLoader: Carga y valida queries
│   │  └─ load_query(), load_query_with_params()
│   │
│   ├─ obligatorias/ (8 queries)
│   │  ├─ oc_diarias.sql: OC del día
│   │  ├─ oc_pendientes.sql: OC sin completar
│   │  ├─ oc_vencidas.sql: OC vencidas
│   │  ├─ asn_status.sql: Status de ASN
│   │  ├─ asn_pendientes.sql: ASN sin recibir
│   │  ├─ distribuciones_dia.sql: Distribuciones del día
│   │  ├─ inventario_resumen.sql: Inventario actual
│   │  └─ recibo_programado.sql: Programación de recibos
│   │
│   ├─ preventivas/
│   │  └─ (Queries para validaciones proactivas)
│   │
│   ├─ bajo_demanda/ (6 queries)
│   │  ├─ buscar_oc.sql: Buscar OC específica
│   │  ├─ buscar_asn.sql: Buscar ASN
│   │  ├─ buscar_lpn.sql: Buscar LPN
│   │  ├─ buscar_sku.sql: Buscar SKU
│   │  ├─ detalle_distribucion.sql: Distribuciones de OC
│   │  ├─ historial_oc.sql: Historial de OC
│   │  └─ movimientos_lpn.sql: Movimientos de LPN
│   │
│   └─ ddl/
│      ├─ views/: Vistas SQL
│      │  ├─ v_oc_summary.sql
│      │  ├─ v_asn_status.sql
│      │  └─ v_distribution_totals.sql
│      └─ procedures/: Procedimientos almacenados
│         ├─ sp_validate_oc.sql
│         └─ sp_get_daily_report.sql
│
├── main.py (1,009 líneas)
│   └─ Interfaz interactiva CLI
│      ├─ menu_interactivo()
│      ├─ validar_orden_compra()
│      ├─ generar_reporte_diario()
│      └─ Modos: --oc, --reporte-diario, --menu
│
└── maestro.py (1,141 líneas)
   └─ Orquestador central
      ├─ MaestroSAC: Clase principal
      ├─ inicializar()
      ├─ ejecutar_ciclo_completo()
      ├─ iniciar_daemon()
      └─ Modos: --daemon, --ejecutar-ahora, --validar, --status
```

---

## 2.2 RELACIONES ENTRE MÓDULOS

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN.PY / MAESTRO.PY                     │
│                    (Orquestación)                           │
└─────────────────────────────────────────────────────────────┘
            ↓
    ┌───────────────────┐
    │   config.py       │ ← Configuración centralizada
    └───────────────────┘

    ┌───────────────────────────────────────────────────────┐
    │         CAPA DE DATOS - DB2 CONNECTION               │
    │  modules/db_connection.py (DB2Connection/Pool)       │
    └───────────────────────────────────────────────────────┘
            ↓
    ┌───────────────────────────────────────────────────────┐
    │              QUERIES (queries/)                        │
    │  ├─ obligatorias/ (ejecución diaria)                 │
    │  ├─ preventivas/ (validaciones)                      │
    │  └─ bajo_demanda/ (búsquedas puntuales)             │
    └───────────────────────────────────────────────────────┘
            ↓
    ┌───────────────────────────────────────────────────────┐
    │      CAPA DE LÓGICA - VALIDACIÓN Y MONITOREO        │
    │  monitor.py:                                          │
    │  ├─ MonitorTiempoReal (detección de errores)         │
    │  ├─ ValidadorProactivo (validación completa)         │
    │  └─ ValidadorAvanzado (10+ validaciones)             │
    │                                                       │
    │  modules/validators/ (validadores específicos)       │
    │  ├─ oc_validator.py                                  │
    │  ├─ distribution_validator.py                        │
    │  └─ asn_validator.py                                 │
    └───────────────────────────────────────────────────────┘
            ↓
    ┌──────────────────────┬──────────────────────┐
    │  SALIDAS DE DATOS    │                      │
    ├──────────────────────┤                      │
    │ Reportes Excel       │  Notificaciones      │
    │ modules/reportes_excel.py                  │
    │ ├─ GeneradorReportesExcel                  │
    │ ├─ excel_styles.py                         │
    │ ├─ chart_generator.py                      │
    │ └─ pivot_generator.py                      │
    │                      │  ├─ gestor_correos.py│
    │                      │  │  (Email - 8 tipos)│
    │                      │  │                   │
    │                      │  └─ notificaciones_telegram.py
    │                      │     (Telegram)       │
    └──────────────────────┴──────────────────────┘
            ↓
    ┌───────────────────────────────────────────────────────┐
    │        SALIDA FINAL: output/                          │
    │  ├─ logs/: Archivos de log                           │
    │  └─ resultados/: Reportes Excel generados            │
    └───────────────────────────────────────────────────────┘
```

---

# 3. CICLO DE DATOS COMPLETO

## 3.1 ORIGEN DE DATOS

### Manhattan WMS - IBM DB2
```
HOST: WM260BASD
PUERTO: 50000
DATABASE: WM260BASD
SCHEMA: WMWHSE1

TABLAS PRINCIPALES:
├─ ORDERS: Cabecera de órdenes de compra
├─ ORDERDETAIL: Detalle línea a línea de OC
├─ DISTRO: Distribuciones de OC a tiendas
├─ INBOUND: Recepciones de mercancía
├─ INVENTORY: Inventario actual
├─ LOCATION: Ubicaciones del almacén
└─ STORER: Información de proveedores/tiendas
```

### Configuración de Conexión
```
config.py:
├─ DB_CONFIG: host, port, database, user, password, driver
├─ DB_POOL_CONFIG: min_size, max_size, timeout, health_check
└─ Credenciales desde .env (variables de entorno)
```

---

## 3.2 TRANSFORMACIONES DE DATOS

### Flujo: Raw Data → Datos Procesados

```
DATOS RAW (DB2)
    ↓
1. EXTRACCIÓN (Query Loader)
   ├─ Cargar SQL desde archivos
   ├─ Sustituir parámetros
   └─ Validar sintaxis
    ↓
2. CONVERSIÓN (DB2Connection)
   ├─ Ejecutar query en DB2
   ├─ Mapear resultados a DataFrame
   └─ Aplicar tipos de dato
    ↓
3. TRANSFORMACIÓN (Monitor/Validadores)
   ├─ Agregar columnas calculadas
   ├─ Renombrar columnas (mapeo DB2 → esperado)
   ├─ Filtrar registros
   └─ Consolidar datos relacionados
    ↓
4. VALIDACIÓN (ValidadorProactivo)
   ├─ Ejecutar 15+ validaciones
   ├─ Detectar inconsistencias
   ├─ Asignar severidad
   └─ Generar lista de errores
    ↓
5. ENRIQUECIMIENTO (GeneradorReportesExcel)
   ├─ Agregar estadísticas
   ├─ Crear tablas dinámicas
   ├─ Generar gráficos
   ├─ Aplicar formato corporativo
   └─ Crear múltiples hojas
    ↓
DATOS PROCESADOS (Excel/Email/Telegram)
```

### Mapeo de Columnas: DB2 → Sistema SAC

```
OC (desde WMWHSE1.ORDERS)
  ORDERKEY → OC
  EXTERNORDERKEY → OC_EXTERNA
  STORERKEY → ALMACEN
  ORDERDATE → FECHA_ORDEN
  STATUS → STATUS_OC
  ORDERTYPE → TIPO_ORDEN

ORDERDETAIL (desde WMWHSE1.ORDERDETAIL)
  ORIGINALQTY → QTY_ORIGINAL
  OPENQTY → QTY_PENDIENTE
  SHIPPEDQTY → QTY_ENVIADA
  QTYALLOCATED → QTY_ASIGNADA

DISTRIBUCIONES (desde WMWHSE1.DISTRO)
  QTY_ALLOCATED → DISTR_QTY
  LOCATION_ID → TIENDA
  SKU → SKU
  INNER_PACK → IP
```

---

## 3.3 DESTINO DE DATOS

### A) REPORTES EXCEL

**Ubicación:** `output/resultados/`

**Tipos de Reportes:**

1. **Validación OC vs Distribuciones**
   - Archivo: `Validacion_OC_{OC}_{YYYYMMDD_HHMMSS}.xlsx`
   - Hojas:
     - Validación OC: Datos y resultados
     - Estadísticas: Gráficos y resumen
   - Colores: Rojo Chedraui (#E31837) para header
   - Filtros: Auto-filter en headers

2. **Distribuciones por OC**
   - Archivo: `Distribuciones_OC_{OC}_{YYYYMMDD_HHMMSS}.xlsx`
   - Hojas:
     - Distribuciones: Detalle completo
     - Pivot Tiendas: Resumen por tienda
     - Pivot SKU: Resumen por SKU
   - Gráficos: Barras y pie charts

3. **Reporte Planning Diario**
   - Archivo: `Planning_Diario_{CEDIS}_{YYYYMMDD}.xlsx`
   - Hojas:
     - Resumen: Estadísticas del día
     - OC: Listado de órdenes
     - ASN: Status de llegadas
     - Errores: Problemas detectados
   - Incluye: Gráficos de tendencia, tablas dinámicas

4. **Reporte de Errores**
   - Archivo: `Errores_{YYYYMMDD_HHMMSS}.xlsx`
   - Hojas:
     - Por Severidad: CRÍTICO, ALTO, MEDIO, BAJO, INFO
     - Timeline: Cronología de errores
   - Colores: Codificado por severidad

### B) NOTIFICACIONES POR EMAIL

**Configuración:** `config.py` - EMAIL_CONFIG

**Destinatarios:**
- To: `EMAIL_CONFIG.to_emails` (Lista de emails)
- CC: `EMAIL_CONFIG.cc_emails` (Opcional)
- Servidor: smtp.office365.com (Office 365)
- Puerto: 587 (TLS)

**Tipos de Emails (8 tipos):**

1. **Reporte Planning Diario**
   - Asunto: `[CEDIS {code}] Reporte Planning Diario {fecha}`
   - Contenido: Tabla HTML con OC y ASN del día
   - Adjunto: Excel con reporte completo
   - Frecuencia: Diaria (por defecto a las 06:00)

2. **Alerta Crítica**
   - Asunto: `🚨 ALERTA CRÍTICA - Sistema Planning CEDIS - {fecha}`
   - Contenido: Detalle de cada error crítico detectado
   - Adjunto: Excel con listado de errores
   - Frecuencia: Inmediata (cuando se detecta)

3. **Validación OC**
   - Asunto: `Validación OC {numero} - {status}`
   - Contenido: Resumen de validación
   - Adjunto: Reporte de validación
   - Frecuencia: A demanda

4. **Programa de Recibo**
   - Asunto: `Programa de Recibo - {fecha}`
   - Contenido: Calendario de recepciones
   - Adjunto: Excel con cronograma
   - Frecuencia: Diaria

5. **Resumen Semanal** (NUEVO)
   - Asunto: `Resumen Semanal - {semana}`
   - Contenido: Estadísticas acumuladas
   - Frecuencia: Semanal (viernes)

6. **Notificación de Error** (NUEVO)
   - Asunto: `Notificación de Error - {tipo}`
   - Contenido: Detalle del problema y solución
   - Frecuencia: Inmediata

7. **Recordatorio** (NUEVO)
   - Asunto: `Recordatorio - {acción pendiente}`
   - Contenido: Tarea pendiente a ejecutar
   - Frecuencia: Configurable

8. **Confirmación de Proceso** (NUEVO)
   - Asunto: `Confirmación - {proceso} Completado`
   - Contenido: Resultado de ejecución
   - Frecuencia: Post-proceso

### C) NOTIFICACIONES POR TELEGRAM

**Configuración:** `config.py` - TELEGRAM_CONFIG

**Requerimientos:**
- Bot Token: `TELEGRAM_BOT_TOKEN`
- Chat IDs: `TELEGRAM_CHAT_IDS` (lista de IDs)
- Rate Limiter: 1 msg/segundo por chat

**Tipos de Alertas:**

1. **Alerta Crítica** (TipoAlerta.CRITICO)
   - Emoji: 🔴
   - Prioridad: Máxima
   - Contenido: Título + Descripción + OC (si aplica)

2. **Alerta Alta** (TipoAlerta.ALTO)
   - Emoji: 🟠
   - Prioridad: Alta
   - Contenido: Problema importante

3. **Alerta Media** (TipoAlerta.MEDIO)
   - Emoji: 🟡
   - Prioridad: Media
   - Contenido: Problema menor

4. **Alerta Baja** (TipoAlerta.BAJO)
   - Emoji: 🟢
   - Prioridad: Baja
   - Contenido: Información

5. **Información** (TipoAlerta.INFO)
   - Emoji: ℹ️
   - Prioridad: Mínima
   - Contenido: Notificación de estado

**Métodos de Envío:**

- `enviar_alerta()`: Alerta genérica con tipo
- `enviar_alerta_critica()`: Alerta inmediata CRÍTICA
- `enviar_estado_sistema()`: Status de conectividad
- `enviar_resumen_diario()`: Resumen de OC y ASN
- `enviar_documento()`: Enviar archivos/fotos

### D) LOGS DEL SISTEMA

**Ubicación:** `output/logs/`

**Archivos:**

1. **maestro_{YYYYMMDD}.log**
   - Contenido: Logs de orquestación
   - Nivel: INFO, WARNING, ERROR
   - Rotación: Diaria

2. **planning_automation_{YYYYMMDD}.log**
   - Contenido: Logs de main.py
   - Nivel: INFO, WARNING, ERROR
   - Rotación: Diaria

3. **sac_427.log**
   - Contenido: Log principal del sistema
   - Tamaño máx: 10 MB
   - Backups: 5 archivos (sac_427.log.1, .2, etc.)

**Formato de Log:**
```
2025-11-21 14:30:45 - MAESTRO - INFO - ✅ OC consultada: 5 registros encontrados
2025-11-21 14:30:46 - MAESTRO - ERROR - ❌ Error en validacion OC OC123: Connection timeout
2025-11-21 14:30:47 - MAESTRO - WARNING - ⚠️  Credenciales DB2 no configuradas
```

---

# 4. VALIDACIONES Y MONITOREO

## 4.1 TIPOS DE VALIDACIONES (15+)

### MonitorTiempoReal - 7 Validaciones Base

1. **VALIDAR_CONEXION_DB**
   - Severidad: CRÍTICO
   - Verifica: Conexión activa a DB2
   - Acción: Test query SELECT 1

2. **VALIDAR_OC_EXISTENTE**
   - Severidad: ALTO
   - Verifica: OC existe en DB2
   - Subvalidaciones:
     - OC_SIN_LETRA_C: Formato incorrecto
     - OC_VENCIDA: Vigencia expirada

3. **VALIDAR_DISTRIBUCIONES**
   - Severidad: CRÍTICO/ALTO
   - Verifica: Cantidad distribuida vs OC
   - Subvalidaciones:
     - DISTRO_EXCEDENTE: Más distribuido que OC (CRÍTICO)
     - DISTRO_INCOMPLETA: Menos distribuido (ALTO)
     - SIN_DISTRIBUCIONES: Sin asignación (CRÍTICO)
     - SKU_SIN_IP: Sin Inner Pack (MEDIO)

4. **VALIDAR_ASN_STATUS**
   - Severidad: MEDIO/BAJO
   - Verifica: Status y actualización de ASN
   - Subvalidaciones:
     - ASN_NO_ENCONTRADO (ALTO)
     - ASN_STATUS_INVALIDO (MEDIO)
     - ASN_SIN_ACTUALIZACION (BAJO)

5. **VALIDAR_DATOS_EXCEL**
   - Severidad: ALTO/MEDIO
   - Verifica: Integridad de archivo Excel
   - Subvalidaciones:
     - EXCEL_VACIO (ALTO)
     - COLUMNAS_FALTANTES (ALTO)
     - DATOS_NULOS (MEDIO)

### ValidadorAvanzado - 10+ Validaciones Adicionales

6. **VALIDAR_SECUENCIA_OC**
   - Severidad: BAJO
   - Verifica: Gaps en numeración de OC
   - Detecta: Órdenes faltantes

7. **VALIDAR_PROVEEDOR_ACTIVO**
   - Severidad: ALTO
   - Verifica: Proveedor con status activo
   - Acción: Rechazar OC de proveedores inactivos

8. **VALIDAR_TIENDA_ACTIVA**
   - Severidad: CRÍTICO/ALTO
   - Verifica: Tienda receptora está activa
   - Acción: Bloquear distribuciones a tiendas cerradas

9. **VALIDAR_RUTA_ENTREGA**
   - Severidad: ALTO
   - Verifica: Ruta configurada para tienda
   - Acción: Alertar si no existe ruta

10. **VALIDAR_CAPACIDAD_ALMACEN**
    - Severidad: CRÍTICO
    - Verifica: Espacio disponible en almacén
    - Cálculo: (inventario_actual + entrada) > capacidad_máx

11. **VALIDAR_HORARIO_RECIBO**
    - Severidad: MEDIO
    - Verifica: Recepción dentro de horario
    - Horarios: 6:00 - 22:00 (configurable)

12. **VALIDAR_DOCUMENTACION_COMPLETA**
    - Severidad: ALTO
    - Verifica: Documentos requeridos presentes
    - Documentos: FACTURA, REMISIÓN, OC

13. **VALIDAR_APROBACIONES**
    - Severidad: ALTO
    - Verifica: OC tiene aprobaciones necesarias
    - Contador: aprobaciones_actuales >= aprobaciones_requeridas

14. **VALIDAR_PRESUPUESTO**
    - Severidad: CRÍTICO
    - Verifica: Monto de OC vs presupuesto disponible
    - Acción: Rechazar si excede

15. **VALIDAR_PRIORIDAD**
    - Severidad: INFO
    - Verifica: OC de alta prioridad
    - Acción: Alertar para procesamiento prioritario

---

## 4.2 NIVELES DE SEVERIDAD

```
🔴 CRÍTICO - ErrorSeverity.CRITICO
   ├─ Requiere acción inmediata
   ├─ Detiene procesos
   ├─ Envía alertas por todos los canales
   └─ Ejemplos:
      ├─ Distribución excedente (más que OC)
      ├─ Sin distribuciones (OC sin asignar)
      ├─ Tienda inactiva
      ├─ Capacidad excedida
      └─ Presupuesto excedido

🟠 ALTO - ErrorSeverity.ALTO
   ├─ Requiere atención urgente
   ├─ Puede bloquear procesos
   ├─ Envía alertas por email
   └─ Ejemplos:
      ├─ OC vencida
      ├─ OC no encontrada
      ├─ Distribución incompleta
      ├─ ASN no encontrado
      └─ Documentación faltante

🟡 MEDIO - ErrorSeverity.MEDIO
   ├─ Requiere revisión
   ├─ No bloquea procesos
   ├─ Log en sistema
   └─ Ejemplos:
      ├─ SKU sin Inner Pack
      ├─ ASN status inválido
      ├─ Horario de recibo
      └─ Datos nulos en Excel

🟢 BAJO - ErrorSeverity.BAJO
   ├─ Información importante
   ├─ No requiere acción inmediata
   ├─ Log para auditoría
   └─ Ejemplos:
      ├─ ASN sin actualización reciente
      ├─ Gaps en secuencia OC
      └─ Cambios de estado

ℹ️ INFO - ErrorSeverity.INFO
   ├─ Notificación de sistema
   ├─ Solo logging
   └─ Ejemplos:
      ├─ OC de alta prioridad detectada
      ├─ Proceso completado exitosamente
      └─ Resumen de operación
```

---

# 5. SISTEMA DE NOTIFICACIONES

## 5.1 GESTIÓN DE CORREOS (8 TIPOS)

### GestorCorreos (476 líneas)

**Inicialización:**
```python
config = {
    'smtp_server': 'smtp.office365.com',
    'smtp_port': 587,
    'user': EMAIL_USER,
    'password': EMAIL_PASSWORD,
    'from_name': 'Sistema SAC - CEDIS 427',
    'cedis_nombre': 'CEDIS Cancún 427'
}
gestor = GestorCorreos(config)
```

**8 Tipos de Emails:**

1. **enviar_reporte_planning_diario()**
   ```python
   gestor.enviar_reporte_planning_diario(
       destinatarios=['planning@chedraui.com.mx'],
       df_oc=df_oc,
       df_asn=df_asn,
       archivos_adjuntos=['Planning_Diario_427_20251121.xlsx']
   )
   ```
   - Tabla HTML con OC y ASN del día
   - Estadísticas y resumen
   - Archivo Excel adjunto

2. **enviar_alerta_critica()**
   ```python
   gestor.enviar_alerta_critica(
       destinatarios=['supervisor@chedraui.com.mx'],
       tipo_error='DISTRO_EXCEDENTE',
       descripcion='Distribución excedente en OC12345',
       oc_numero='OC12345'
   )
   ```
   - Alerta inmediata
   - Detalle de problema
   - Recomendaciones de solución

3. **enviar_validacion_oc()**
   - Resultado de validación de OC
   - Status: OK, ALERTA, CRÍTICO
   - Detalles de errores encontrados

4. **enviar_programa_recibo()**
   - Cronograma de recepciones próximas
   - Coordinación de almacén
   - Recursos requeridos

5. **enviar_resumen_semanal()**
   - Estadísticas semanales
   - OC procesadas
   - Errores detectados
   - Tendencias

6. **enviar_notificacion_error()**
   - Detalle de cada error
   - Módulo afectado
   - Recomendación de solución

7. **enviar_recordatorio()**
   - Tareas pendientes
   - OC a revisar
   - Aprobaciones faltantes

8. **enviar_confirmacion_proceso()**
   - Confirmación de ejecución
   - Resultado final
   - Archivos generados

### Sistema de Emails Integrado

**Módulos de soporte:**
- `modules/email/email_client.py`: Cliente SMTP avanzado
- `modules/email/template_engine.py`: Templates Jinja2 HTML
- `modules/email/queue.py`: Cola con reintentos automáticos
- `modules/email/scheduler.py`: Programación de envíos
- `modules/email/recipients.py`: Gestión de destinatarios por categoría

---

## 5.2 NOTIFICACIONES TELEGRAM (920 LÍNEAS)

### NotificadorTelegram

**Configuración:**
```python
TELEGRAM_CONFIG = {
    'bot_token': 'tu_token_bot',  # De @BotFather
    'chat_ids': [123456789, 987654321],  # Tus chat IDs
    'enabled': True,
    'alertas_criticas': True,
    'resumen_diario': True
}
```

**Rate Limiter Integrado:**
- Máximo: 1 mensaje/segundo al mismo chat
- Máximo: 25 mensajes/segundo globales
- Respeta límites de Telegram API
- Control de throttling automático

**Tipos de Alertas:**

```
┌─────────────────────────────────────────────┐
│         TIPOS DE ALERTA TELEGRAM            │
├─────────────────────────────────────────────┤
│ 🔴 CRITICO                                  │
│    └─ enviar_alerta_critica(titulo, desc)  │
│                                             │
│ 🟠 ALTO                                    │
│    └─ enviar_alerta(TipoAlerta.ALTO, ...)  │
│                                             │
│ 🟡 MEDIO                                   │
│    └─ enviar_alerta(TipoAlerta.MEDIO, ...) │
│                                             │
│ 🟢 BAJO                                    │
│    └─ enviar_alerta(TipoAlerta.BAJO, ...)  │
│                                             │
│ ℹ️ INFO                                    │
│    └─ enviar_alerta(TipoAlerta.INFO, ...)  │
└─────────────────────────────────────────────┘
```

**Métodos de Notificación:**

1. **enviar_alerta()**
   ```python
   resultado = notificador.enviar_alerta(
       tipo=TipoAlerta.CRITICO,
       titulo='Validación OC',
       mensaje='OC12345: Distribución excedente',
       modulo='VALIDACION_OC'
   )
   # Retorna: {'chat_1': True, 'chat_2': False}
   ```

2. **enviar_alerta_critica()**
   ```python
   resultado = notificador.enviar_alerta_critica(
       titulo='STOP: Distribución Excedente',
       descripcion='OC tiene 500 unidades de más',
       oc_numero='OC12345'
   )
   # Prioridad máxima, múltiples intentos
   ```

3. **enviar_estado_sistema()**
   ```python
   resultado = notificador.enviar_estado_sistema(
       db_conectada=True,
       email_configurado=True,
       ultimo_reporte='2025-11-21 14:30',
       errores_pendientes=2
   )
   # Estado actual de todos los componentes
   ```

4. **enviar_resumen_diario()**
   ```python
   resultado = notificador.enviar_resumen_diario(
       total_oc=45,
       oc_ok=43,
       oc_problemas=2,
       total_asn=52,
       asn_recibido=50,
       errores_criticos=0
   )
   # Resumen de operación del día
   ```

5. **enviar_documento()**
   ```python
   resultado = notificador.enviar_documento(
       archivo='output/resultados/Planning_Diario.xlsx',
       descripcion='Reporte diario de Planning'
   )
   # Envía archivo/imagen adjunto
   ```

---

# 6. QUERIES SQL - ORGANIZACIÓN

## 6.1 CATEGORÍAS DE QUERIES

### A) OBLIGATORIAS (8 queries) - Ejecución Diaria

**Propósito:** Extraer datos críticos de operación diaria

| Query | Ubicación | Frecuencia | Parámetros | Propósito |
|-------|-----------|-----------|-----------|----------|
| `oc_diarias.sql` | obligatorias/ | Diaria 06:00 | fecha_inicio, fecha_fin, storerkey | OC ingresadas/modificadas hoy |
| `oc_pendientes.sql` | obligatorias/ | Diaria 09:00 | storerkey | OC sin completar |
| `oc_vencidas.sql` | obligatorias/ | Diaria 06:00 | storerkey | OC con vigencia expirada |
| `asn_status.sql` | obligatorias/ | Diaria 06:00 | fecha_inicio, fecha_fin, storerkey | Status de llegadas |
| `asn_pendientes.sql` | obligatorias/ | Diaria 09:00 | storerkey | ASN no recibidos |
| `distribuciones_dia.sql` | obligatorias/ | Diaria 06:00 | fecha_inicio, fecha_fin, storerkey | Distribuciones del día |
| `inventario_resumen.sql` | obligatorias/ | Diaria 21:00 | storerkey | Inventario actual total |
| `recibo_programado.sql` | obligatorias/ | Diaria 06:00 | fecha_inicio, fecha_fin, storerkey | Cronograma de recepciones |

**Ejemplo: oc_diarias.sql**
```sql
SELECT
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.STORERKEY AS almacen,
    o.STATUS AS status_oc,
    COUNT(od.ORDERLINENUMBER) AS total_lineas,
    SUM(od.ORIGINALQTY) AS qty_original_total,
    SUM(od.OPENQTY) AS qty_pendiente_total
FROM WMWHSE1.ORDERS o
LEFT JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
WHERE o.STORERKEY = '{{storerkey}}'
  AND (DATE(o.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
       OR DATE(o.EDITDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}')
GROUP BY o.ORDERKEY, o.EXTERNORDERKEY, o.STORERKEY, o.STATUS
ORDER BY o.ADDDATE DESC;
```

### B) PREVENTIVAS - Validaciones Proactivas

**Propósito:** Detección temprana de problemas

Ejecución: Cada 15 min (daemon) y a las 15:00 (tarea programada)

Ejemplos:
- OC sin distribuciones asignadas
- Distribuciones que exceden OC
- Proveedores con múltiples errores
- Patrones de retrasos en ASN

### C) BAJO_DEMANDA (6 queries) - Búsquedas Puntuales

**Propósito:** Consultas por solicitud del usuario

| Query | Propósito | Parámetros |
|-------|-----------|-----------|
| `buscar_oc.sql` | Detalles de OC específica | oc_numero, storerkey |
| `buscar_asn.sql` | Detalles de ASN | asn_numero, storerkey |
| `buscar_lpn.sql` | Datos de LPN (caja/cartón) | lpn_numero, storerkey |
| `buscar_sku.sql` | Información de producto | sku, storerkey |
| `detalle_distribucion.sql` | Distribuciones de una OC | oc_referencia, storerkey, tienda_destino |
| `historial_oc.sql` | Movimientos históricos | oc_numero, storerkey, fecha_inicio, fecha_fin |
| `movimientos_lpn.sql` | Historial de LPN | lpn_numero, storerkey |

### D) DDL - Data Definition Language

**Propósito:** Crear vistas y procedimientos almacenados

**Vistas SQL:**
- `v_oc_summary.sql` - Resumen de OC con totales
- `v_asn_status.sql` - Vista de ASN con descriptions
- `v_distribution_totals.sql` - Totales por distribución

**Procedimientos Almacenados:**
- `sp_validate_oc.sql` - Validar OC en base de datos
- `sp_get_daily_report.sql` - Generar reporte del día

---

## 6.2 QUERY LOADER (query_loader.py)

**Funcionalidades:**

```python
from queries import (
    QueryLoader, QueryCategory,
    load_query, load_query_with_params,
    get_default_loader
)

# Obtener loader
loader = get_default_loader()

# Listar queries disponibles
queries = loader.list_queries(QueryCategory.OBLIGATORIAS)

# Cargar query sin parámetros
sql = load_query(QueryCategory.OBLIGATORIAS, "oc_diarias")

# Cargar query con parámetros
sql = load_query_with_params(
    QueryCategory.BAJO_DEMANDA,
    "buscar_oc",
    {
        "oc_numero": "OC123456",
        "storerkey": "C22"
    }
)

# Ejecutar con DB2Connection
df = db_connection.execute_query(sql)
```

**Características:**
- Caché de queries cargadas
- Validación de sintaxis SQL
- Soporte para templates Jinja2
- Substitución de parámetros con {{param}}
- Metadatos de cada query (autor, fecha, tablas)

---

# 7. GENERACIÓN DE REPORTES

## 7.1 TIPOS DE REPORTES (5+)

### GeneradorReportesExcel (varies líneas)

```python
from modules.reportes_excel import GeneradorReportesExcel

generador = GeneradorReportesExcel(cedis="CANCÚN")
```

### 1. Reporte de Validación OC vs Distribuciones

**Método:** `crear_reporte_validacion_oc()`

```python
generador.crear_reporte_validacion_oc(
    df_validacion=df,
    nombre_archivo="Validacion_OC_123_20251121_143022.xlsx"
)
```

**Contenido:**
```
┌─────────────────────────────────────────────────────────┐
│ ENCABEZADO (Filas 1-4)                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Rojo Chedraui #E31837]  REPORTE DE VALIDACIÓN      │ │
│ │ Órdenes de Compra vs Distribuciones                 │ │
│ │ CEDIS Cancún | Fecha: 21/11/2025                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ DATOS PRINCIPALES (Filas 5+)                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ OC │ Total_OC │ Total_Distro │ Diferencia │ STATUS  │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ OC001 │ 1,000 │ 1,000 │ 0 │ ✅ OK              │ │
│ │ OC002 │ 2,000 │ 1,800 │ 200 │ ⚠️ Revisar        │ │
│ │ OC003 │ 1,500 │ 1,650 │ -150 │ 🔴 CRÍTICO       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ RESUMEN (Abajo)                                         │
│ Total OC Validadas: 3                                   │
│ OK: 1 | Alertas: 1 | Críticos: 1                       │
│ % Exactitud: 33%                                        │
└─────────────────────────────────────────────────────────┘
```

**Hojas:**
- Validación OC: Datos y resultados
- Estadísticas: Gráficos y resumen

### 2. Reporte de Distribuciones por OC

**Método:** `crear_reporte_distribuciones()`

```python
generador.crear_reporte_distribuciones(
    df_distribuciones=df,
    oc_numero="OC12345",
    nombre_archivo="Distribuciones_OC_12345_20251121.xlsx"
)
```

**Hojas:**
- Distribuciones: Detalle tienda x tienda
- Pivot Tiendas: Resumen por punto de venta
- Pivot SKU: Resumen por producto
- Gráficos: Distribución por tienda y SKU

### 3. Reporte Planning Diario

**Método:** `crear_reporte_planning_diario()`

```python
generador.crear_reporte_planning_diario(
    df_oc=df_oc,
    df_asn=df_asn,
    df_errores=df_errores,
    nombre_archivo="Planning_Diario_427_20251121.xlsx"
)
```

**Hojas:**
1. Resumen
   - Estadísticas del día
   - Gráficos de estado
   - KPIs principales

2. OC
   - Listado completo de órdenes
   - Status y cantidades
   - Auto-filter en headers

3. ASN
   - Llegadas esperadas
   - Status de recepciones
   - ETAs

4. Errores
   - Problemas detectados por severidad
   - Detalles y soluciones
   - Timeline

### 4. Reporte de Errores

**Método:** `crear_reporte_errores()`

**Organización:**
- Hoja 1: Por Severidad
  - CRÍTICO: Acciones inmediatas
  - ALTO: Requiere atención
  - MEDIO: Revisar
  - BAJO: Informativo

- Hoja 2: Timeline
  - Cronología de errores
  - Hora exacta de detección
  - Módulo afectado

- Hoja 3: Por Tipo
  - Errores agrupados por tipo
  - Frecuencia de ocurrencia
  - Tendencias

### 5. Reporte de Reconciliación

**Propósito:** Validar consistencia de datos

---

## 7.2 FORMATOS Y ESTILOS CORPORATIVOS

### Colores Chedraui

```python
COLORS = {
    # Corporativos
    'chedraui_red': '#E31837',      # Encabezados
    'chedraui_blue': '#003DA5',     # Alternativo
    'chedraui_green': '#92D050',    # Success
    
    # Por severidad
    'critico': '#FF0000',           # Rojo puro
    'alto': '#FFC000',              # Naranja
    'medio': '#FFFF00',             # Amarillo
    'bajo': '#92D050',              # Verde
    'info': '#B4C7E7',              # Azul claro
}
```

### Estilos Aplicados

```python
# Header
- Font: Bold, Blanco 12pt, Arial
- Fill: Rojo Chedraui #E31837
- Alignment: Centro, Vertical Centro
- Border: Todas

# SubHeader
- Font: Normal, Negro 11pt
- Fill: Peach claro #F8CBAD
- Alignment: Centro
- Border: Fondo

# Datos
- Font: Normal, Negro 10pt
- Fill: Blanco
- Alignment: Izquierda/Centro según tipo
- Border: Ligera

# Resumen
- Font: Bold, Negro 11pt
- Fill: Gris claro
- Alignment: Centro
- Border: Doble fondo
```

### Características Automáticas

1. **Auto-fit de Columnas**
   - Ancho automático según contenido
   - Mínimo: 10, Máximo: 50

2. **Freeze Panes**
   - Filas de header congeladas
   - Facilita scroll vertical

3. **Auto-Filter**
   - Filtros en fila de header
   - Todos los reportes

4. **Gráficos**
   - Barras: Para comparaciones
   - Pie: Para porcentajes
   - Línea: Para tendencias

5. **Tablas Dinámicas** (Pivot)
   - Resumen por dimensión
   - Subtotales automáticos
   - Expandible/colapsable

---

# 8. SCHEDULING Y AUTOMATIZACIÓN

## 8.1 MODO DAEMON - TAREAS PROGRAMADAS

**Inicialización:**
```bash
python maestro.py --daemon
```

**Sistema de Scheduling:**
- Biblioteca: `schedule` (Python)
- Resolución: 1 minuto (revisa cada minuto)
- Precisión: ±1 minuto

### Horarios de Ejecución

```
┌────────────────────────────────────────────────────────┐
│           CALENDARIO DE EJECUCIÓN DIARIA               │
├────────────────────────────────────────────────────────┤
│ 00:00 │ RESET DIARIO                                  │
│       │ └─ Limpiar: contador tareas, alertas, errores │
│       │ └─ Log: Resumen nocturno si hay               │
│       │                                               │
│ 06:00 │ REPORTE MATUTINO                             │
│       │ ├─ ejecutar_monitoreo()                      │
│       │ ├─ ejecutar_reporte_diario()                 │
│       │ └─ Notificar por Email + Telegram            │
│       │                                               │
│ 09:00 │ VALIDACIÓN DE PENDIENTES                      │
│       │ ├─ ejecutar_validacion_preventiva()          │
│       │ └─ Detectar OC en riesgo                      │
│       │                                               │
│ 12:00 │ MONITOREO DE MEDIO DÍA                        │
│       │ └─ ejecutar_monitoreo()                      │
│       │    (Verificación rápida de status)            │
│       │                                               │
│ 15:00 │ VALIDACIÓN PREVENTIVA                         │
│       │ └─ ejecutar_validacion_preventiva()          │
│       │    (Segunda onda del día)                     │
│       │                                               │
│ 18:00 │ REPORTE VESPERTINO                            │
│       │ ├─ ejecutar_reporte_diario()                 │
│       │ └─ Resumen de tarde                          │
│       │                                               │
│ 21:00 │ RESUMEN DEL DÍA                               │
│       │ └─ ejecutar_resumen_dia()                    │
│       │    (Consolidación de estadísticas)            │
│       │                                               │
│ CADA  │ MONITOREO CONTINUO                            │
│ 15    │ └─ ejecutar_monitoreo()                      │
│ MIN   │    (Cada 15 minutos, 24x7)                   │
└────────────────────────────────────────────────────────┘
```

## 8.2 INTEGRACIÓN CON SISTEMA OPERATIVO

### Instalación como Servicio Windows

**Script:** `instalar_sac.py` (892 líneas)

```bash
python instalar_sac.py --instalar
# Crea servicio Windows: SistemaSAC
# Arranque automático
# Se ejecuta con usuario configurado

python instalar_sac.py --reiniciar
# Reinicia servicio

python instalar_sac.py --desinstalar
# Remueve servicio
```

### Instalación como Daemon Linux

```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/sac.service

[Unit]
Description=Sistema de Automatización de Consultas - CEDIS 427
After=network.target

[Service]
Type=simple
User=sac_user
WorkingDirectory=/opt/sac
ExecStart=/usr/bin/python /opt/sac/maestro.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Activar servicio
sudo systemctl enable sac
sudo systemctl start sac
sudo systemctl status sac
```

---

# 9. ESTRUCTURA DE DIRECTORIOS Y ARCHIVOS

```
SAC_V01_427_ADMJAJA/
│
├─ config.py                          # Configuración central
├─ config/
│  └─ README.md                      # Guía de configuración
│
├─ main.py                           # Interfaz principal
├─ maestro.py                        # Orquestador central
├─ monitor.py                        # Monitoreo y validación
├─ gestor_correos.py                 # Gestión de emails
├─ notificaciones_telegram.py        # Notificaciones Telegram
├─ notificaciones_whatsapp.py        # Notificaciones WhatsApp (dev)
│
├─ modules/
│  ├─ __init__.py
│  ├─ db_connection.py              # Conexión DB2
│  ├─ db_pool.py                    # Pool de conexiones
│  ├─ db_schema.py                  # Esquema de tablas
│  ├─ reportes_excel.py             # Generador de reportes
│  ├─ excel_styles.py               # Estilos corporativos
│  ├─ chart_generator.py            # Gráficos
│  ├─ pivot_generator.py            # Tablas dinámicas
│  ├─ export_manager.py             # Exportación de datos
│  ├─ exportar_pdf.py               # Exportación a PDF
│  ├─ anomaly_detector.py           # Detección de anomalías
│  ├─ reconciliation.py             # Reconciliación de datos
│  ├─ validation_result.py          # Resultado de validación
│  ├─ query_builder.py              # Constructor de queries
│  │
│  ├─ email/
│  │  ├─ __init__.py
│  │  ├─ email_client.py            # Cliente SMTP
│  │  ├─ email_message.py           # Estructura de mensaje
│  │  ├─ template_engine.py         # Engine de templates
│  │  ├─ queue.py                   # Cola de envío
│  │  ├─ scheduler.py               # Scheduler de emails
│  │  └─ recipients.py              # Gestión de destinatarios
│  │
│  ├─ excel_templates/
│  │  ├─ __init__.py
│  │  ├─ base_template.py           # Template base
│  │  └─ report_templates.py        # Templates de reportes
│  │
│  ├─ repositories/
│  │  ├─ __init__.py
│  │  ├─ base_repository.py         # Clase base
│  │  ├─ oc_repository.py           # Repositorio OC
│  │  ├─ distribution_repository.py # Repositorio distribuciones
│  │  └─ asn_repository.py          # Repositorio ASN
│  │
│  ├─ validators/
│  │  ├─ __init__.py
│  │  ├─ base_validator.py          # Validador base
│  │  ├─ oc_validator.py            # Validador OC
│  │  ├─ distribution_validator.py  # Validador distribuciones
│  │  ├─ asn_validator.py           # Validador ASN
│  │  ├─ lpn_validator.py           # Validador LPN
│  │  └─ sku_validator.py           # Validador SKU
│  │
│  └─ rules/
│     ├─ __init__.py
│     ├─ rule_engine.py             # Motor de reglas de negocio
│     └─ business_rules.py          # Reglas de negocio
│
├─ queries/
│  ├─ __init__.py
│  ├─ query_loader.py               # Cargador de queries
│  │
│  ├─ obligatorias/
│  │  ├─ __init__.py
│  │  ├─ oc_diarias.sql
│  │  ├─ oc_pendientes.sql
│  │  ├─ oc_vencidas.sql
│  │  ├─ asn_status.sql
│  │  ├─ asn_pendientes.sql
│  │  ├─ distribuciones_dia.sql
│  │  ├─ inventario_resumen.sql
│  │  └─ recibo_programado.sql
│  │
│  ├─ preventivas/
│  │  └─ __init__.py
│  │
│  ├─ bajo_demanda/
│  │  ├─ __init__.py
│  │  ├─ buscar_oc.sql
│  │  ├─ buscar_asn.sql
│  │  ├─ buscar_lpn.sql
│  │  ├─ buscar_sku.sql
│  │  ├─ detalle_distribucion.sql
│  │  ├─ historial_oc.sql
│  │  └─ movimientos_lpn.sql
│  │
│  ├─ templates/
│  │  └─ __init__.py
│  │
│  └─ ddl/
│     ├─ __init__.py
│     ├─ views/
│     │  ├─ __init__.py
│     │  ├─ v_oc_summary.sql
│     │  ├─ v_asn_status.sql
│     │  └─ v_distribution_totals.sql
│     └─ procedures/
│        ├─ __init__.py
│        ├─ sp_validate_oc.sql
│        └─ sp_get_daily_report.sql
│
├─ tests/
│  ├─ __init__.py
│  ├─ test_monitor_scenarios.py
│  ├─ test_repositories.py
│  ├─ test_validators.py
│  ├─ test_db_connection.py
│  ├─ test_email_client.py
│  ├─ test_gestor_correos_scenarios.py
│  ├─ test_reportes_excel_scenarios.py
│  └─ ... (más tests)
│
├─ output/                           # [Gitignored]
│  ├─ logs/
│  │  ├─ maestro_20251121.log
│  │  ├─ planning_automation_20251121.log
│  │  └─ sac_427.log
│  └─ resultados/
│     ├─ Validacion_OC_*.xlsx
│     ├─ Planning_Diario_*.xlsx
│     └─ ... (reportes generados)
│
├─ docs/
│  ├─ README.md                     # Documentación principal
│  ├─ QUICK_START.md                # Guía rápida
│  ├─ FUNCIONALIDADES_COMPLETAS.md  # Features detallado
│  ├─ NUEVAS_FUNCIONALIDADES.md     # Roadmap
│  ├─ RESUMEN_PROYECTO.md           # Resumen ejecutivo
│  └─ LICENCIA.md                   # Licencia
│
├─ .env                             # Variables de entorno [Gitignored]
├─ env                              # Template de .env
├─ .gitignore                       # Reglas de git
├─ requirements.txt                 # Dependencias Python
├─ README.md                        # README principal
│
├─ ejemplos.py                      # 6 ejemplos de uso interactivos
├─ verificar_sistema.py             # Utilidad de verificación
├─ dashboard.py                     # Dashboard web (desarrollo)
│
├─ build_exe.py                     # Compilación a EXE
├─ build_executable.py              # Construcción ejecutable
├─ instalar_sac.py                  # Instalador del sistema
├─ sac_launcher.py                  # Lanzador del sistema
├─ enviar_hito_lanzamiento.py      # Script de lanzamiento
└─ crear_distribucion.py            # Generador de distribuciones

ESTADÍSTICAS DE CÓDIGO:
├─ Total líneas Python: 9,952
├─ Archivos Python: 15+ principales
├─ Módulos: 30+ componentes
├─ Tests: 25+ archivos de test
└─ Documentación: 6 archivos MD
```

---

# CONCLUSIÓN

El Sistema SAC es una solución empresarial completa y robusta que:

1. **Automatiza validación** de OC con 15+ tipos de control
2. **Monitorea 24/7** mediante tareas programadas en daemon
3. **Notifica multi-canal** por Email, Telegram, WhatsApp
4. **Genera reportes** profesionales en Excel con formato Chedraui
5. **Integra con DB2** Manhattan WMS de forma nativa
6. **Proporciona visibilidad** en tiempo real de operaciones
7. **Reduce errores** en cadena de suministro significativamente
8. **Acelera procesos** de validación y aprobación

**Filosofía del Proyecto:**
> "Las máquinas y los sistemas al servicio de los analistas"

Desarrollado con dedicación para que el equipo de Planning tenga más tiempo para tomar decisiones inteligentes en lugar de realizar validaciones manuales.

