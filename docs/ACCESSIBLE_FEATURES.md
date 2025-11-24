# 🎯 Capacidades y Artefactos Accesibles - SAC 1.0

> **Documentación WCAG 2.1 AA Compliant**
>
> Sistema de Automatización de Consultas - CEDIS Cancún 427
>
> Última actualización: Noviembre 2025

---

## 📋 Tabla de Contenidos

1. [Características de Accesibilidad](#características-de-accesibilidad)
2. [Módulo de Reportería Accesible](#módulo-de-reportería-accesible)
3. [REST API WCAG Compliant](#rest-api-wcag-compliant)
4. [Guías de Uso](#guías-de-uso)
5. [Soporte para Lectores de Pantalla](#soporte-para-lectores-de-pantalla)
6. [Temas de Alto Contraste](#temas-de-alto-contraste)

---

## ✨ Características de Accesibilidad

### WCAG 2.1 Nivel AA

El sistema SAC ahora cumple con **WCAG 2.1 Nivel AA**, que significa:

✅ **Perceptible**: Información accesible a todos
- Texto con contraste suficiente
- Alternativas para contenido visual
- Contenido legible y comprensible

✅ **Operable**: Navegación por teclado completa
- Tab para navegar
- Enter para seleccionar
- Escape para cancelar

✅ **Comprensible**: Lenguaje claro y predecible
- Estructura semántica HTML5
- Roles ARIA descriptivos
- Mensajes de error claros

✅ **Robusto**: Compatible con tecnologías de asistencia
- Lectores de pantalla (NVDA, JAWS, VoiceOver)
- Navegadores antiguos
- Dispositivos móviles

---

## 📊 Módulo de Reportería Accesible

### Ubicación
```
modules/accessible_reports/
├── __init__.py
├── base.py              # Clase base abstracta
├── html_generator.py    # Reportes HTML WCAG
├── text_generator.py    # Reportes en texto plano
└── pdf_generator.py     # Reportes PDF accesibles
```

### Generador HTML (WCAG 2.1 AA)

Genera reportes HTML semánticos con características accesibles.

#### Ejemplo de uso:

```python
from modules.accessible_reports import AccessibleHTMLReport
from modules.accessible_reports.base import ReportMetadata, AccessibilitySettings, ContrastMode

# Crear metadatos
metadata = ReportMetadata(
    title="Reporte de Validación OC",
    description="Validación de Órdenes de Compra vs Distribuciones",
    author="Sistema SAC",
    cedis_name="CEDIS Cancún 427",
    cedis_code="427"
)

# Configurar accesibilidad
accessibility = AccessibilitySettings(
    contrast_mode=ContrastMode.NORMAL,  # O: HIGH, DARK, LIGHT
    include_aria_labels=True,
    include_semantic_html=True,
    keyboard_navigation=True,
    language_code="es"
)

# Crear reporte
reporte = AccessibleHTMLReport(metadata, accessibility)

# Agregar contenido
from modules.accessible_reports.base import ReportSection
section = ReportSection(
    id="validacion",
    title="Resultados de Validación",
    heading_level=2,
    content="<p>Se validaron 150 órdenes de compra...</p>"
)
reporte.add_section(section)

# Agregar tabla
import pandas as pd
df = pd.DataFrame({
    'OC': ['750384000001', '750384000002'],
    'Estado': ['✅ Aprobada', '❌ Fallida'],
    'Detalles': ['Sin errores', 'Distribución excede']
})
reporte.add_table(
    df,
    caption="Órdenes de Compra",
    summary="Tabla con resultados de validación de OCs"
)

# Generar
if reporte.generate("/ruta/reporte.html"):
    print("✅ Reporte generado correctamente")
```

#### Características HTML WCAG:

| Característica | Descripción |
|---|---|
| **Skip Links** | Saltar contenido repetitivo (2.4.1) |
| **Encabezados Semánticos** | h1 > h2 > h3 jerárquico |
| **ARIA Labels** | `aria-label`, `aria-describedby` en elementos |
| **Tablas Accesibles** | `<table>` con `<th scope="row">` y `<th scope="col">` |
| **Navegación por Teclado** | Tab, Enter, Escape funcionales |
| **Contraste WCAG AAA** | Texto: 7:1 en modo high-contrast |
| **Modo Oscuro** | Automático según preferencia SO |
| **Print-Friendly** | CSS optimizado para impresión |
| **Barra de Herramientas** | A+ / A- / Contraste / Imprimir / PDF |

#### Modos de Contraste:

```python
# Contraste normal (Chedraui estándar)
ContrastMode.NORMAL

# Alto contraste (WCAG AAA)
ContrastMode.HIGH

# Modo oscuro (prefers-color-scheme: dark)
ContrastMode.DARK

# Modo claro
ContrastMode.LIGHT
```

### Generador de Texto Plano

Genera reportes en texto puro para:
- Lectores de pantalla
- Email directo
- Cualquier dispositivo

#### Ejemplo:

```python
from modules.accessible_reports import AccessibleTextReport

reporte = AccessibleTextReport(metadata)

# Agregar secciones
reporte.add_section(section)

# Agregar tablas
reporte.add_table(
    df,
    title="Órdenes de Compra",
    description="Tabla con OCs validadas"
)

# Generar
reporte.generate("/ruta/reporte.txt")

# El archivo incluye:
# ✓ Tabla ASCII formateada
# ✓ Información de accesibilidad
# ✓ Índice de contenidos
# ✓ Resumen ejecutivo
```

### Generador PDF Accesible

Genera PDFs con etiquetado semántico y metadata accesible.

#### Ejemplo:

```python
from modules.accessible_reports import AccessiblePDFReport

reporte = AccessiblePDFReport(
    metadata,
    page_size="a4",
    include_toc=True  # Tabla de contenidos con bookmarks
)

# ... agregar contenido ...

reporte.generate("/ruta/reporte.pdf")

# El PDF incluye:
# ✓ Metadata accesible
# ✓ Bookmarks de navegación
# ✓ Estructura etiquetada
# ✓ Texto seleccionable
# ✓ Colores WCAG AA
```

---

## 🔗 REST API WCAG Compliant

### Ubicación
```
modules/api_rest.py
```

### Documentación Interactiva

La API incluye documentación automática e interactiva:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Iniciar API

#### Opción 1: Direct

```bash
python -m modules.api_rest
```

#### Opción 2: Uvicorn

```bash
uvicorn modules.api_rest:app --reload --host 0.0.0.0 --port 8000
```

### Endpoints Principales

#### 1. Validar OC

```bash
POST /api/v1/validaciones/oc
Content-Type: application/json

{
  "numero_oc": "750384000001",
  "incluir_distribuciones": true,
  "incluir_asn": true,
  "detalle_completo": false
}
```

**Respuesta exitosa:**
```json
{
  "oc_numero": "750384000001",
  "estado": "APROBADO",
  "mensaje": "✅ OC 750384000001 validada correctamente",
  "errores": [],
  "advertencias": [],
  "timestamp": "2025-11-22T10:30:00Z"
}
```

#### 2. Generar Reporte

```bash
POST /api/v1/reportes/generar
Content-Type: application/json

{
  "tipo": "validacion_oc",
  "formato": "html",
  "incluir_accesibilidad": true,
  "numero_oc": "750384000001"
}
```

**Respuesta:**
```json
{
  "id_reporte": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tipo": "validacion_oc",
  "formato": "html",
  "estado": "COMPLETADO",
  "fecha_generacion": "2025-11-22T10:30:00Z",
  "tiempo_generacion_ms": 150.5,
  "tamaño_bytes": 15420,
  "url_descarga": "/api/v1/reportes/a1b2c3d4-e5f6-7890-abcd-ef1234567890/descargar",
  "mensaje": "✅ Reporte generado exitosamente"
}
```

#### 3. Obtener Estado del Sistema

```bash
GET /api/v1/sistema/status
```

**Respuesta:**
```json
{
  "estado": "OK",
  "base_datos": "CONECTADO",
  "email": "ACTIVO",
  "almacenamiento": "DISPONIBLE",
  "uptime_segundos": 86400,
  "version": "1.0.0",
  "timestamp": "2025-11-22T10:30:00Z"
}
```

### Validación de Entrada

Todas las solicitudes se validan automáticamente:

```python
# Número OC válido - patrones aceptados:
"750384000001"      # 750384XXXXXX
"811117000001"      # 811117XXXXXX
"40123456789012"    # 40XXXXXXXXXXX
"C000001"           # CXXXXXX

# Formatos de reporte:
"validacion_oc"     # Validación OC
"planning_diario"   # Planning Diario
"distribuciones"    # Distribuciones
"errores"           # Errores detectados
"reconciliacion"    # Reconciliación
"asn"              # ASN

# Formatos de salida:
"html"              # HTML accesible
"pdf"               # PDF accesible
"texto"             # Texto plano
"excel"             # Excel accesible
```

### Manejo de Errores Accesible

Todos los errores incluyen información clara:

```json
{
  "codigo_error": 400,
  "tipo_error": "validation_error",
  "mensaje": "Formato de OC inválido: XYZ123",
  "detalles": {
    "campo": "numero_oc",
    "valor_recibido": "XYZ123",
    "formatos_validos": [
      "750384XXXXXX",
      "811117XXXXXX",
      "40XXXXXXXXXXX"
    ]
  },
  "timestamp": "2025-11-22T10:30:00Z"
}
```

### Rate Limiting

- 100 solicitudes por minuto por IP
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

---

## 📖 Guías de Uso

### Guía 1: Generar Reporte HTML Accesible

1. **Crear metadata**:
   ```python
   metadata = ReportMetadata(
       title="Mi Reporte",
       description="Descripción del reporte",
       cedis_name="CEDIS Cancún 427"
   )
   ```

2. **Configurar accesibilidad**:
   ```python
   accessibility = AccessibilitySettings(
       contrast_mode=ContrastMode.NORMAL,
       include_aria_labels=True,
       keyboard_navigation=True
   )
   ```

3. **Crear reporte**:
   ```python
   reporte = AccessibleHTMLReport(metadata, accessibility)
   ```

4. **Agregar contenido**:
   ```python
   reporte.add_section(section)
   reporte.add_table(df, caption="...", summary="...")
   ```

5. **Generar**:
   ```python
   reporte.generate("reporte.html")
   ```

6. **Usar**:
   - Abrir en navegador
   - Usar con lector de pantalla
   - Cambiar contraste con barra de herramientas
   - Imprimir o descargar como PDF

### Guía 2: Usar REST API desde Python

```python
import requests

# Configurar
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# Validar OC
response = requests.post(
    f"{BASE_URL}/api/v1/validaciones/oc",
    json={"numero_oc": "750384000001"},
    headers=headers
)

if response.status_code == 200:
    resultado = response.json()
    print(f"✅ {resultado['mensaje']}")
else:
    print(f"❌ Error: {response.json()}")

# Generar reporte
response = requests.post(
    f"{BASE_URL}/api/v1/reportes/generar",
    json={
        "tipo": "validacion_oc",
        "formato": "html"
    },
    headers=headers
)

reporte = response.json()
print(f"📊 Reporte: {reporte['url_descarga']}")
```

### Guía 3: Usar REST API desde JavaScript

```javascript
// Configurar
const BASE_URL = 'http://localhost:8000';

// Validar OC
async function validarOC(numeroOC) {
    const response = await fetch(`${BASE_URL}/api/v1/validaciones/oc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numero_oc: numeroOC })
    });

    const resultado = await response.json();
    console.log(`✅ ${resultado.mensaje}`);
    return resultado;
}

// Usar
validarOC('750384000001').then(resultado => {
    if (resultado.estado === 'APROBADO') {
        // Mostrar éxito
    }
});
```

### Guía 4: Usar REST API desde cURL

```bash
# Validar OC
curl -X POST http://localhost:8000/api/v1/validaciones/oc \
  -H "Content-Type: application/json" \
  -d '{
    "numero_oc": "750384000001",
    "incluir_distribuciones": true
  }'

