# PLAN PARA CREAR EL SCRIPT MAESTRO DEL SISTEMA SAC

## Propósito General

El script maestro debe orquestar TODOS los procesos del sistema SAC:
- Ejecutar procesos diarios en horarios específicos
- Mantener monitoreo continuo 24/7
- Gestionar errores y reintentos
- Mantener logs centralizados
- Coordinar múltiples procesos en paralelo cuando sea posible

---

## ESTRUCTURA PROPUESTA PARA EL SCRIPT MAESTRO

### Ubicación: `/home/user/SAC_V01_427_ADMJAJA/maestro.py`

### Responsabilidades:

```
maestro.py (Nuevo script - ~500-800 líneas)
│
├── 1. INICIALIZACIÓN (startup)
│   ├── Cargar configuración
│   ├── Verificar sistema (verificar_sistema.py)
│   ├── Inicializar logging
│   ├── Establecer conexión a DB2
│   ├── Inicializar notificadores (Email, Telegram)
│   └── Mostrar estado inicial
│
├── 2. PLANIFICADOR (Scheduler)
│   ├── APScheduler o cronograma manual
│   ├── Tareas diarias (4)
│   ├── Tareas cada N minutos (preventivas)
│   ├── Tareas cada hora (sincronización)
│   └── Tareas bajo demanda
│
├── 3. MONITOREO CONTINUO (Background)
│   ├── Ejecutar monitor.py en thread separado
│   ├── Chequear errores CRÍTICO
│   ├── Alertas instantáneas
│   └── Actualizar dashboard
│
├── 4. GESTIÓN DE ERRORES
│   ├── Reintentos automáticos
│   ├── Fallback strategies
│   ├── Notificaciones sobre fallos
│   └── Recuperación automática
│
├── 5. REPORTES Y ESTADÍSTICAS
│   ├── Resumen de ejecuciones
│   ├── Contador de procesos
│   ├── Errores y alertas
│   ├── Métricas de rendimiento
│   └── Histórico diario
│
└── 6. API/INTERFAZ DE CONTROL
    ├── Comandos interactivos
    ├── Ejecución manual de procesos
    ├── Cambio de configuración
    └── Reporte de estado
```

---

## TAREAS PRINCIPALES A ORQUESTAR

### 1. PROCESOS DIARIOS (Ejecución una sola vez por día)

#### Tarea 1.1: Reporte Planning Diario - 06:00 AM
```python
{
    'nombre': 'Reporte Planning Diario',
    'horario': '06:00',
    'comando': 'python main.py --reporte-diario',
    'descripcion': 'Genera y envía reporte diario de OCs y ASNs',
    'timeout': 300,  # 5 minutos
    'reintentos': 2,
    'notificación': True,
    'urgencia': 'NORMAL'
}
```

**Qué hace**:
1. Ejecuta `query_loader.load_query('oc_diarias')`
2. Ejecuta `query_loader.load_query('asn_pendientes')`
3. Ejecuta `query_loader.load_query('distribuciones_dia')`
4. Combina datos en DataFrame
5. Llama `reportes_excel.crear_reporte_planning_diario()`
6. Envía vía `gestor_correos.enviar_reporte_planning_diario()`
7. Notifica vía Telegram `NotificadorTelegram.enviar_resumen_diario()`
8. Guarda en `output/resultados/`

**Dependencias**:
- main.py (CLI)
- config.py
- query_loader.py
- db_connection.py
- reportes_excel.py
- gestor_correos.py
- notificaciones_telegram.py

---

#### Tarea 1.2: Validación de OCs Vencidas - 09:00 AM
```python
{
    'nombre': 'Validación OCs Vencidas',
    'horario': '09:00',
    'comando': 'python main.py --validar-vencidas',
    'descripcion': 'Detecta OCs a punto de vencer o vencidas',
    'timeout': 600,  # 10 minutos
    'reintentos': 1,
    'notificación': True,
    'urgencia': 'ALTO'  # Si encuentra críticos
}
```

**Qué hace**:
1. Ejecuta `query_loader.load_query('oc_vencidas')`
2. Ejecuta `query_loader.load_query('oc_por_vencer')`
3. Llama `monitor.validar_oc_vencidas()`
4. Si hay CRÍTICOS → alerta inmediata Telegram
5. Genera reporte
6. Envía email

