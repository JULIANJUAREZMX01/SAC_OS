# 🔌 Sistema Modular de APIs - SAC

> Sistema de integración de APIs externas para el Sistema de Automatización de Consultas

---

## 📋 Descripción General

El módulo `api` proporciona un sistema modular y extensible para integrar APIs externas que agregan capacidades, recursos y beneficios a las operaciones de SAC.

### Características

- ✅ **Arquitectura modular**: Fácil adición de nuevas APIs
- ✅ **Cache inteligente**: Reduce llamadas y mejora rendimiento
- ✅ **Retry automático**: Backoff exponencial para resiliencia
- ✅ **Métricas integradas**: Monitoreo de uso y rendimiento
- ✅ **Health checks**: Verificación de disponibilidad
- ✅ **Fallbacks**: Datos de respaldo cuando fallan APIs

---

## 🚀 APIs Activas

### 1. 📅 CalendarAPI - Calendario Mexicano

Proporciona información sobre el calendario laboral mexicano.

**Funcionalidades:**
- Días festivos oficiales (Ley Federal del Trabajo)
- Cálculo de días hábiles
- Semana Santa (calculada dinámicamente)
- Días móviles (lunes de puentes)

**Uso:**
```python
from modules.api import get_api

calendar = get_api('calendar')

# Verificar si es festivo
es_festivo = calendar.es_dia_festivo('2025-12-25')

# Contar días hábiles
dias = calendar.contar_dias_habiles(fecha_inicio, fecha_fin)

# Sumar días hábiles
nueva_fecha = calendar.sumar_dias_habiles(fecha, 5)

# Obtener festivos del año
festivos = calendar.obtener_festivos_anio(2025)
```

**Beneficio SAC:** Planificación precisa de fechas de recepción y entregas.

---

### 2. 💱 ExchangeRateAPI - Tipo de Cambio

Tipos de cambio MXN/USD/EUR desde fuentes públicas.

**Funcionalidades:**
- Tipo de cambio actual
- Histórico de hasta 30 días
- Conversión entre monedas
- Variación diaria

**Fuentes:**
- Frankfurter API (basada en BCE)
- Datos de respaldo local

**Uso:**
```python
from modules.api import get_api

exchange = get_api('exchange_rate')

# Obtener USD/MXN
tc = exchange.obtener_usd_mxn()
print(f"1 USD = {tc.tasa:.4f} MXN")

# Convertir cantidad
mxn = exchange.convertir(100, 'USD', 'MXN')

# Obtener histórico
historico = exchange.obtener_historico('USD', dias=30)
```

**Beneficio SAC:** Cálculo de costos de importación y reportes financieros.

---

### 3. 🌤️ WeatherAPI - Clima para Logística

Pronóstico meteorológico para planificación de operaciones.

**Funcionalidades:**
- Clima actual
- Pronóstico hasta 16 días
- Alertas de condiciones adversas
- Evaluación de impacto logístico
- Múltiples ubicaciones (CEDIS región)

**Ubicaciones predefinidas:**
- CEDIS Cancún
- Villahermosa
- Mérida
- Chetumal
- Playa del Carmen

**Uso:**
```python
from modules.api import get_api

weather = get_api('weather')

# Clima actual en CEDIS
clima = weather.obtener_clima_actual('cancun')
print(f"{clima.emoji} {clima.temperatura}°C - {clima.condicion}")

# Pronóstico 7 días
pronostico = weather.obtener_pronostico_diario('cancun', dias=7)

# Verificar condiciones adversas
hay_alerta, alertas = weather.hay_condiciones_adversas()

# Resumen regional
resumen = weather.obtener_resumen_regional()
```

**Beneficio SAC:** Anticipar condiciones que afecten distribución y operaciones.

---

## 📊 Uso del Registry

El sistema incluye un registro centralizado de APIs:

```python
from modules.api import api_registry, get_api, list_apis, get_api_status

# Obtener una API
calendar = get_api('calendar')

# Listar todas las APIs
apis = list_apis()
for api in apis:
    print(f"- {api['nombre']}: {api['estado']}")

# Estado global
status = get_api_status()
print(f"APIs activas: {status['total_activas']}/{status['total_registradas']}")

# Health check global
resultados = api_registry.health_check_all()

# Métricas de uso
metricas = api_registry.get_all_metrics()
```

---

## 🔧 Configuración

### Variables de Entorno

Agregar a `.env`:

```bash
# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE APIs EXTERNAS
# ═══════════════════════════════════════════════════════════════

# Configuración global
API_CACHE_ENABLED=true
API_CACHE_TTL=300
API_TIMEOUT=30
API_MAX_RETRIES=3

# Weather API
# (Open-Meteo no requiere API key)

# Exchange Rate API
# (Frankfurter no requiere API key)

# Telegram Bot (para futuro)
# TELEGRAM_BOT_TOKEN=tu_token
# TELEGRAM_CHAT_IDS=id1,id2
```

### Archivo de Configuración

Ver `modules/api/config.py` para configuraciones detalladas de cada API.

---

## 🗺️ Roadmap de APIs Futuras

### Versión 1.1 (Próxima)

#### 📱 Telegram Bot API
**Prioridad:** Alta
**Estado:** Planificado
**Requiere:** Bot token y Chat IDs

