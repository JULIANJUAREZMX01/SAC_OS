# 📧 Enviar Correo de Hito SAC 2.0

> **Instrucciones para Enviar Correo Profesional de Entrega**
>
> CEDIS Cancún 427 - Tiendas Chedraui
>
> Noviembre 2025

---

## 🎯 Objetivo

Enviar un correo profesional confirmando la entrega completa de SAC 2.0 al equipo de administración, sistemas y stakeholders.

---

## 📋 Requisitos

- ✅ Python 3.8 o superior instalado
- ✅ SAC 2.0 completamente configurado
- ✅ Archivo `.env` con credenciales de email
- ✅ Conexión a Internet disponible
- ✅ Acceso a smtp.office365.com:587

---

## 🚀 Instrucciones de Ejecución

### Opción 1: Ejecutar Directamente

```bash
# Abrir terminal/CMD en la carpeta de SAC 2.0

# Ejecutar el script
python enviar_hito_sac2.0.py

# Esperar a que se complete el envío
# Verás mensajes de progreso como:
#   ✅ Mensaje creado correctamente
#   ✅ Conexión TLS establecida
#   ✅ Autenticación exitosa
#   ✅ CORREO ENVIADO EXITOSAMENTE
```

### Opción 2: Con Argumentos (Personalización)

```bash
# Ver ayuda
python enviar_hito_sac2.0.py --help

# Enviar a destinatarios específicos
python enviar_hito_sac2.0.py --to email1@chedraui.com.mx,email2@chedraui.com.mx

# Incluir CC adicional
python enviar_hito_sac2.0.py --cc cc1@chedraui.com.mx,cc2@chedraui.com.mx
```

### Opción 3: Desde Python Script

```python
#!/usr/bin/env python3
from enviar_hito_sac2_0 import enviar_correo_hito

# Ejecutar
exito = enviar_correo_hito()

if exito:
    print("✅ Correo enviado exitosamente")
else:
    print("❌ Error al enviar correo")
```

---

## 📊 Contenido del Correo

El correo incluye automáticamente:

### Encabezado Profesional
- Título: "🎉 SAC 2.0 - HITO COMPLETADO"
- Subtítulo: "Creación y Puesta en Marcha Exitosa"
- Logo/Colores corporativos Chedraui

### Cuerpo Principal
✅ Estadísticas del proyecto
- 3,600+ líneas de código
- 9 archivos nuevos
- 100% WCAG 2.1 AA

✅ Características principales
- Módulo de reportería accesible
- REST API con documentación OpenAPI
- Accesibilidad integral (5 lectores de pantalla)
- Email corporativo integrado
- DB2 garantizado

✅ Integraciones configuradas
- Base de datos IBM DB2
- Email Office 365
- API REST
- Reportería profesional

✅ Accesibilidad implementada
- WCAG 2.1 Nivel A: 100%
- WCAG 2.1 Nivel AA: 100%
- WCAG 2.1 Nivel AAA: 50%

✅ Instrucciones de inicio
- Instalación de drivers
- Verificación de integraciones
- Ejecución del sistema

✅ Información de contacto
- Jefe de Sistemas
- Email directo
- Ubicación del CEDIS

### Pie de Página
- Versión del sistema
- Rama Git
- Información de derechos

---

## 🔍 Verificación Previa al Envío

Antes de ejecutar el script, verifica que todo esté listo:

```bash
# 1. Verificar archivo .env existe
test -f .env && echo "✅ .env encontrado" || echo "❌ .env no existe"

# 2. Verificar credenciales están configuradas
grep -q "EMAIL_USER=" .env && echo "✅ EMAIL_USER configurado"
grep -q "EMAIL_PASSWORD=" .env && echo "✅ EMAIL_PASSWORD configurado"

# 3. Verificar script existe
test -f enviar_hito_sac2_0.py && echo "✅ Script encontrado"

# 4. Ejecutar verificación de integraciones
python verificar_integraciones.py
```

---

## ⚠️ Solución de Problemas

### Error: "Módulo no encontrado"

```bash
# Instalar dependencias necesarias
pip install python-dotenv
```

### Error: "Autenticación fallida"

Posibles causas:
1. **Contraseña incorrecta en .env**
   - Verificar que EMAIL_PASSWORD sea correcta
   - Verificar caracteres especiales no estén escapados

2. **Usuario incorrecto**
   - Verificar que EMAIL_USER sea exacto
   - Debe ser: `u427jd15@chedraui.com.mx`

3. **Contraseña de aplicación requerida**
   - Office 365 puede requerir "contraseña de aplicación"
   - Ir a: https://account.microsoft.com/security-info
   - Crear "Contraseña de aplicación" para correo

### Error: "Conexión rechazada"

Posibles causas:
1. **Sin conectividad de red**
   - Verificar conexión Internet: `ping 8.8.8.8`
   - Verificar puerto 587: `telnet smtp.office365.com 587`