---

#### Tarea 1.3: Resumen Ejecutivo - 06:00 PM
```python
{
    'nombre': 'Resumen Ejecutivo del Día',
    'horario': '18:00',
    'comando': 'python maestro.py --resumen-diario',
    'descripcion': 'Consolidado de operaciones del día',
    'timeout': 300,
    'reintentos': 1,
    'notificación': True,
    'urgencia': 'NORMAL'
}
```

**Qué hace**:
1. Recolecta todas las ejecuciones del día
2. Cuenta errores y alertas
3. Genera resumen ejecutivo
4. Envía vía email con formato HTML
5. Notifica Telegram con resumen

---

#### Tarea 1.4: Limpieza y Backup - 11:00 PM
```python
{
    'nombre': 'Limpieza y Backup Diario',
    'horario': '23:00',
    'comando': 'python maestro.py --backup',
    'descripcion': 'Limpia logs antiguos, hace backup de datos',
    'timeout': 600,
    'reintentos': 0,
    'notificación': False,
    'urgencia': 'BAJO'
}
```

**Qué hace**:
1. Comprime logs de más de 7 días
2. Hace backup de `output/resultados/`
3. Sincroniza DB local con DB2
4. Limpia cache temporal
5. Genera estadísticas

---

### 2. PROCESOS PREVENTIVOS (Cada 15 minutos)

```python
{
    'nombre': 'Chequeo Preventivo',
    'intervalo_minutos': 15,
    'comandos': [
        'query_loader.load_query("distribuciones_excedentes")',
        'query_loader.load_query("distribuciones_incompletas")',
        'query_loader.load_query("asn_sin_actualizar")',
        'query_loader.load_query("sku_sin_innerpack")'
    ],
    'timeout': 120,
    'notificación': True,  # Solo si hay CRÍTICO
    'urgencia': 'VARIABLE'
}
```

**Qué hace**:
1. Ejecuta 4 queries preventivas en paralelo
2. Busca errores CRÍTICO
3. Si encuentra → alerta Telegram inmediata + email
4. Actualiza caché local
5. Actualiza dashboard

---

### 3. PROCESOS HORARIOS (Cada hora)

```python
{
    'nombre': 'Sincronización Horaria',
    'intervalo_horas': 1,
    'tareas': [
        'sincronizar_db_local()',
        'actualizar_dashboard()',
        'generar_estadisticas_hora()'
    ],
    'timeout': 300,
    'notificación': False,
    'urgencia': 'BAJO'
}
```

**Qué hace**:
1. Sincroniza DB2 con DB local (SQLite)
2. Actualiza dashboard web
3. Calcula métricas horarias
4. Comprueba salud del sistema

---

### 4. PROCESOS BAJO DEMANDA

Ejecutables desde menú o CLI:

```python
comandos_bajo_demanda = {
    'validar-oc': 'python main.py --oc {OC_NUMBER}',
    'validar-todas': 'python main.py --validar-todas',
    'reporte-oc': 'python main.py --reporte-oc {OC_NUMBER}',
    'buscar-oc': 'python main.py --buscar {OC_NUMBER}',
    'buscar-lpn': 'python main.py --buscar-lpn {LPN}',
    'buscar-asn': 'python main.py --buscar-asn {ASN}',
    'auditoria': 'python main.py --auditoria {USER}',
    'dashboard': 'python dashboard.py'
}
```

---

## ARQUITECTURA DEL SCRIPT MAESTRO

### Componentes Clave:

