# 🤖 AGENTE SAC SIEMPRE ACTIVO

## Sistema de Automatización de Consultas - CEDIS Cancún 427

**Versión:** 1.0.0
**Estado:** Production Ready
**Última Actualización:** Noviembre 2025

---

## 📋 TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Características Principales](#características-principales)
3. [Arquitectura](#arquitectura)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Formas de Invocación](#formas-de-invocación)
6. [Modos de Operación](#modos-de-operación)
7. [Modo Copiloto Automático](#modo-copiloto-automático)
8. [Configuración de Autonomía](#configuración-de-autonomía)
9. [Tareas Autónomas](#tareas-autónomas)
10. [Monitoreo y Estadísticas](#monitoreo-y-estadísticas)
11. [API REST](#api-rest-futuro)
12. [Troubleshooting](#troubleshooting)
13. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 INTRODUCCIÓN

El **Agente SAC Siempre Activo** es una extensión inteligente del Sistema de Automatización de Consultas que funciona **24/7 en segundo plano**, proporcionando asistencia automática a los analistas del departamento de Planning.

### Filosofía

> "Las máquinas y los sistemas al servicio de los analistas"

El agente respeta la autoridad de los usuarios humanos mientras proporciona automatización inteligente que:
- ✅ Reduce trabajo manual repetitivo
- ✅ Detiene errores antes de que ocurran
- ✅ Escala automáticamente en períodos de inactividad
- ✅ Aprende patrones de trabajo del usuario

---

## 🌟 CARACTERÍSTICAS PRINCIPALES

### 1. **Funcionamiento Continuo (24/7)**
- Se ejecuta constantemente en segundo plano
- No interfiere con el trabajo normal del usuario
- Se adapta automáticamente a los patrones de actividad

### 2. **Detección Automática de Inactividad**
- Monitorea actividad del usuario en tiempo real
- Activa automáticamente "modo copiloto" tras 30 minutos sin respuesta
- Sensible a diferentes tipos de actividad

### 3. **Modo Copiloto Inteligente**
```
Usuario ACTIVO        → Modo Normal (espera comandos)
       ↓ (30 min sin actividad)
Usuario INACTIVO      → Modo Copiloto (actúa automáticamente)
       ↓ (actividad detectada)
Usuario ACTIVO NUEVAMENTE → Regresa a Modo Normal
```

### 4. **Autonomía Condicional**
- ✅ Ejecuta automáticamente tareas preautorizadas
- ⚠️ Solicita confirmación cuando hay usuario activo
- 🔒 Respeta límites de seguridad configurables
- 📋 Registra todas las acciones para auditoría

### 5. **Múltiples Formas de Invocación**
- 💻 CLI (línea de comandos)
- 🌐 API HTTP REST
- 📅 Tareas programadas
- 🎤 Voz (futuro)
- 📱 Aplicación móvil (futuro)

### 6. **Comunicación Interdepartamental**
- Sincroniza información entre departamentos
- Envía alertas automáticas
- Genera reportes sin intervención

### 7. **Monitoreo Proactivo**
- Verifica salud del sistema continuamente
- Detecta problemas antes de que afecten operaciones
- Sugiere acciones correctivas

---

## 🏗️ ARQUITECTURA

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│         AGENTE SAC SIEMPRE ACTIVO (v1.0)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Núcleo Principal (AgenteSACSimpreActivo)       │  │
│  │  - Orquestación de componentes                  │  │
│  │  - Gestión de estado global                     │  │
│  │  - Callbacks de eventos                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Monitor de Inactividad                          │  │
│  │ - Detecta ausencia de usuario                   │  │
│  │ - Registra eventos de actividad                 │  │
│  │ - Calcula tiempo sin respuesta                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Autorizador Autónomo                            │  │
│  │ - Determina qué puede ejecutar                  │  │
│  │ - Evalúa niveles de autonomía                   │  │
│  │ - Respeta horarios laborales                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Motor de Tareas Autónomas                       │  │
│  │ - Cola de tareas con prioridades                │  │
│  │ - Ejecución paralela controlada                 │  │
│  │ - Callbacks para tipos específicos              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Integración con AgenteSAC Existente             │  │
│  │ - Reutiliza respuestas rápidas                  │  │
│  │ - Accede a conocimiento del agente              │  │
│  │ - Mantiene compatibilidad total                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Sistema de Eventos y Auditoría                  │  │
│  │ - Registra todo automáticamente                 │  │
│  │ - Proporciona trazabilidad completa             │  │
│  │ - Estadísticas en tiempo real                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Hilos de Ejecución

| Hilo | Función | Intervalo |
|------|---------|-----------|
| Monitor Inactividad | Detecta ausencia de usuario | 1 min |
| Procesador Tareas | Ejecuta tareas autónomas | 15 min |
| Verificador Salud | Chequea estado del sistema | 1 min |
| Monitor Principal | Mantiene agente activo | Continuo |

---

## 📦 INSTALACIÓN Y CONFIGURACIÓN

### Requisitos Previos

- **Python:** 3.8 o superior
- **Sistema Operativo:** Windows 10+, Linux, macOS
- **Dependencias:** Las mismas que SAC base (ver `requirements.txt`)
- **Permisos:** Acceso a `output/logs/` para escribir logs

### Pasos de Instalación

#### 1. Verificar Instalación Base

```bash
# Verificar que SAC está instalado correctamente
python verificar_sistema.py

# O ejecutar health check
python health_check.py
```

#### 2. Crear Configuración (Opcional)

```bash
# Crear archivo de configuración de ejemplo
python scripts/iniciar_agente_siempre_activo.py --config-ejemplo

# Editar si es necesario
cat config/agente_siempre_activo.json
```

#### 3. Hacer Script Ejecutable (Linux/Mac)

```bash
chmod +x scripts/iniciar_agente_siempre_activo.py
chmod +x scripts/iniciar_agente_siempre_activo.sh
```

#### 4. Instalar en Startup (Opcional)

**Windows:**
```
1. Crear acceso directo a scripts/iniciar_agente_siempre_activo.bat
2. Mover a: C:\Users\<usuario>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

**Linux (con cron):**
```bash
# Agregar a crontab
crontab -e

# Agregar línea:
@reboot /usr/bin/python3 /ruta/a/SAC_V01_427_ADMJAJA/scripts/iniciar_agente_siempre_activo.py --daemon

# O con nohup:
@reboot nohup python3 /ruta/scripts/iniciar_agente_siempre_activo.py --daemon > /tmp/agente_sac.log 2>&1 &
```

**macOS (con launchd):**
```bash
# Crear plist (ver template disponible)
# Colocar en: ~/Library/LaunchAgents/
# Cargar con: launchctl load ~/Library/LaunchAgents/com.chedraui.agente-sac.plist
```

---

## 🚀 FORMAS DE INVOCACIÓN

### 1. Modo Interactivo (Default)

```bash
# Inicia con interfaz interactiva
python scripts/iniciar_agente_siempre_activo.py

# O simplemente:
python -m modules.agente_siempre_activo
```

**Comandos disponibles:**
```
ayuda           - Muestra esta ayuda
estado          - Estado actual del agente
copiloto        - Info del modo copiloto
tareas          - Tareas pendientes
eventos         - Últimos eventos registrados
salir           - Termina el programa
```

### 2. Modo Daemon (Background)

```bash
# Inicia sin interfaz, en segundo plano
python scripts/iniciar_agente_siempre_activo.py --daemon

# Windows:
scripts\iniciar_agente_siempre_activo.bat --daemon
```

**Ideal para:**
- Ejecutar como servicio del sistema
- Instalar en startup
- Automatización no interactiva

### 3. Consultar Estado

```bash
python scripts/iniciar_agente_siempre_activo.py --estado

# Salida esperada:
# ═══════════════════════════════════════════════════════════════
# 📊 ESTADO DEL AGENTE SAC SIEMPRE ACTIVO
# ═══════════════════════════════════════════════════════════════
#
# 🤖 Información General:
#    Versión: 1.0.0
#    Activo: ✅ Sí
#    Timestamp: 2025-11-22T14:30:45.123456
#
# 🔄 Modo Copiloto:
#    Estado: desactivado
#    Tiempo Inactivo: 0:05:23
#    Tareas Pendientes: 0
#
# ...
```

### 4. Configuración Personalizada

```bash
# Con timeout personalizado
python scripts/iniciar_agente_siempre_activo.py --timeout-minutos 45

# Con nivel de autonomía
python scripts/iniciar_agente_siempre_activo.py --nivel-autonomia media

# Combinados
python scripts/iniciar_agente_siempre_activo.py \
    --daemon \
    --timeout-minutos 20 \
    --nivel-autonomia basica
```

### 5. Script Batch (Windows)

```batch
REM Modo interactivo
iniciar_agente_siempre_activo.bat

REM Modo daemon
iniciar_agente_siempre_activo.bat --daemon

REM Ver estado
iniciar_agente_siempre_activo.bat --estado

REM Ayuda
iniciar_agente_siempre_activo.bat --ayuda
```

### 6. API HTTP REST (Futuro)

```bash
# Obtener estado
curl http://localhost:5000/agente/estado

# Registrar actividad
curl -X POST http://localhost:5000/agente/actividad \
  -H "Content-Type: application/json" \
  -d '{"usuario": "username", "tipo": "interaccion"}'

# Agregar tarea
curl -X POST http://localhost:5000/agente/tarea \
  -H "Content-Type: application/json" \
  -d '{"tipo": "generacion_reporte", "prioridad": 8}'
```

---

## 🔄 MODOS DE OPERACIÓN

### Modo Normal (Interactivo)

**Estado:** Usuario está trabajando activamente

```
Comportamiento:
├── Espera comandos/interacciones del usuario
├── No ejecuta tareas automáticas
├── Registra cada interacción
├── Resetea el timer de inactividad
└── Disponible para ayuda inmediata
```

**Transición a Copiloto:** Tras 30 minutos sin actividad

### Modo Copiloto (Automático)

**Estado:** Usuario ausente o inactivo por 30+ minutos

```
Comportamiento:
├── Activa automáticamente
├── Ejecuta tareas preautorizadas
├── No requiere confirmación del usuario
├── Toma decisiones basadas en reglas
├── Notifica al usuario si lo desea
├── Registra todas las acciones
└── Detenerse si detecta actividad
```

**Transición a Normal:** Cuando se detecta actividad del usuario

**Ejemplos de tareas en modo copiloto:**
- 📈 Generar reportes diarios
- ✅ Validar órdenes de compra pendientes
- 📧 Enviar alertas configuradas
- 🔍 Verificar salud del sistema
- 📝 Limpiar logs antiguos

### Modo Daemon (Servicio)

**Estado:** Ejecuta como servicio sin interfaz

```
Comportamiento:
├── Sin interfaz interactiva visible
├── Se ejecuta en segundo plano
├── Logs en archivo (output/logs/...)
├── Ideal para servers/automatización
├── Inicia con el sistema operativo
└── Monitoreo continuo sin intervención
```

### Modo Vigilancia (Monitor)

**Estado:** Solo monitorea, no ejecuta acciones

```
Comportamiento:
├── Observa eventos del sistema
├── Registra todas las anomalías
├── Notifica de problemas
├── No toma decisiones automáticas
├── Útil para auditoría/compliance
└── Nivel de autonomía MINIMA
```

---

## 🤖 MODO COPILOTO AUTOMÁTICO

### Activación Automática

El copiloto se **activa automáticamente** después de 30 minutos sin actividad del usuario.

```timeline
00:00 - Usuario interactúa          ✅ Timer reinicia
00:15 - Usuario sigue activo        ✅ Timer continúa
00:30 - Inactividad detectada       ⏰ Alerta a 30 min
01:00 - 🤖 COPILOTO SE ACTIVA
      - Notifica al usuario si está configurado
      - Comienza tareas autorizadas
      - Monitorea eventos
01:30 - Usuario regresa             👤 Timer reinicia
```

### Tipos de Tareas en Copiloto

| Tarea | Riesgo | Auto? | Notificación |
|-------|--------|-------|--------------|
| Generación de Reporte | Bajo | ✅ | Opcional |
| Validación OC | Bajo | ✅ | Opcional |
| Envío de Alerta | Bajo | ✅ | Sí |
| Notificación | Bajo | ✅ | N/A |
| Verificación Salud | Bajo | ✅ | Opcional |
| Comunicación Interdept | Medio | ✅ | Sí |
| Limpieza Logs | Bajo | ✅ | No |
| Decisión Operativa | Alto | ❌ | **Requiere confirmación** |

### Notificación de Activación

Cuando se activa el copiloto, se puede notificar por:
- 📧 Email
- 📱 Telegram (si configurado)
- 💬 WhatsApp (si configurado)
- 📋 Log local

Configurar en `config/agente_siempre_activo.json`:
```json
{
  "notificaciones": {
    "al_activar_copiloto": true,
    "canal_predeterminado": "email"
  }
}
```

---

## 🔒 CONFIGURACIÓN DE AUTONOMÍA

### Niveles de Autonomía

#### 1. MINIMA
```
Acciones permitidas:
  ✅ Generar alertas
  ✅ Enviar notificaciones
  ❌ Ejecutar tareas
  ❌ Cambiar configuración

Uso: Auditoría, monitoreo solo lectura
```

#### 2. BASICA (Recomendado)
```
Acciones permitidas:
  ✅ Generar reportes
  ✅ Validar OC
  ✅ Enviar alertas
  ✅ Notificar
  ✅ Verificar salud
  ⚠️ Requiere confirmación si hay usuario

Uso: Producción normal con supervisión
```

#### 3. MEDIA
```
Acciones permitidas:
  ✅ Todas las de BASICA
  ✅ Comunicación interdepartamental
  ✅ Limpieza automática
  ⚠️ Solicita confirmación en horario laboral

Uso: Operaciones extendidas con control
```

#### 4. ALTA
```
Acciones permitidas:
  ✅ Todas las anteriores
  ✅ Decisiones operativas autorizadas
  ✅ Sin confirmación en horario no laboral
  ⚠️ Requiere confirmación en horario laboral

Uso: Casos muy específicos, con máxima confianza
```

### Configurar Nivel de Autonomía

**Por línea de comandos:**
```bash
# Nivel BASICA
python scripts/iniciar_agente_siempre_activo.py --nivel-autonomia basica

# Nivel MEDIA
python scripts/iniciar_agente_siempre_activo.py --nivel-autonomia media

# Nivel ALTA
python scripts/iniciar_agente_siempre_activo.py --nivel-autonomia alta
```

**En archivo de configuración:**
```json
{
  "copiloto": {
    "nivel_autonomia": "media",
    "tareas_autorizadas": [
      "generacion_reporte",
      "validacion_oc",
      "envio_alerta",
      "comunicacion_interdept"
    ]
  }
}
```

### Horario No Laboral (Mayor Autonomía)

El agente puede tener mayor autonomía fuera del horario laboral:

```json
{
  "copiloto": {
    "horario_no_laboral": {
      "inicio": "22:00",
      "fin": "08:00"
    }
  }
}
```

En horario no laboral (22:00-08:00):
- ✅ Autonomía aumentada
- ✅ Menos solicitudes de confirmación
- ✅ Tareas más complejas permitidas

En horario laboral (08:00-22:00):
- ⚠️ Más cuidadoso
- ⚠️ Solicita confirmación para tareas riesgosas
- ⚠️ Respeta preferencias del usuario activo

---

## 📋 TAREAS AUTÓNOMAS

### Tipos de Tareas Disponibles

```python
TipoTareaAutonoma = {
    'GENERACION_REPORTE': 'generar_reporte',
    'VALIDACION_OC': 'validacion_oc',
    'SINCRONIZACION_DATOS': 'sincronizacion_datos',
    'ENVIO_ALERTA': 'envio_alerta',
    'NOTIFICACION': 'notificacion',
    'COMUNICACION_INTERDEPT': 'comunicacion_interdept',
    'LIMPIEZA_LOGS': 'limpieza_logs',
    'VERIFICACION_SALUD': 'verificacion_salud',
}
```

### Estructura de Tarea

```python
{
    'id': 'tarea_unique_id',
    'tipo': 'generacion_reporte',
    'descripcion': 'Generar reporte diario de validaciones',
    'parametros': {
        'fecha': '2025-11-22',
        'cedis': '427',
        'formato': 'xlsx'
    },
    'prioridad': 8,  # 1-10, 10 es máxima
    'requiere_confirmacion': False
}
```

### Registrar Callbacks Personalizados

```python
from modules.agente_siempre_activo import obtener_agente_siempre_activo, TipoTareaAutonoma

agente = obtener_agente_siempre_activo()

# Registrar callback personalizado
def generar_reporte_diario(parametros):
    # Tu código aquí
    return {"status": "success", "archivo": "reporte.xlsx"}

agente.motor_tareas.registrar_callback(
    TipoTareaAutonoma.GENERACION_REPORTE,
    generar_reporte_diario
)
```

### Agregar Tarea Manual

```python
from modules.agente_siempre_activo import TareaAutonoma, TipoTareaAutonoma

tarea = TareaAutonoma(
    id='mi_tarea_001',
    tipo=TipoTareaAutonoma.VALIDACION_OC,
    descripcion='Validar OC 750384000001',
    parametros={'oc_numero': '750384000001'},
    prioridad=9
)

agente.motor_tareas.agregar_tarea(tarea)
```

---

## 📊 MONITOREO Y ESTADÍSTICAS

### Obtener Estado Actual

```python
from modules.agente_siempre_activo import obtener_agente_siempre_activo

agente = obtener_agente_siempre_activo()
estado = agente.obtener_estado()

print(f"Estado del copiloto: {estado['estado_copiloto']}")
print(f"Tiempo inactivo: {estado['tiempo_inactivo']}")
print(f"Tareas pendientes: {estado['tareas_pendientes']}")
```

### Estadísticas del Agente

```python
stats = agente.estadisticas

print(f"Total tareas ejecutadas: {stats.total_tareas_ejecutadas}")
print(f"Total errores: {stats.total_errores}")
print(f"Modo copiloto activaciones: {stats.modo_copiloto_activaciones}")
print(f"Tiempo total en copiloto: {stats.tiempo_en_copiloto_total}s")
```

### Eventos Registrados

```python
# Obtener últimos 10 eventos
ultimos_eventos = agente.eventos[-10:]

for evento in ultimos_eventos:
    print(f"{evento.timestamp} - {evento.tipo.value} ({evento.severidad})")
    print(f"  Detalles: {evento.detalles}")
```

### Información de Tareas

```python
# Tareas pendientes
tareas_pendientes = agente.motor_tareas.tareas_pendientes
print(f"Pendientes: {len(tareas_pendientes)}")

# Tareas completadas
tareas_completadas = agente.motor_tareas.tareas_completadas
print(f"Completadas: {len(tareas_completadas)}")

# Próxima tarea
proxima = agente.motor_tareas.obtener_proxima_tarea()
if proxima:
    print(f"Próxima: {proxima.tipo.value} (prioridad: {proxima.prioridad})")
```

### Logs y Auditoría

Los logs se guardan en:
```
output/logs/agente_siempre_activo.log
```

Configurar nivel de log:
```json
{
  "logging": {
    "nivel": "INFO",
    "archivo": "output/logs/agente_siempre_activo.log"
  }
}
```

Niveles disponibles:
- `DEBUG` - Información detallada (para desarrollo)
- `INFO` - Información general (recomendado)
- `WARNING` - Advertencias
- `ERROR` - Errores
- `CRITICAL` - Errores críticos

---

## 🌐 API REST (Futuro)

La API HTTP REST está en fase de desarrollo y estará disponible en v1.1.0.

**Endpoints planeados:**

```
GET /agente/estado
  Obtiene estado actual del agente

GET /agente/estadisticas
  Obtiene estadísticas detalladas

GET /agente/eventos
  Obtiene eventos registrados

POST /agente/actividad
  Registra actividad del usuario

POST /agente/tarea
  Agrega una tarea a ejecutar

GET /agente/configuracion
  Obtiene configuración actual

PUT /agente/configuracion
  Actualiza configuración
```

Para habilitar (cuando esté disponible):
```json
{
  "api_rest": {
    "habilitada": true,
    "puerto": 5000,
    "host": "127.0.0.1"
  }
}
```

---

## 🔧 TROUBLESHOOTING

### Problema: El agente no inicia

**Síntomas:**
```
❌ Error: No se puede importar módulo
```

**Soluciones:**
```bash
# 1. Verificar Python
python --version  # Debe ser 3.8+

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar archivos
ls -la modules/agente_siempre_activo.py
ls -la modules/agente_sac.py

# 4. Ver error detallado
python -u scripts/iniciar_agente_siempre_activo.py 2>&1 | head -50
```

### Problema: El copiloto nunca se activa

**Síntomas:**
```
estado_copiloto: desactivado
(incluso tras 30+ min sin actividad)
```

**Soluciones:**
```bash
# 1. Verificar configuración
python -c "from modules.agente_siempre_activo import ConfiguracionCopiloto; print(ConfiguracionCopiloto().habilitado)"

# 2. Registrar actividad manualmente
python scripts/iniciar_agente_siempre_activo.py  # En otro terminal
# En otro terminal:
python -c "
from modules.agente_siempre_activo import obtener_agente_siempre_activo
agente = obtener_agente_siempre_activo()
print(agente.obtener_estado())
"

# 3. Revisar logs
tail -f output/logs/agente_siempre_activo.log
```

### Problema: Tareas no se ejecutan

**Síntomas:**
```
tareas_pendientes: 1
(pero no se ejecutan)
```

**Soluciones:**
```bash
# 1. Verificar callbacks registrados
python -c "
from modules.agente_siempre_activo import obtener_agente_siempre_activo
agente = obtener_agente_siempre_activo()
print('Callbacks:', agente.motor_tareas.callbacks)
"

# 2. Revisar logs de ejecución
grep -i "ejecutando tarea" output/logs/agente_siempre_activo.log

# 3. Verificar estado copiloto
python scripts/iniciar_agente_siempre_activo.py --estado
```

### Problema: Alto uso de CPU

**Síntomas:**
```
CPU 70-100% consistentemente
```

**Soluciones:**
```bash
# 1. Aumentar intervalo de chequeo
# En config/agente_siempre_activo.json:
{
  "inactividad": {
    "intervalo_chequeo_segundos": 120  # Aumentar a 120s
  }
}

# 2. Reducir frecuencia de verificación de salud
{
  "verificacion_salud": {
    "intervalo_minutos": 10  # Aumentar a 10 min
  }
}

# 3. Limitar tareas paralelas
{
  "tareas_autonomas": {
    "max_tareas_simultaneas": 1
  }
}
```

### Problema: Logs muy grandes

**Síntomas:**
```
output/logs/agente_siempre_activo.log > 100MB
```

**Soluciones:**
```bash
# 1. Configurar rotación
{
  "logging": {
    "tamaño_maximo_mb": 10,
    "backup_count": 5
  }
}

# 2. Limpiar logs manualmente
rm output/logs/agente_siempre_activo.log*

# 3. Reducir nivel de logging
{
  "logging": {
    "nivel": "WARNING"  # En lugar de INFO
  }
}
```

---

## ❓ PREGUNTAS FRECUENTES

### ¿Cómo detengo el agente?

```bash
# Si está en modo interactivo
Presiona Ctrl+C o escribe "salir"

# Si está en background
# Windows:
taskkill /IM python.exe /F

# Linux/Mac:
pkill -f "iniciar_agente_siempre_activo"
ps aux | grep "agente"  # Para encontrar el PID
kill -9 <PID>
```

### ¿Puedo tener múltiples instancias del agente?

**No recomendado.** La arquitectura está diseñada para una sola instancia. Si necesitas múltiples agentes:
- Considera ejecutar en máquinas diferentes
- O usar niveles de autonomía más bajos
- O configurar horarios no superpuestos

### ¿Qué pasa si hay un error en una tarea automática?

El agente:
1. ✅ Registra el error en logs
2. ✅ Incrementa contador de errores
3. ✅ Notifica si está configurado
4. ✅ Continúa procesando otras tareas
5. ✅ **NO detiene** el agente

### ¿El agente puede acceder a datos sensibles?

✅ **Sí, con precauciones:**
- Usa credenciales de `config/.env` como cualquier módulo SAC
- Registra auditoría de todas las acciones
- Respeta límites de autonomía configurados
- Nunca ejecuta acciones no autorizadas explícitamente

### ¿Es seguro dejar corriendo 24/7?

✅ **Sí:**
- Está diseñado para ejecución continua
- Autolimpieza de recursos
- Manejo de errores robusto
- Logs de auditoría completos
- Puede detenerse limpiamente en cualquier momento

### ¿Puedo personalizar las tareas que ejecuta?

✅ **Sí, de varias formas:**
```python
# 1. Registrar callbacks personalizados
agente.motor_tareas.registrar_callback(tipo, mi_funcion)

# 2. Crear archivo de config personalizado
# Editar config/agente_siempre_activo.json

# 3. Extender la clase
class MiAgente(AgenteSACSimpreActivo):
    def _procesar_tareas_autonomas(self):
        # Tu código aquí
        pass
```

### ¿Cómo integro esto con mi aplicación?

```python
# Importar el agente
from modules.agente_siempre_activo import obtener_agente_siempre_activo

# Obtener instancia global
agente = obtener_agente_siempre_activo()

# Registrar actividad del usuario
agente.registrar_actividad_usuario('username', 'interaccion')

# Agregar tarea
agente.motor_tareas.agregar_tarea(mi_tarea)

# Obtener estado
estado = agente.obtener_estado()
```

### ¿Puedo resetear el agente?

Para limpiar completamente:

```bash
# 1. Detener el agente actual
python scripts/iniciar_agente_siempre_activo.py --estado
# Ctrl+C si está corriendo

# 2. Limpiar archivos de estado (opcional)
rm -rf output/agente_sac/  # Eventos, etc.

# 3. Reiniciar
python scripts/iniciar_agente_siempre_activo.py
```

---

## 📞 SOPORTE Y CONTACTO

**Equipo de Sistemas CEDIS 427**

- **Jefe de Sistemas:** Julián Alexander Juárez Alvarado (ADMJAJA)
- **Email:** sistemas@chedraui.com.mx
- **Sistemas Analistas:** Larry Adanael Basto Díaz, Adrian Quintana Zuñiga

**Supervisión Regional**
- **Itza Vera Reyes Sarubí** (Villahermosa)

---

## 📄 LICENCIA

© 2025 Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados

Este software es parte del Sistema SAC y está destinado exclusivamente para uso interno del CEDIS Cancún 427.

---

## 🚀 PRÓXIMAS CARACTERÍSTICAS

**Versión 1.1.0 (Q1 2026):**
- ✅ API HTTP REST completa
- ✅ Dashboard web de monitoreo
- ✅ Integración con Telegram/WhatsApp
- ✅ Machine Learning para predicción de tareas
- ✅ Reporte analítico automático

**Versión 1.2.0 (Q2 2026):**
- ✅ Interfaz gráfica de desktop
- ✅ Reconocimiento de voz
- ✅ Integración con calendario
- ✅ Colaboración multi-usuario
- ✅ Sincronización en la nube

---

**Última revisión:** 22 de Noviembre, 2025
**Estado:** Production Ready v1.0.0