2. **Firewall/Proxy bloqueando**
   - Contactar a TI de Chedraui
   - Solicitar apertura puerto 587 a smtp.office365.com

3. **Servidor incorrecto**
   - Verificar EMAIL_HOST en .env
   - Debe ser: `smtp.office365.com`

### Error: "Timeout"

- Aumentar timeout en script:
  ```python
  server = smtplib.SMTP(host, port, timeout=30)  # Aumentar de 10 a 30
  ```

---

## 📧 Destinatarios Predeterminados

El script usa automáticamente:

**Para (TO):**
```
"JERONIMO GARCIA,JUAN" <jgarciaj@chedraui.com.mx>
```

**Copia Carbón (CC):**
```
"VERA REYES,ITZA RUBY" <ivreyes@chedraui.com.mx>
"SUAREZ PACHECO,ISRAEL" <isuarez@chedraui.com.mx>
"Control de Inventario, Cedis 427" <cedis427ci@chedraui.com.mx>
"Auditor calidad 427" <auditorcalidad427@chedraui.com.mx>
"MESA DE EXPEDICION, CEDIS CANCUN" <mexpedicion427ced@chedraui.com.mx>
"MESA DE PREPARACION, CEDIS CANCUN" <mpreparacion427ced@chedraui.com.mx>
"MESA DE RECIBO, CEDIS CANCUN" <mrecibo427ced@chedraui.com.mx>
```

---

## 🎨 Personalización

### Cambiar Destinatarios

Edita el archivo `.env`:

```bash
# Destinatarios principales
EMAIL_TO_CRITICAL="Nombre1" <email1@chedraui.com.mx>, "Nombre2" <email2@chedraui.com.mx>

# Copia carbón (CC)
EMAIL_CC="Nombre3" <email3@chedraui.com.mx>, "Nombre4" <email4@chedraui.com.mx>
```

### Cambiar Asunto

Edita `enviar_hito_sac2_0.py`, línea del Subject:

```python
msg['Subject'] = 'Tu nuevo asunto aquí'
```

### Cambiar Contenido HTML

Edita la función `crear_correo_hito()` en `enviar_hito_sac2_0.py`:

```python
def crear_correo_hito() -> str:
    """Crea el contenido HTML del correo de hito"""
    html = """
    <!-- Editar HTML aquí -->
    """
    return html
```

---

## ✅ Confirmación de Envío Exitoso

Cuando el envío sea exitoso, verás:

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ✅ CORREO DE HITO ENVIADO EXITOSAMENTE                        ║
║                                                                ║
║  Fecha: 22/11/2025 16:45:30                                   ║
║  Destinatarios: 8                                             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 📱 Después del Envío

Una vez que el correo sea enviado:

1. **Verificar en Bandeja de Salida**
   - Acceder a: https://outlook.office365.com
   - Ir a: Elementos Enviados
   - Confirmar que el correo aparece

2. **Confirmar Recepción**
   - Contactar a destinatarios principales
   - Solicitar confirmación de recepción
   - Verificar que el HTML se vea correctamente

3. **Guardar Evidencia**
   - Hacer screenshot del correo enviado
   - Guardar confirmación de envío

---

## 🔒 Seguridad

**IMPORTANTE:**
- ✅ El archivo `.env` nunca se sube a Git
- ✅ Las credenciales están encriptadas en tránsito (TLS)
- ✅ El script valida antes de enviar
- ✅ Se mantiene log de envíos

---

## 📞 Soporte

Si hay problemas al enviar el correo:

1. **Revisar logs del script**
   - Ejecutar con más detalle: `python -u enviar_hito_sac2_0.py`

2. **Verificar conectividad**
   - Ejecutar: `python verificar_integraciones.py`

3. **Contactar a Sistemas**
   - Email: u427jd15@chedraui.com.mx
   - Ext: 4336

---

## 📚 Referencia Rápida

```bash
# Ejecutar envío
python enviar_hito_sac2_0.py

# Verificar antes de enviar
python verificar_integraciones.py

# Ver credenciales configuradas (NO mostrar en pantalla)
cat .env | grep EMAIL

# Ver logs de ejecución
python enviar_hito_sac2_0.py 2>&1 | tee envio.log
```

---

## 🎯 Resultados Esperados

| Aspecto | Resultado |
|---------|-----------|
| Conexión SMTP | ✅ TLS iniciado |
| Autenticación | ✅ Exitosa |
| Creación de mensaje | ✅ HTML válido |
| Envío | ✅ Completado |
| Destinatarios | ✅ Recibido |
| Apariencia | ✅ Profesional |

---

**Documento versión**: 1.0
**Última actualización**: Noviembre 2025
**Responsable**: ADMJAJA - Jefe de Sistemas CEDIS 427

---

## 🚀 ¡Listo para Enviar!

El correo de hito está completamente preparado. Solo ejecuta:

```bash
python enviar_hito_sac2_0.py
```

¡SAC 2.0 estará oficialmente entregado al equipo! 🎉