```python
# 1. CLASE PLANIFICADOR
class Planificador:
    """Gestiona la ejecución de tareas programadas"""
    
    def __init__(self):
        self.tareas_diarias = []
        self.tareas_periodicas = []
        self.tareas_bajo_demanda = {}
        self.scheduler = APScheduler()
    
    def agregar_tarea_diaria(self, nombre, horario, comando):
        """Agrega tarea para ejecución diaria"""
        pass
    
    def agregar_tarea_periodica(self, nombre, intervalo_minutos, comando):
        """Agrega tarea para ejecución periódica"""
        pass
    
    def ejecutar(self):
        """Inicia el scheduler"""
        pass

# 2. CLASE MONITOR CONTINUO
class MonitorContinuo:
    """Monitorea errores en tiempo real"""
    
    def __init__(self):
        self.thread_monitor = None
        self.running = False
    
    def iniciar(self):
        """Inicia monitoreo en background"""
        pass
    
    def detener(self):
        """Detiene monitoreo"""
        pass
    
    def procesar_errores(self):
        """Procesa errores detectados"""
        pass

# 3. CLASE GESTOR DE EJECUCIONES
class GestorEjecuciones:
    """Registra y gestiona las ejecuciones"""
    
    def __init__(self):
        self.historial = []
        self.estadisticas = {}
    
    def registrar_ejecucion(self, nombre, resultado, duracion):
        """Registra una ejecución"""
        pass
    
    def generar_reporte(self):
        """Genera reporte de ejecuciones"""
        pass

# 4. CLASE RECUPERACIÓN
class GestorRecuperacion:
    """Gestiona errores y reintentos"""
    
    def __init__(self):
        self.reintentos_pendientes = []
        self.fallback_tasks = {}
    
    def agregar_reintento(self, tarea, intento=1):
        """Agrega tarea a cola de reintentos"""
        pass
    
    def procesar_reintentos(self):
        """Procesa tareas pendientes de reintento"""
        pass

# 5. INTERFAZ DE CONTROL
class InterfazControl:
    """Proporciona interfaz de control y monitoreo"""
    
    def menu_interactivo(self):
        """Menú interactivo en consola"""
        pass
    
    def mostrar_estado(self):
        """Muestra estado actual del sistema"""
        pass
    
    def ejecutar_comando(self, comando):
        """Ejecuta comando manualmente"""
        pass
```

---

## FLUJO DE EJECUCIÓN ESPERADO

```
INICIO (maestro.py)
│
├─→ 1. INICIALIZACIÓN
│   ├─→ Cargar config desde config.py
│   ├─→ Ejecutar verificar_sistema.py
│   ├─→ Establecer conexión DB2
│   ├─→ Inicializar logging
│   └─→ Mostrar "Sistema SAC Iniciado ✅"
│
├─→ 2. CONFIGURAR PLANIFICADOR
│   ├─→ Agregar 4 tareas diarias
│   ├─→ Agregar tareas preventivas (cada 15 min)
│   ├─→ Agregar tareas horarias (cada hora)
│   └─→ Mostrar próximas tareas programadas
│
├─→ 3. INICIAR MONITOREO EN BACKGROUND
│   ├─→ Thread de monitor.py corriendo
│   ├─→ Chequea errores CRÍTICO
│   └─→ Alertas inmediatas si hay problemas
│
├─→ 4. MOSTRAR MENÚ DE CONTROL
│   ├─→ Opción 1: Ver estado actual
│   ├─→ Opción 2: Ejecutar tarea manual
│   ├─→ Opción 3: Ver próximas ejecuciones
│   ├─→ Opción 4: Ver últimas ejecuciones
│   ├─→ Opción 5: Cambiar configuración
│   ├─→ Opción 6: Ver logs
│   └─→ Opción 0: Salir
│
├─→ 5. BUCLE PRINCIPAL (while running)
│   ├─→ Cada 1 segundo
│   │   ├─→ Chequear si hay tareas pendientes
│   │   ├─→ Ejecutar tareas vencidas
│   │   └─→ Capturar comandos del usuario
│   └─→ Si error crítico
│       ├─→ Alertar Telegram inmediato
│       ├─→ Enviar email
│       └─→ Registrar en log
│
└─→ 6. FINALIZACIÓN (Ctrl+C o comando exit)
    ├─→ Detener monitoreo background
    ├─→ Generar reporte final
    ├─→ Cerrar conexiones
    └─→ Mostrar "Sistema SAC Detenido"
```

---

## CONSIDERACIONES IMPORTANTES

### 1. CONCURRENCIA Y THREADS

