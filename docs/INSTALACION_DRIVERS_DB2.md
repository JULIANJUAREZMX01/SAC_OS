# 📥 Instalación de Drivers IBM DB2 - SAC 2.0

> **Guía Completa para Configurar Conexión a Base de Datos Manhattan WMS**
>
> CEDIS Cancún 427 - Tiendas Chedraui
>
> Actualizado: Noviembre 2025

---

## 🎯 Objetivo

Instalar y configurar los drivers ODBC y librerías necesarias para que SAC 2.0 pueda conectarse a la base de datos IBM DB2 (Manhattan WMS) del CEDIS 427.

---

## ✅ Requisitos Previos

- ✅ Python 3.8 o superior
- ✅ Acceso de administrador en la computadora
- ✅ SAC 2.0 ya descargado e instalado
- ✅ pip actualizado (`pip install --upgrade pip`)
- ✅ Archivos .env configurados con credenciales

---

## 🪟 WINDOWS - Instalación Paso a Paso

### Paso 1: Descargar Drivers ODBC de IBM DB2

1. Visita: https://www.ibm.com/support/pages/ibm-data-server-driver-odbc-installation-instructions-windows

2. Descarga el instalador más reciente:
   - **IBM Data Server Runtime Client** o
   - **IBM Data Server Driver Package** (ODBC incluido)

3. Recomendamos versión **11.5.x** o superior

### Paso 2: Instalar Drivers ODBC

1. Ejecuta el instalador descargado
2. Selecciona: **Custom Installation**
3. Asegúrate de marcar:
   - ✅ IBM Data Server Runtime Client
   - ✅ IBM ODBC Driver
   - ✅ Add to PATH
4. Completa la instalación

### Paso 3: Configurar Data Source (Opcional pero Recomendado)

1. Ve a: **Panel de Control** → **Herramientas Administrativas** → **ODBC Data Source Administrator**
2. Click en: **Add**
3. Selecciona: **IBM DB2 ODBC DRIVER**
4. Configura:
   - **Data Source Name**: SAC427
   - **Server**: WM260BASD
   - **Port**: 50000
   - **Database**: WM260BASD
   - **User ID**: ADMJAJA
   - **Password**: [Tu contraseña]

5. Click: **Test Connection** (debe mostrar éxito)

### Paso 4: Instalar Librerías Python

```bash
# Abre PowerShell o CMD como Administrador

# Instalar pyodbc (para ODBC)
pip install pyodbc

# Instalar ibm_db (alternativa/respaldo)
pip install ibm-db ibm-db-sa

# Instalar SQLAlchemy (ORM)
pip install sqlalchemy

# Verificar instalación
python -c "import pyodbc; print('✅ pyodbc OK')"
python -c "import ibm_db; print('✅ ibm_db OK')"
```

### Paso 5: Verificar Conexión

```bash
# Ejecutar script de verificación
python verificar_integraciones.py

# Debe mostrar:
# ✅ Conexión a DB2 EXITOSA
# ✅ Email corporativo FUNCIONAL
```

---

## 🐧 LINUX (Ubuntu/Debian) - Instalación Paso a Paso

### Paso 1: Instalar Librerías del Sistema

```bash
# Actualizar lista de paquetes
sudo apt update

# Instalar librerías ODBC base
sudo apt install -y unixodbc unixodbc-dev

# Instalar dependencias
sudo apt install -y libssl-dev libkrb5-dev

# Instalar Python dev headers (necesario para compilar pyodbc)
sudo apt install -y python3-dev python3-pip
```

### Paso 2: Descargar e Instalar Drivers IBM DB2

```bash
# Crear directorio para drivers
mkdir -p ~/ibm_db_drivers
cd ~/ibm_db_drivers

# Descargar desde IBM (reemplaza VERSION con la versión actual)
# Opción 1: ODBC Driver Package
wget https://download.ibm.com/ibmdl/export/pub/software/data/db2/drivers/odbc_cli/linuxx64_odbc/db2_cli_odbc_linuxx64_v11.5.4_0.zip

# Opción 2: Si el link anterior no funciona, visita:
# https://www.ibm.com/support/pages/ibm-data-server-driver-odbc-installation-instructions-linux

# Descomprimir
unzip db2_cli_odbc_linuxx64_v11.5.4_0.zip

# Instalar
cd db2_cli_odbc_linuxx64_v11.5.4_0
sudo ./installFixPack

# Aceptar términos y completar instalación
```

### Paso 3: Configurar Drivers ODBC

```bash
# Editar odbcinst.ini
sudo nano /etc/odbcinst.ini

# Agregar esta sección (si no existe):
[IBM DB2 ODBC DRIVER]
Description = IBM Data Server Driver for ODBC and CLI
Driver = /opt/IBM/db2/odbc_cli/lib/libdb2o.so
Driver64 = /opt/IBM/db2/odbc_cli/lib64/libdb2o.so
Setup = /opt/IBM/db2/odbc_cli/lib/libdb2s.so
Setup64 = /opt/IBM/db2/odbc_cli/lib64/libdb2s.so
FileUsage = 1
```

### Paso 4: Instalar Librerías Python