# Generar reporte
curl -X POST http://localhost:8000/api/v1/reportes/generar \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "validacion_oc",
    "formato": "html"
  }'

# Obtener estado
curl http://localhost:8000/api/v1/sistema/status
```

---

## 🔊 Soporte para Lectores de Pantalla

### Lectores Soportados

✅ **NVDA** (Windows, Linux) - Gratuito
✅ **JAWS** (Windows) - Licencia
✅ **VoiceOver** (macOS, iOS) - Integrado
✅ **TalkBack** (Android) - Integrado
✅ **Narrator** (Windows) - Integrado

### Cómo usar reportes con lector de pantalla

1. **Abrir reporte HTML**:
   - Lector anuncia: "REPORTE: Validación OC"
   - Navega con Tab para elementos
   - Lee aria-labels automáticamente

2. **Navegar tablas**:
   - Lector anuncia encabezados con scope
   - "Fila 1, Columna 1: OC 750384000001"
   - "Fila 1, Columna 2: Estado Aprobada"

3. **Usar barra de herramientas**:
   - Tab hasta botones (A+, A-, Contraste)
   - Enter para activar
   - Cambios se anuncian

4. **Reportes de texto**:
   - Abrir archivo .txt con lector
   - Lee linealmente sin problemas
   - Tablas en formato ASCII accesible

---

## 🎨 Temas de Alto Contraste

### Activar en Reporte HTML

1. **En generación**:
   ```python
   accessibility = AccessibilitySettings(
       contrast_mode=ContrastMode.HIGH  # ← Alto contraste
   )
   ```

2. **En navegador**:
   - Click en botón "◐ Contraste" en barra superior
   - Alterna automáticamente a alto contraste

### Ratios de Contraste

| Elemento | Ratio Normal | Ratio Alto |
|---|---|---|
| Texto normal | 4.5:1 | 7:1 |
| Texto grande | 3:1 | 4.5:1 |
| Elemento enfocado | 3:1 | 5:1 |

### Modo Oscuro

Automático según preferencia del SO:

```css
/* Activado cuando: prefers-color-scheme: dark */
body {
    background-color: #121212;  /* Gris muy oscuro */
    color: #E0E0E0;             /* Gris claro */
}
```

---

## 🚀 Características Avanzadas

### 1. Validación de Accesibilidad Integrada

```python
reporte = AccessibleHTMLReport(metadata)
# ...agregar contenido...

