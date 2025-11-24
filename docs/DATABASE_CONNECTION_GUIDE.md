# Guía de Configuración de Conexión a Base de Datos DB2

> **Sistema SAC - CEDIS Cancún 427**
> Guía completa para configurar la conexión a IBM DB2 (Manhattan WMS)

---

## Tabla de Contenidos

1. [Información de Conexión](#información-de-conexión)
2. [Configuración en DBeaver](#configuración-en-dbeaver)
3. [Configuración en el Sistema SAC](#configuración-en-el-sistema-sac)
4. [Verificación de Conexión](#verificación-de-conexión)
5. [Solución de Problemas](#solución-de-problemas)

---

## Información de Conexión

### Datos del Servidor DB2 Manhattan WMS

| Parámetro | Valor |
|-----------|-------|
| **Host** | `WM260BASD` |
| **Puerto** | `50000` |
| **Base de Datos** | `WM260BASD` |
| **Schema** | `WMWHSE1` |
| **Driver** | `IBM DB2 ODBC DRIVER` |
| **Timeout** | `30` segundos |
| **Protocolo** | `TCPIP` |

### Credenciales Requeridas

- **Usuario**: Tu usuario de DB2 (ej: `ADMJAJA`)
- **Contraseña**: Tu contraseña de DB2

> **IMPORTANTE**: Las credenciales deben ser proporcionadas por el equipo de Sistemas.
> NUNCA compartas tus credenciales ni las incluyas en archivos de código.

---

## Configuración en DBeaver

### Paso 1: Crear Nueva Conexión

1. Abre DBeaver
2. Ve a **Database → New Database Connection** (o presiona `Ctrl+N`)
3. En el asistente, busca y selecciona **DB2 LUW**

### Paso 2: Configurar Parámetros de Conexión

En la pestaña **Main**, configura:

```
Host:     WM260BASD
Port:     50000
Database: WM260BASD
Username: [TU_USUARIO_DB2]
Password: [TU_CONTRASEÑA_DB2]
```

### Paso 3: Configuración de Driver

Si es la primera vez que usas DB2 en DBeaver:

1. Ve a **Window → Preferences → Connections → Drivers**
2. Selecciona **IBM DB2**
3. En **Settings**:
   - Marca "Check for new recommended driver versions on connect"
4. En **File repositories**:
   - Asegúrate de tener: `https://dbeaver.io/files/jdbc/`
5. Click en **Apply and Close**

### Paso 4: Propiedades del Driver (Avanzado)

En la pestaña **Driver properties**, agrega:

| Propiedad | Valor |
|-----------|-------|
| `currentSchema` | `WMWHSE1` |
| `loginTimeout` | `30` |
| `blockingReadConnectionTimeout` | `30000` |
| `commandTimeout` | `300` |

### Paso 5: Client Identification (Opcional)

En **Preferences → Connections → Client Identification**:

- Marca "Disable client identification" si tienes problemas de conexión
- O configura "Override client application name" con: `SAC_CEDIS_427`

### Paso 6: Tipo de Conexión

En la pestaña **Connection Details**, selecciona el tipo apropiado:

| Tipo | Uso | Color |
|------|-----|-------|
| **Development** | Pruebas y desarrollo | Blanco |
| **Test** | Pre-producción | Verde oliva |
| **Production** | Base de datos en vivo | Rojo ladrillo |

Para la base de datos `WM260BASD`, se recomienda usar **Production** ya que es el ambiente productivo.

### Paso 7: Probar Conexión

1. Click en **Test Connection...**
2. Si es exitoso, verás: "Connected"
3. Click en **Finish**

### Paso 8: Verificar Schema

Una vez conectado:

1. Expande la conexión en el navegador
2. Navega a: `WM260BASD → Schemas → WMWHSE1`
3. Verifica que puedes ver las tablas

---

## Configuración en el Sistema SAC

### Paso 1: Crear Archivo .env

```bash
# Copia el archivo de ejemplo
cp .env.example .env

# O desde Windows:
copy .env.example .env
```

### Paso 2: Configurar Credenciales

Edita el archivo `.env` y agrega tus credenciales:

```bash
# Base de Datos DB2 (Manhattan WMS)
DB_USER=TU_USUARIO_AQUI
DB_PASSWORD=TU_PASSWORD_AQUI

# Configuración pre-establecida (NO MODIFICAR)
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_DRIVER={IBM DB2 ODBC DRIVER}
DB_TIMEOUT=30
```

### Paso 3: Configuración del Pool de Conexiones

Estos valores están pre-configurados pero pueden ajustarse según necesidad:

```bash
# Pool de conexiones
DB_POOL_MIN_SIZE=1
DB_POOL_MAX_SIZE=5
DB_POOL_ACQUIRE_TIMEOUT=30.0
DB_POOL_MAX_IDLE_TIME=300.0
DB_POOL_HEALTH_CHECK_INTERVAL=60.0
DB_POOL_MAX_LIFETIME=3600.0
```

### Paso 4: Verificar Configuración

```bash
# Ejecutar verificación de configuración
python config.py

# O ejecutar health check completo
python health_check.py --detailed
```

---

## Verificación de Conexión

### Usando el Script de Verificación

```bash
# Verificar conexión a DB2
python verificar_conexion_db2.py
```

### Verificación Manual con Python

```python
from config import DB_CONFIG, DB_CONNECTION_STRING

print(f"Host: {DB_CONFIG['host']}")
print(f"Port: {DB_CONFIG['port']}")
print(f"Database: {DB_CONFIG['database']}")
print(f"User: {DB_CONFIG['user']}")
print(f"Connection String: {DB_CONNECTION_STRING}")
```

### Query de Prueba

Una vez conectado, ejecuta esta query de prueba:

```sql
-- Verificar conexión y schema
SELECT CURRENT SERVER, CURRENT SCHEMA, CURRENT USER
FROM SYSIBM.SYSDUMMY1;

-- Listar tablas del schema WMWHSE1
SELECT TABNAME, TYPE, CREATE_TIME
FROM SYSCAT.TABLES
WHERE TABSCHEMA = 'WMWHSE1'
ORDER BY CREATE_TIME DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## Solución de Problemas

### Error: "Connection refused"

**Causa**: El servidor DB2 no es accesible.

**Solución**:
1. Verifica que estés conectado a la red corporativa/VPN
2. Confirma que el host `WM260BASD` es resoluble:
   ```bash
   ping WM260BASD
   nslookup WM260BASD
   ```
3. Verifica que el puerto 50000 esté abierto:
   ```bash
   telnet WM260BASD 50000
   ```

### Error: "Authentication failed"

**Causa**: Credenciales incorrectas.

**Solución**:
1. Verifica usuario y contraseña
2. Confirma que tu usuario tenga permisos en el schema WMWHSE1
3. Contacta al equipo de DBA si persiste

### Error: "Driver not found"

**Causa**: Driver de DB2 no instalado.

**Solución para DBeaver**:
1. Ve a **Window → Driver Manager**
2. Selecciona **IBM DB2 LUW**
3. Click en **Download/Update**
4. Espera la descarga del driver

**Solución para Python**:
```bash
# Instalar ibm_db
pip install ibm_db ibm_db_sa
```

### Error: "Schema not found"

**Causa**: El schema WMWHSE1 no está configurado.

**Solución en DBeaver**:
1. Abre las propiedades de la conexión
2. Ve a **Driver properties**
3. Agrega: `currentSchema = WMWHSE1`

### Error: "Timeout"

**Causa**: La conexión tarda demasiado.

**Solución**:
1. Aumenta el timeout en `.env`:
   ```bash
   DB_TIMEOUT=60
   ```
2. En DBeaver, aumenta `loginTimeout` en Driver properties

### Error: "Too many connections"

**Causa**: Se alcanzó el límite de conexiones del pool.

**Solución**:
1. Cierra conexiones no utilizadas
2. Ajusta el pool:
   ```bash
   DB_POOL_MAX_SIZE=10
   DB_POOL_MAX_IDLE_TIME=180.0
   ```

---

## Configuración ODBC (Windows)

Para usar ODBC en Windows:

### Paso 1: Instalar IBM DB2 Driver

1. Descarga IBM Data Server Client de IBM
2. Instala el driver ODBC
3. Reinicia el equipo

### Paso 2: Configurar DSN

1. Abre **ODBC Data Sources (64-bit)**
2. Ve a **System DSN**
3. Click en **Add...**
4. Selecciona **IBM DB2 ODBC DRIVER**
5. Configura:
   - Data source name: `WM260BASD`
   - Database alias: `WM260BASD`
   - Description: `Manhattan WMS CEDIS 427`

### Paso 3: Probar DSN

1. En la configuración del DSN, click en **Test**
2. Ingresa usuario y contraseña
3. Verifica que la conexión sea exitosa

---

## Referencias

- [DBeaver - Create Connection](https://dbeaver.com/docs/dbeaver/Create-Connection/)
- [DBeaver - Connection Types](https://dbeaver.com/docs/dbeaver/Connection-Types/)
- [IBM DB2 Documentation](https://www.ibm.com/docs/en/db2)
- [ibm_db Python Driver](https://github.com/ibmdb/python-ibmdb)

---

## Contacto y Soporte

**Equipo de Sistemas CEDIS 427**
- Extensión: 4336
- Email: siterfvh@chedraui.com.mx

**Responsables**:
- Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Díaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas

---

**Versión**: 1.0
**Última actualización**: Noviembre 2025
**© 2025 Tiendas Chedraui S.A. de C.V.**