```python
# Estructura con threading:
├─ Main Thread
│  ├─ Planificador de tareas
│  ├─ Menú interactivo
│  └─ Bucle principal
│
└─ Background Threads
   ├─ Monitor en tiempo real
   ├─ Procesador de alertas
   ├─ Gestor de reintentos
   └─ Actualizador de dashboard
```

### 2. MANEJO DE ERRORES

```python
# Estrategias de recuperación:
1. Error en OC específica → Reintento 1 vez
2. Error en query → Reintento 2 veces + fallback local
3. Error de conexión DB2 → Usar DB local + alerta
4. Error en email → Guardar en cola para reintentar
5. Error en Telegram → Log y continuar
6. Error no recuperable → Alerta crítica + parar tarea
```

### 3. LOGGING CENTRALIZADO

```python
# Estructura de logs:
logs/
├── maestro.log (principal)
├── ejecuciones.log (historial detallado)
├── errores.log (solo errores)
├── alertas.log (alertas CRÍTICO)
└── diario/
    ├── 20250121.log
    ├── 20250122.log
    └── ...
```

### 4. ALMACENAMIENTO DE ESTADO

```python
# Archivo JSON para estado persistente:
state/
└── maestro_estado.json
    {
        "ultima_ejecucion": "2025-01-21 23:00:00",
        "proximas_tareas": [...],
        "tareas_ejecutadas_hoy": 4,
        "errores_detectados": 2,
        "alertas_criticas": 0,
        "uptime_segundos": 3600
    }
```

---

## DEPENDENCIAS EXTERNAS PARA SCRIPT MAESTRO

```python
# requirements_maestro.txt
apscheduler>=3.10.0  # Planificador de tareas
pytz>=2024.1         # Manejo de zonas horarias
schedule>=1.2.0      # Alternativa a APScheduler
psutil>=5.9.0        # Monitoreo de sistema
tabulate>=0.9.0      # Tablas en consola
colorama>=0.4.6      # Colores en terminal
```

---

## EJEMPLO DE EJECUCIÓN

```bash
$ python maestro.py

╔══════════════════════════════════════════════════════════════╗
║    SISTEMA SAC - MAESTRO DE ORQUESTACIÓN v1.0               ║
║    CEDIS Cancún 427 - Chedraui                              ║
╚══════════════════════════════════════════════════════════════╝

✅ Configuración cargada correctamente
✅ Verificación de sistema completada
✅ Conexión a DB2 establecida
✅ Inicialización de logging completada
✅ Monitor en tiempo real iniciado

📋 PRÓXIMAS EJECUCIONES:
├─ 06:00 AM (en 23 horas) - Reporte Planning Diario
├─ 09:00 AM (en 26 horas) - Validación OCs Vencidas
├─ 18:00 PM (en 35 horas) - Resumen Ejecutivo
├─ 23:00 PM (en 40 horas) - Limpieza y Backup
└─ [Cada 15 min] - Chequeos Preventivos

📊 ESTADO DEL SISTEMA:
├─ Uptime: 0 días, 0 horas, 5 minutos
├─ Ejecuciones hoy: 0
├─ Errores detectados: 0
├─ Alertas críticas: 0
└─ Dashboard: http://localhost:5000

═══════════════════════════════════════════════════════════════

MENÚ DE CONTROL:
1. Ver estado actual del sistema
2. Ejecutar tarea manual
3. Ver próximas ejecuciones programadas
4. Ver historial de ejecuciones
5. Cambiar configuración
6. Ver logs en tiempo real
0. Salir

Seleccione opción: █
```

---

## RESUMEN DE BENEFICIOS DEL SCRIPT MAESTRO

✅ **Centralización**: Un único punto de control para TODO el sistema
✅ **Automatización**: Ejecución automática de tareas diarias
✅ **Monitoreo 24/7**: Detección y alertas en tiempo real
✅ **Recuperación**: Reintentos automáticos y fallback strategies
✅ **Visibilidad**: Dashboard, logs y reportes completos
✅ **Control**: Menú interactivo para ejecución manual
✅ **Escalabilidad**: Fácil agregar nuevas tareas
✅ **Confiabilidad**: Manejo robusto de errores
✅ **Auditoría**: Registro completo de todas las ejecuciones
✅ **Notificaciones**: Alertas instantáneas en Telegram + Email

---