# Validar antes de generar
validacion = reporte.validate_accessibility()

if all(validacion.values()):
    print("✅ Reporte cumple WCAG 2.1 AA")
else:
    print("⚠️ Advertencias:", validacion)
```

### 2. Personalizar Estilos CSS

```python
# En AccessibleHTMLReport
html_content = reporte._build_html()
# Incluye CSS personalizable por clase

# Clases disponibles:
# .skip-links
# .accessibility-toolbar
# .section-content
# .data-table-section
# .accessibility-statement
```

### 3. Exportar a Múltiples Formatos

```python
# Mismo reporte, múltiples formatos
metadata = ReportMetadata(...)

# HTML
html = AccessibleHTMLReport(metadata)
html.add_section(section)
html.generate("reporte.html")

# Texto
text = AccessibleTextReport(metadata)
text.add_section(section)
text.generate("reporte.txt")

# PDF
pdf = AccessiblePDFReport(metadata)
pdf.add_section(section)
pdf.generate("reporte.pdf")
```

---

## 📋 Checklist de Accesibilidad

Antes de generar un reporte, asegúrate que cumple:

- [ ] Título claro y descriptivo
- [ ] Descripción del contenido
- [ ] Estructura de encabezados jerárquica (h1 > h2 > h3)
- [ ] Atributos alt/aria-label en imágenes
- [ ] Tablas con encabezados (`<th scope>`)
- [ ] Contraste de color suficiente (4.5:1)
- [ ] Texto sin solo colores para información
- [ ] Navegación por teclado funcional
- [ ] Sin contenido que parpadea
- [ ] Lenguaje claro en español
- [ ] Validación de formularios clara
- [ ] Mensajes de error accesibles

---

## 🆘 Soporte y Ayuda

### ¿No ves los colores correctamente?

1. Abre el reporte HTML
2. Click en botón "◐ Contraste"
3. Cambia automáticamente a alto contraste

### ¿Tienes dificultad para leer?

1. Click en "A+" para aumentar fuente
2. Usa modo oscuro (automático en SO)
3. Descarga versión de texto (.txt)

### ¿Usas lector de pantalla?

1. Abre el reporte HTML
2. Lector anuncia automáticamente: "REPORTE: Título"
3. Navega con Tab entre elementos
4. Lee aria-labels descriptivos

### ¿Prefieres texto plano?

1. Solicita reporte en formato "texto"
2. Se descarga archivo .txt puro
3. Compatible con cualquier lector de pantalla

---

## 📚 Recursos Adicionales

- [WCAG 2.1 Officialt](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM](https://webaim.org/)
- [Accessibility Insights](https://accessibilityinsights.io/)

---

## 📝 Notas de Desarrollo

### Dependencias Requeridas

```bash
pip install fastapi uvicorn pydantic
pip install reportlab
pip install pandas openpyxl
pip install slowapi  # Rate limiting
pip install python-multipart
```

### Archivos Generados

```
output/resultados/
├── Reporte_WCAG_20251122_143022.html
├── Reporte_WCAG_20251122_143022.txt
└── Reporte_WCAG_20251122_143022.pdf
```

### Variables de Entorno

```bash
# Configuración de accesibilidad
ACCESSIBILITY_MODE=WCAG_AA
CONTRAST_MODE=NORMAL
LANGUAGE_CODE=es
```

---

## ✅ Validación WCAG 2.1

Este sistema ha sido diseñado y validado contra:

- ✅ WCAG 2.1 Criterios A
- ✅ WCAG 2.1 Criterios AA
- 🎯 WCAG 2.1 Criterios AAA (parcial)

Validado con:
- WAVE (WebAIM)
- Lighthouse (Google)
- Axe DevTools
- NVDA Screen Reader

---

**© 2025 Tiendas Chedraui S.A. de C.V. - CEDIS Cancún 427**

**Diseñado para todos, sin excepciones.**