**Funcionalidades planificadas:**
- Notificaciones push de alertas críticas
- Comandos interactivos (`/status`, `/reporte`)
- Resumen diario automatizado
- Confirmación de recepciones

```python
# Ejemplo de uso futuro
from modules.api import get_api

telegram = get_api('telegram')
telegram.enviar_alerta_critica("OC vencida: C750384123456")
telegram.enviar_resumen_diario(datos_resumen)
```

---

#### 🗺️ Geocoding API
**Prioridad:** Media
**Estado:** Planificado
**Requiere:** Ninguna (Nominatim es gratuito)

**Funcionalidades planificadas:**
- Validación de direcciones de entrega
- Cálculo de distancias
- Geocodificación de tiendas

---

#### 📊 QR/Barcode API
**Prioridad:** Media
**Estado:** Planificado
**Requiere:** Ninguna (librería local)

**Funcionalidades planificadas:**
- Generación de códigos de barras para LPNs
- Códigos QR para etiquetas
- Escaneo y validación

---

### Versión 2.0 (Futuro)

#### 🔗 SAP Integration API
**Prioridad:** Alta
**Estado:** Investigación
**Requiere:** Credenciales SAP, VPN corporativa

**Funcionalidades planificadas:**
- Sincronización de órdenes de compra
- Actualización de inventarios
- Consulta de proveedores
- Integración contable

```python
# Ejemplo de uso futuro
from modules.api import get_api

sap = get_api('sap')
oc_data = sap.obtener_orden_compra('4500123456')
sap.actualizar_recepcion(oc_numero, cantidad_recibida)
```

---

#### 📈 Power BI API
**Prioridad:** Media
**Estado:** Planificado
**Requiere:** Azure AD credentials, workspace ID

**Funcionalidades planificadas:**
- Push de datos a datasets
- Actualización de dashboards
- Embedding de reportes
- Alertas automatizadas

---

#### 🚛 Fleet Tracking API
**Prioridad:** Media
**Estado:** Investigación
**Requiere:** Contrato con proveedor GPS

**Funcionalidades planificadas:**
- Rastreo de unidades en tiempo real
- ETAs de entregas
- Histórico de rutas
- Alertas de retrasos

---

#### 💬 WhatsApp Business API
**Prioridad:** Baja
**Estado:** Evaluación
**Requiere:** Meta Business Account verificada

**Funcionalidades planificadas:**
- Comunicación con proveedores
- Confirmación de citas
- Notificaciones de recepción

---

## 🏗️ Agregar Nueva API

### 1. Crear el archivo del proveedor

```python
# modules/api/providers/mi_api.py

from ..base import BaseAPIClient, APIResponse, APIError

class MiAPI(BaseAPIClient):
    API_NAME = "MiAPI"
    API_VERSION = "1.0"
    API_DESCRIPTION = "Descripción de mi API"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inicialización específica

    def health_check(self) -> bool:
        # Implementar verificación
        return True

    def get_info(self) -> dict:
        return {
            'nombre': self.API_NAME,
            'version': self.API_VERSION,
            # ...
        }

    # Métodos específicos de la API
    def mi_metodo(self, param):
        # Implementación
        pass
```

### 2. Registrar en providers/__init__.py

```python
from .mi_api import MiAPI

__all__ = [
    # ...existentes
    'MiAPI',
]
```

### 3. Agregar al registry

```python
# En modules/api/registry.py, función _initialize_default_apis()

from .providers.mi_api import MiAPI
api_registry.register('mi_api', MiAPI, auto_init=True)
```

### 4. Agregar configuración

```python
# En modules/api/config.py

API_CONFIG = {
    # ...
    'mi_api': {
        'enabled': True,
        'cache_ttl_seconds': 300,
        # configuraciones específicas
    },
}
```

---

## 📈 Métricas y Monitoreo

Cada API registra automáticamente:

| Métrica | Descripción |
|---------|-------------|
| `total_requests` | Total de llamadas realizadas |
| `successful_requests` | Llamadas exitosas |
| `failed_requests` | Llamadas fallidas |
| `cache_hits` | Respuestas desde cache |
| `cache_misses` | Llamadas a la API real |
| `average_response_time_ms` | Tiempo promedio de respuesta |
| `success_rate` | Tasa de éxito (%) |
| `cache_hit_rate` | Tasa de aciertos de cache (%) |

```python
# Obtener métricas
from modules.api import get_api

api = get_api('weather')
metricas = api.get_metrics()
print(f"Tasa de éxito: {metricas['success_rate']}")
```

---

## 🔒 Consideraciones de Seguridad

1. **API Keys**: Almacenar siempre en `.env`, nunca en código
2. **Rate Limits**: Respetar límites de APIs externas
3. **Cache**: Usar cache para reducir llamadas
4. **Fallbacks**: Implementar datos de respaldo
5. **Timeouts**: Configurar timeouts apropiados
6. **Retry**: Usar backoff exponencial

---

## 📞 Soporte

**Desarrollado por:** Julián Alexander Juárez Alvarado (ADMJAJA)
**Cargo:** Jefe de Sistemas - CEDIS Cancún 427
**Email:** admjaja@chedraui.com.mx

---

**© 2025 Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados**