```bash
# Instalar pyodbc (puede requerir compilación)
pip install pyodbc

# Si hay errores, intentar:
pip install --no-binary :all: pyodbc

# Instalar ibm_db
pip install ibm-db ibm-db-sa

# Instalar SQLAlchemy
pip install sqlalchemy

# Verificar instalación
python3 -c "import pyodbc; print('✅ pyodbc OK')"
python3 -c "import ibm_db; print('✅ ibm_db OK')"
```

### Paso 5: Configurar Variables de Entorno

```bash
# Agregar a ~/.bashrc o ~/.bash_profile
export DB2PATH=/opt/IBM/db2/odbc_cli
export LD_LIBRARY_PATH=$DB2PATH/lib:$DB2PATH/lib64:$LD_LIBRARY_PATH
export PATH=$DB2PATH/bin:$PATH

# Aplicar cambios
source ~/.bashrc
```

### Paso 6: Verificar Conexión

```bash
# Ejecutar script de verificación
python3 verificar_integraciones.py

# Debe mostrar:
# ✅ Conexión a DB2 EXITOSA
# ✅ Email corporativo FUNCIONAL
```

---

## 🍎 macOS - Instalación Paso a Paso

### Paso 1: Instalar Homebrew (si no está instalado)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Paso 2: Instalar Librerías Necesarias

```bash
# Actualizar Homebrew
brew update

# Instalar ODBC
brew install unixodbc

# Instalar OpenSSL y Kerberos
brew install openssl krb5
```

### Paso 3: Descargar e Instalar Drivers IBM DB2

```bash
# Crear directorio
mkdir -p ~/ibm_db_drivers
cd ~/ibm_db_drivers

# Descargar (versión macOS)
# Visita: https://www.ibm.com/support/pages/ibm-data-server-driver-odbc-installation-instructions-mac

# Descomprimir e instalar
# Seguir instrucciones del instalador
```

### Paso 4: Instalar Librerías Python

```bash
# Instalar pyodbc
pip3 install pyodbc

# Instalar ibm_db (alternativa)
pip3 install ibm-db ibm-db-sa

# Instalar SQLAlchemy
pip3 install sqlalchemy
```

### Paso 5: Verificar Conexión

```bash
python3 verificar_integraciones.py
```

---

## 🔧 Solución de Problemas Comunes

### Error: "Can't open lib 'libodbc.so.2'"

**Solución:**
```bash
# Linux: Instalar unixodbc
sudo apt install -y unixodbc unixodbc-dev

# O crear link simbólico
sudo find / -name "libodbc.so*" 2>/dev/null
sudo ln -s /usr/lib/x86_64-linux-gnu/libodbc.so.2 /usr/lib/libodbc.so.2
```

### Error: "Driver not found"

**Solución:**
1. Verificar que los drivers ODBC estén instalados
2. Verificar ruta en `/etc/odbcinst.ini` (Linux)
3. Ejecutar: `odbcinst -j` para ver configuración

### Error: "Authentication failed"

**Solución:**
- Verificar credenciales en .env
- Probar conectividad: `telnet WM260BASD 50000`
- Verificar usuario en DB2

### Error: "Connection timeout"

**Solución:**
- Verificar conectividad de red a WM260BASD
- Probar ping: `ping WM260BASD`
- Verificar firewall/proxy
- Aumentar timeout en .env: `DB_TIMEOUT=60`

---

## ✅ Verificación Final

Una vez instalado todo, ejecuta:

```bash
python verificar_integraciones.py
```

**Debe mostrar:**

```
═══════════════════════════════════════════════════════════════════
RESUMEN DE VERIFICACIÓN
═══════════════════════════════════════════════════════════════════

Variables de Entorno:  ✅ CONFIGURADO
Base de Datos DB2:     ✅ FUNCIONAL
Email Corporativo:     ✅ FUNCIONAL

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║    ✅ SAC 2.0 ESTÁ COMPLETAMENTE OPERACIONAL                      ║
║    Todas las integraciones funcionan correctamente                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 📚 Referencias Oficiales

| Tema | Enlace |
|------|--------|
| IBM Data Server Driver ODBC | https://www.ibm.com/support/pages/ibm-data-server-driver-odbc-cli |
| Documentación DB2 | https://www.ibm.com/docs/en/db2 |
| pyodbc Documentation | https://github.com/mkleehammer/pyodbc/wiki |
| IBM DB2 Python | https://github.com/ibmdb/python-ibmdb |
| SQLAlchemy | https://docs.sqlalchemy.org/ |

---

## 📞 Soporte

Si tienes problemas durante la instalación:

1. **Revisa los logs**: `cat ~/.sac2.0_install.log`
2. **Verifica credenciales**: Revisa archivo `.env`
3. **Contacta a Sistemas**:
   - Email: siterfvh@chedraui.com.mx
   - Ext: 4336
   - CEDIS 427: Sistemas

---

## 🎯 Próximos Pasos

Una vez verificado todo:

1. ✅ Ejecutar `python main.py` para iniciar SAC
2. ✅ Ejecutar `python -m modules.api_rest` para iniciar API REST
3. ✅ Acceder a documentación: http://localhost:8000/docs

---

**Documento versión**: 1.0
**Última actualización**: Noviembre 2025
**Responsable**: ADMJAJA - Jefe de Sistemas CEDIS 427
