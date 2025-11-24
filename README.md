# Configuración del Sistema SAC

## Archivos de Configuración

| Archivo | Descripción |
|---------|-------------|
| `.env.example` | Plantilla de variables de entorno |
| `email_config.yaml` | Configuración de email |

## Variables de Entorno Principales

### Base de Datos (DB2)
- `DB_HOST` - Servidor DB2 (WM260BASD)
- `DB_PORT` - Puerto (50000)
- `DB_USER` - Usuario DB2
- `DB_PASSWORD` - Contraseña DB2

### Email (Office 365)
- `EMAIL_HOST` - smtp.office365.com
- `EMAIL_PORT` - 587
- `EMAIL_USER` - Correo corporativo
- `EMAIL_PASSWORD` - Contraseña

### CEDIS
- `CEDIS_CODE` - 427
- `CEDIS_NAME` - CEDIS Cancún
- `CEDIS_REGION` - Sureste

## Uso

1. Copiar `.env.example` a `.env` en la raíz del proyecto
2. Completar credenciales
3. Ejecutar `python config.py` para verificar

---
© 2025 CEDIS Cancún 427
