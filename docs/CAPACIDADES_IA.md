# 🤖 CAPACIDADES DE INTELIGENCIA ARTIFICIAL - SISTEMA SAC

> **Guía completa de integración con modelos de lenguaje**
>
> Versión: 1.0.0
> Fecha: Noviembre 2025
> Sistema: SAC V1 - CEDIS Cancún 427

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Nuevos Módulos de IA](#nuevos-módulos-de-ia)
3. [Proveedores Soportados](#proveedores-soportados)
4. [Capacidades Principales](#capacidades-principales)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Integración en Flujos Existentes](#integración-en-flujos-existentes)
7. [Configuración](#configuración)
8. [Casos de Uso](#casos-de-uso)
9. [Limitaciones y Consideraciones](#limitaciones-y-consideraciones)

---

## 📌 RESUMEN EJECUTIVO

El sistema SAC ha sido potenciado con capacidades avanzadas de **Inteligencia Artificial** que permiten:

✨ **Análisis Inteligente**: Interpretación automática de datos de OC y distribuciones
🤖 **Asistente Conversacional**: Interacción natural en lenguaje español
📊 **Reportes Inteligentes**: Generación automática con insights y recomendaciones
🔍 **Detección de Anomalías**: Identificación de patrones anómalos usando IA
💡 **Recomendaciones Automáticas**: Sugerencias basadas en análisis de datos

---

## 🆕 NUEVOS MÓDULOS DE IA

### 1. `modules/integracion_llm.py` (600+ líneas)

**Propósito**: Integración central con APIs de modelos de lenguaje.

**Características**:
- ✅ Soporte para OpenAI (GPT-3.5, GPT-4)
- ✅ Soporte para Anthropic (Claude)
- ✅ Interfaz uniforme para múltiples proveedores
- ✅ Tracking de tokens y costos
- ✅ Análisis de datos
- ✅ Clasificación automática
- ✅ Generación de resúmenes
- ✅ Detección de anomalías

**Clases Principales**:
```python
IntegradorLLM:              # Integrador principal
ClienteLLM (ABC):           # Interfaz base
ClienteOpenAI:              # Implementación OpenAI
ClienteAnthropic:           # Implementación Anthropic
RespuestaLLM:              # Estructura de respuesta
```

**Métodos**:
```python
integracion = IntegradorLLM(ProveedorLLM.ANTHROPIC)

# Análisis de datos
respuesta = integracion.consultar_analisis(datos, tipo="riesgos")

# Clasificación
categoria, confianza = integracion.consultar_clasificacion(datos, ["A", "B", "C"])

# Resúmenes
resumen = integracion.consultar_resumen(datos, max_palabras=200)

# Recomendaciones
recomendaciones = integracion.consultar_recomendaciones(datos, contexto="OC 123")

# Detección de anomalías
anomalias = integracion.consultar_deteccion_anomalias(datos)

# Estadísticas
stats = integracion.obtener_estadisticas()
```

---

### 2. `modules/analizador_inteligente.py` (800+ líneas)

**Propósito**: Análisis inteligente de datos SAC específicos.

**Características**:
- ✅ Análisis completo de OCs
- ✅ Análisis de distribuciones
- ✅ Detección de anomalías inteligente
- ✅ Clasificación de órdenes por riesgo
- ✅ Generación de insights
- ✅ Puntuación de salud de OC

**Clases Principales**:
```python
AnalizadorInteligente:      # Analizador principal
AnálisisOC:                # Resultado de análisis OC
AnálisisDistribución:      # Resultado de análisis distribuciones
```

**Métodos**:
```python
analizador = AnalizadorInteligente(cliente_llm)

# Análisis completo de OC
analisis_oc = analizador.analizar_oc_completa(df_oc, df_distro)
# Retorna: riesgos, oportunidades, recomendaciones, puntuación

# Análisis de distribuciones
analisis_dist = analizador.analizar_distribucion_inteligente(df_distro, oc_numero)
# Retorna: equidad, anomalías, tiendas en riesgo

# Detección de anomalías
anomalias = analizador.detectar_anomalias_inteligentes(df_datos, tipo="oc")
# Retorna: lista de anomalías con severidad

# Clasificación de órdenes
clasificadas = analizador.clasificar_ordenes(df_oc)
# Retorna: {"CRÍTICAS": [...], "ALTO_RIESGO": [...], "NORMAL": [...]}

# Insights automáticos
insights = analizador.generar_insights(df_oc, df_distro)
# Retorna: lista de insights accionables
```

---

### 3. `modules/asistente_conversacional.py` (700+ líneas)

**Propósito**: Interacción conversacional natural con el sistema.

**Características**:
- ✅ Chat natural en español
- ✅ Manejo de contexto de conversación
- ✅ Múltiples conversaciones simultáneas
- ✅ Asistencia paso a paso
- ✅ Respuestas por defecto sin LLM
- ✅ Historial y estadísticas

**Clases Principales**:
```python
AsistenteConversacional:    # Asistente para usuario
GestorConversaciones:       # Gestor de múltiples conversaciones
Conversacion:               # Registro de conversación
PromptTemplate:             # Templates de prompts
```

**Métodos**:
```python
asistente = AsistenteConversacional(cliente_llm, usuario="Juan")

# Iniciar conversación
conv_id = asistente.iniciar_conversacion()

# Chat simple
respuesta = asistente.chat("¿Cuáles son los riesgos de la OC C123456?")

# Establecer contexto
asistente.establecer_contexto("oc", {"oc_numero": "C123456", "cantidad_total": 1000})

# Solicitar análisis
analisis = asistente.solicitar_analisis("riesgos")

# Generar reporte
reporte = asistente.generar_reporte_conversacional(datos_oc)

# Asistencia paso a paso
pasos = asistente.obtener_asistencia_paso_a_paso("Validar una OC")

# Obtener historial
historial = asistente.obtener_historial()

# Finalizar
resumen = asistente.finalizar_conversacion()
```

---

### 4. `modules/generador_reportes_inteligentes.py` (900+ líneas)

**Propósito**: Generación automática de reportes con análisis IA.

**Características**:
- ✅ Reportes de planning inteligentes
- ✅ Reportes de anomalías
- ✅ Reportes de OC específicas
- ✅ Exportación a múltiples formatos
- ✅ Resúmenes conversacionales
- ✅ Alertas automáticas
- ✅ Recomendaciones contextuales

**Clases Principales**:
```python
GeneradorReportesInteligentes:  # Generador
ReporteInteligente:             # Estructura de reporte
```

**Métodos**:
```python
generador = GeneradorReportesInteligentes(cliente_llm, generador_excel)

# Reporte de planning
reporte = generador.generar_reporte_planning_inteligente(df_oc, df_distro)

# Reporte de anomalías
reporte = generador.generar_reporte_anomalias_inteligente(df_datos, anomalias)

# Reporte de OC
reporte = generador.generar_reporte_oc_inteligente(df_oc, df_distro, oc="C123456")

# Exportar reporte
archivo = generador.exportar_reporte_completo(reporte, formato="excel")

# Resumen conversacional
resumen = generador.generar_resumen_conversacional(reporte)
```

---

## 🤖 PROVEEDORES SOPORTADOS

### OpenAI (GPT)

**Modelos disponibles**:
- `gpt-3.5-turbo` (recomendado: rápido, económico)
- `gpt-4` (más preciso, más caro)
- `gpt-4-turbo` (balance óptimo)

**Precios** (aproximados 2024):
- GPT-3.5: $0.0005 entrada / $0.0015 salida por 1K tokens
- GPT-4: $0.03 entrada / $0.06 salida por 1K tokens

**Configuración**:
```bash
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODELO=gpt-3.5-turbo
```

**Uso**:
```python
from modules.integracion_llm import IntegradorLLM, ProveedorLLM

integracion = IntegradorLLM(ProveedorLLM.OPENAI, modelo="gpt-3.5-turbo")
```

---

### Anthropic (Claude)

**Modelos disponibles**:
- `claude-3-haiku-20240307` (rápido, económico)
- `claude-3-sonnet-20240229` (balance)
- `claude-3-opus-20240229` (más potente)

**Precios** (aproximados 2024):
- Haiku: $0.25 entrada / $1.25 salida por 1M tokens
- Sonnet: $3.0 entrada / $15.0 salida por 1M tokens
- Opus: $15.0 entrada / $75.0 salida por 1M tokens

**Configuración**:
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODELO=claude-3-haiku-20240307
```

**Uso**:
```python
from modules.integracion_llm import IntegradorLLM, ProveedorLLM

integracion = IntegradorLLM(ProveedorLLM.ANTHROPIC)
```

---

## ✨ CAPACIDADES PRINCIPALES

### 1. Análisis Inteligente de OCs

```python
from modules.analizador_inteligente import AnalizadorInteligente

analizador = AnalizadorInteligente(cliente_llm)

# Análisis completo
analisis = analizador.analizar_oc_completa(df_oc, df_distro)

print(f"Resumen: {analisis.resumen_ejecutivo}")
print(f"Puntuación de salud: {analisis.puntuacion_salud:.0%}")
print(f"Crítica: {'Sí' if analisis.es_critica else 'No'}")

for riesgo in analisis.riesgos_identificados:
    print(f"  - [{riesgo['severidad']}] {riesgo['descripcion']}")

for rec in analisis.recomendaciones:
    print(f"  → {rec}")
```

**Resultados**:
- Resumen ejecutivo automático
- Identificación de riesgos por severidad
- Oportunidades de mejora
- Recomendaciones accionables
- Puntuación de salud (0-1)
- Indicador de criticidad

---

### 2. Asistente Conversacional

```python
from modules.asistente_conversacional import AsistenteConversacional

asistente = AsistenteConversacional(cliente_llm, usuario="Juan García")
conv_id = asistente.iniciar_conversacion()

# Preguntar
respuesta = asistente.chat("¿Qué significa el alto valor de distribución en la OC C123456?")
print(respuesta)

# Establecer contexto
asistente.establecer_contexto("oc", {
    "oc_numero": "C123456",
    "cantidad_total": 5000,
    "vigencia": "2025-01-15"
})

# Solicitar análisis
analisis = asistente.solicitar_analisis("riesgos")
print(analisis)

# Generar reporte
reporte = asistente.generar_reporte_conversacional(datos_oc)
print(reporte)
```

**Características**:
- Responde en español natural
- Mantiene contexto de conversación
- Entiendo intenciones del usuario
- Proporciona respuestas claras y accionables

---

### 3. Detección de Anomalías IA

```python
from modules.analizador_inteligente import AnalizadorInteligente

analizador = AnalizadorInteligente(cliente_llm)

# Detectar anomalías
resultado = analizador.detectar_anomalias_inteligentes(df_oc, tipo="oc")

if not resultado['es_normal']:
    print(f"⚠️  Anomalías detectadas (confianza: {resultado['confianza']:.0%})")
    for anom in resultado['anomalias_detectadas']:
        print(f"  [{anom['severidad']}] {anom['tipo']}: {anom['descripcion']}")
```

**Tipos de anomalías detectadas**:
- Distribuciones inequitativas (variance > 50%)
- Cantidades inusualmente altas/bajas
- Patrones de tiendas sospechosos
- Desviaciones estadísticas (> 3σ)
- Cambios significativos respecto a histórico

---

### 4. Clasificación Automática de Órdenes

```python
from modules.analizador_inteligente import AnalizadorInteligente

analizador = AnalizadorInteligente(cliente_llm)

# Clasificar
clasificadas = analizador.clasificar_ordenes(df_oc)

print(f"CRÍTICAS ({len(clasificadas['CRÍTICAS'])}): {clasificadas['CRÍTICAS'][:3]}")
print(f"ALTO RIESGO ({len(clasificadas['ALTO_RIESGO'])}): {clasificadas['ALTO_RIESGO'][:3]}")
print(f"NORMAL ({len(clasificadas['NORMAL'])}): {clasificadas['NORMAL'][:3]}")
```

**Categorías**:
- **CRÍTICAS**: Requieren atención inmediata
- **ALTO_RIESGO**: Requieren revisión
- **NORMAL**: Operación estándar
- **BAJO_RIESGO**: Bajo riesgo

---

### 5. Reportes Inteligentes

```python
from modules.generador_reportes_inteligentes import GeneradorReportesInteligentes

generador = GeneradorReportesInteligentes(cliente_llm, generador_excel)

# Generar reporte
reporte = generador.generar_reporte_planning_inteligente(df_oc, df_distro)

# Mostrar resumen conversacional
print(generador.generar_resumen_conversacional(reporte))

# Exportar
archivo = generador.exportar_reporte_completo(reporte, formato="excel")
print(f"Reporte guardado en: {archivo}")
```

**Contenido de reportes**:
- Resumen ejecutivo
- Métricas clave
- Análisis detallado
- Alertas críticas
- Recomendaciones priorizadas
- Próximos pasos

---

## 💻 EJEMPLOS DE USO

### Ejemplo 1: Análisis Completo de OC

```python
import pandas as pd
from modules.integracion_llm import IntegradorLLM, ProveedorLLM
from modules.analizador_inteligente import AnalizadorInteligente

# Inicializar
cliente_llm = IntegradorLLM(ProveedorLLM.ANTHROPIC)
analizador = AnalizadorInteligente(cliente_llm)

# Cargar datos
df_oc = pd.read_csv("oc_data.csv")
df_distro = pd.read_csv("distribucion_data.csv")

# Analizar
analisis = analizador.analizar_oc_completa(df_oc, df_distro)

# Mostrar resultados
print("=" * 70)
print(f"OC: {analisis.oc_numero}")
print(f"Salud: {analisis.puntuacion_salud:.0%} {'🟢' if analisis.puntuacion_salud > 0.7 else '🔴'}")
print(f"Crítica: {'SÍ ⚠️' if analisis.es_critica else 'NO ✅'}")
print("\nResumen:")
print(analisis.resumen_ejecutivo)
print("\nRiesgos:")
for r in analisis.riesgos_identificados:
    print(f"  • {r['descripcion']}")
print("\nRecomendaciones:")
for i, rec in enumerate(analisis.recomendaciones, 1):
    print(f"  {i}. {rec}")
```

---

### Ejemplo 2: Chat Conversacional

```python
from modules.asistente_conversacional import AsistenteConversacional
from modules.integracion_llm import IntegradorLLM, ProveedorLLM

# Inicializar
cliente_llm = IntegradorLLM(ProveedorLLM.ANTHROPIC)
asistente = AsistenteConversacional(cliente_llm, usuario="Analista Planning")

# Iniciar conversación
conv_id = asistente.iniciar_conversacion()
print(f"Conversación iniciada: {conv_id}\n")

# Conversación interactiva
mensajes = [
    "Hola, necesito ayuda con la OC C123456",
    "¿Cuáles son los riesgos principales?",
    "¿Qué me recomiendas?",
    "¿Cómo puedo optimizar la distribución?"
]

for mensaje in mensajes:
    print(f"\n👤 Tú: {mensaje}")
    respuesta = asistente.chat(mensaje)
    print(f"🤖 Asistente: {respuesta}\n")
    print("-" * 70)

# Finalizar
resumen = asistente.finalizar_conversacion()
print(f"\nConversación finalizada ({resumen['total_turnos']} turnos)")
```

---

### Ejemplo 3: Generación de Reportes

```python
from modules.generador_reportes_inteligentes import GeneradorReportesInteligentes
from modules.integracion_llm import IntegradorLLM, ProveedorLLM
import pandas as pd

# Inicializar
cliente_llm = IntegradorLLM(ProveedorLLM.ANTHROPIC)
generador = GeneradorReportesInteligentes(cliente_llm)

# Cargar datos
df_oc = pd.read_csv("oc_data.csv")
df_distro = pd.read_csv("distribucion_data.csv")

# Generar reporte
reporte = generador.generar_reporte_planning_inteligente(
    df_oc, df_distro, periodo="Diario"
)

# Mostrar resumen
print(generador.generar_resumen_conversacional(reporte))

# Exportar
archivo = generador.exportar_reporte_completo(reporte, formato="json")
print(f"\n✅ Reporte guardado: {archivo}")
```

---

## 🔌 INTEGRACIÓN EN FLUJOS EXISTENTES

### En `main.py`

```python
from modules.integracion_llm import IntegradorLLM, ProveedorLLM
from modules.analizador_inteligente import AnalizadorInteligente

def menu_interactivo():
    # Inicializar LLM si está disponible
    cliente_llm = None
    try:
        cliente_llm = IntegradorLLM(ProveedorLLM.ANTHROPIC)
        analizador = AnalizadorInteligente(cliente_llm)
        print("✅ Análisis inteligente disponible")
    except Exception as e:
        print(f"⚠️  Análisis inteligente no disponible: {e}")

    # ... resto del menú ...

    # Opción para análisis inteligente
    if cliente_llm:
        opcion = input("\n¿Deseas análisis inteligente? (s/n): ")
        if opcion.lower() == 's':
            analisis = analizador.analizar_oc_completa(df_oc, df_distro)
            print(f"\n📊 Análisis Inteligente:")
            print(analisis.resumen_ejecutivo)
```

---

### En `monitor.py`

```python
from modules.analizador_inteligente import AnalizadorInteligente

def monitoreo_continuo():
    # Detección de anomalías inteligente
    if cliente_llm:
        anomalias = analizador.detectar_anomalias_inteligentes(df_oc, tipo="oc")

        if not anomalias['es_normal']:
            logger.critical(f"🚨 Anomalías detectadas: {anomalias}")
            enviar_alerta_critica(anomalias)
```

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODELO=gpt-3.5-turbo

# Anthropic/Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODELO=claude-3-haiku-20240307

# Proveedor por defecto (openai o anthropic)
LLM_PROVEEDOR=anthropic
```

### Instalación de Dependencias

```bash
# OpenAI
pip install openai

# Anthropic
pip install anthropic

# Ambos
pip install openai anthropic
```

---

## 📚 CASOS DE USO

### Caso 1: Validación Automática de OC

```python
# Sistema automático que valida y analiza cada OC
for oc_numero in df_oc['OC'].unique():
    df_oc_actual = df_oc[df_oc['OC'] == oc_numero]
    analisis = analizador.analizar_oc_completa(df_oc_actual)

    if analisis.es_critica:
        enviar_alerta(f"OC {oc_numero} CRÍTICA: {analisis.recomendaciones[0]}")
```

---

### Caso 2: Asistencia a Analistas

```python
# Analista puede chatear con el asistente
asistente = AsistenteConversacional(cliente_llm, usuario="Analista")
conv_id = asistente.iniciar_conversacion()

while True:
    pregunta = input("❓ Pregunta: ")
    if pregunta.lower() in ['salir', 'exit']:
        break

    respuesta = asistente.chat(pregunta)
    print(f"✓ {respuesta}\n")
```

---

### Caso 3: Reportes Automáticos Diarios

```python
# Programa que genera reporte automáticamente cada día
generador = GeneradorReportesInteligentes(cliente_llm)

reporte = generador.generar_reporte_planning_inteligente(df_oc, df_distro)

# Enviar por email
resumen = generador.generar_resumen_conversacional(reporte)
gestor_correos.enviar_reporte(
    destinatarios=["analista@chedraui.com"],
    asunto=f"Reporte Inteligente {datetime.now().strftime('%Y-%m-%d')}",
    cuerpo_html=f"<pre>{resumen}</pre>"
)
```

---

## ⚠️ LIMITACIONES Y CONSIDERACIONES

### Limitaciones Técnicas

1. **Disponibilidad de API**: Requiere conexión a internet
2. **Latencia**: Primeras respuestas pueden tardar 2-5 segundos
3. **Costos**: Consumo de tokens genera costos
4. **Límites de Rate**: Cada proveedor tiene límites de tasa
5. **Contexto**: Historial de conversación limitado a ~4000 tokens

### Consideraciones de Seguridad

1. **API Keys**: Nunca commitear claves en código
2. **Datos Sensibles**: No enviar datos confidenciales innecesarios
3. **Validación**: Siempre validar respuestas del LLM
4. **Auditoría**: Loguear todas las consultas para trazabilidad

### Estrategia de Fallback

```python
try:
    analisis = analizador.analizar_oc_completa(df_oc)
except Exception as e:
    logger.warning(f"⚠️  LLM no disponible: {e}")
    # Fallback a validación tradicional
    analisis_tradicional = monitor.validar_oc(df_oc)
```

---

## 📊 COSTOS ESTIMADOS

**Ejemplo**: Procesar 100 OCs diarias

| Proveedor | Modelo | Costo/día | Costo/mes |
|-----------|--------|-----------|-----------|
| OpenAI | GPT-3.5 | $0.50 | $15 |
| OpenAI | GPT-4 | $3.00 | $90 |
| Anthropic | Haiku | $0.10 | $3 |
| Anthropic | Sonnet | $0.50 | $15 |

---

## 🔄 PRÓXIMAS MEJORAS

1. **Cache de Respuestas**: Caching de análisis comunes
2. **Fine-tuning**: Entrenar modelos con datos SAC
3. **Integración de Web**: API REST para acceso remoto
4. **Mobile App**: Asistente en dispositivos móviles
5. **Análisis Histórico**: Comparación con datos históricos
6. **Predicciones**: Forecasting de demanda

---

## 📞 SOPORTE

Para preguntas o issues:
1. Revisar docstrings en módulos
2. Consultar ejemplos en esta documentación
3. Verificar configuración de .env
4. Revisar logs en `output/logs/`

---

**Documento creado**: Noviembre 2025
**Versión**: 1.0.0
**CEDIS**: Cancún 427 - Tiendas Chedraui S.A. de C.V.

---
