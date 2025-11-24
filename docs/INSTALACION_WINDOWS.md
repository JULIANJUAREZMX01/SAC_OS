# Guía de Instalación en Windows

## Sistema de Automatización de Consultas (SAC)
### CEDIS Cancún 427 - Tiendas Chedraui

---

## Requisitos Previos

### 1. Python 3.10 o superior
- Descargar desde: https://www.python.org/downloads/
- **IMPORTANTE**: Durante la instalación, marcar la opción **"Add Python to PATH"**

### 2. Drivers ODBC para IBM DB2 (si vas a conectar a la base de datos)
- Descargar IBM Data Server Driver Package desde:
  https://www.ibm.com/support/pages/ibm-data-server-driver-package-support-lifecycle-guidance

---

## Instalación Rápida (Recomendado)

### Opción A: Usando el script BAT (más simple)

1. Abre el Explorador de archivos
2. Navega a la carpeta del proyecto SAC
3. Haz doble clic en `setup_windows.bat`
4. Espera a que termine la instalación

### Opción B: Usando PowerShell

1. Abre PowerShell como Administrador
2. Ejecuta (solo una vez, para habilitar scripts):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Navega al directorio del proyecto:
   ```powershell
   cd "C:\ruta\al\proyecto\SAC"
   ```
4. Ejecuta el instalador:
   ```powershell
   .\setup_windows.ps1
   ```

---

## Instalación Manual

### Paso 1: Abrir CMD o PowerShell

Presiona `Win + R`, escribe `cmd` o `powershell`, y presiona Enter.

### Paso 2: Navegar al directorio del proyecto

```cmd
cd C:\ruta\al\proyecto\SAC
```

### Paso 3: Crear directorio output (si no existe)

```cmd
mkdir output
mkdir output\logs
mkdir output\resultados
```

### Paso 4: Actualizar pip

```cmd
python -m pip install --upgrade pip
```

### Paso 5: Instalar dependencias mínimas

```cmd
python -m pip install --user -r requirements-minimal.txt
```

### Paso 6: Si la instalación mínima funciona, instalar completas (opcional)

```cmd
python -m pip install --user -r requirements.txt
```

---

## Solución de Problemas Comunes

### Error: "La ejecución de scripts está deshabilitada"

Este error aparece en PowerShell cuando la política de ejecución no permite scripts.

**Solución:**
1. Abre PowerShell como Administrador
2. Ejecuta:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Confirma con "S" (Sí)
4. Intenta de nuevo

**Alternativa:** Usa el archivo `setup_windows.bat` en lugar de PowerShell.

---

### Error: "Failed to build pandas/numpy"

Este error ocurre cuando pip intenta compilar desde código fuente porque no encuentra wheels precompilados.

**Causas comunes:**
- Python 3.13 muy reciente (algunas librerías aún no tienen wheels)
- Falta Visual C++ Build Tools

**Solución 1 - Usar versiones específicas:**
```cmd
python -m pip install --user numpy==2.1.3
python -m pip install --user pandas==2.2.3
```

**Solución 2 - Instalar Visual C++ Build Tools:**
1. Descargar Visual Studio Build Tools:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Instalar con la opción "Herramientas de compilación de C++"
3. Reiniciar e intentar de nuevo

**Solución 3 - Usar Python 3.12 o 3.11:**
Python 3.13 es muy reciente. Si tienes problemas, considera usar Python 3.12.

---

### Error: "ModuleNotFoundError: No module named 'xxx'"

**Solución:**
```cmd
python -m pip install --user nombre_del_modulo
```

---

### Error: "pip install --user" no funciona

Puede ocurrir en entornos corporativos con restricciones.

**Solución:**
1. Crear un entorno virtual:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements-minimal.txt
   ```

---

### Error: "Access Denied" o permisos

**Solución:**
- Ejecuta CMD o PowerShell como Administrador
- O usa `--user` flag: `pip install --user paquete`

---

## Verificación de la Instalación

Ejecuta el verificador del sistema:

```cmd
python verificar_sistema.py
```

Deberías ver algo como:
```
✓ pandas instalado
✓ numpy instalado
✓ openpyxl instalado
✓ python-dotenv instalado
✓ Configuración válida
```

---

## Configuración Post-Instalación

### 1. Crear archivo .env

Copia la plantilla:
```cmd
copy config\.env.example .env
```

### 2. Editar credenciales

Abre `.env` con Notepad o tu editor preferido:
```cmd
notepad .env
```

Configura:
```ini
# Base de datos
DB_USER=tu_usuario_db2
DB_PASSWORD=tu_contraseña_db2

# Email corporativo
EMAIL_USER=tu_email@chedraui.com.mx
EMAIL_PASSWORD=tu_contraseña_email
```

### 3. Verificar configuración

```cmd
python config.py
```

---

## Ejecutar el Sistema

### Modo interactivo (menú)
```cmd
python main.py
```

### Validar una OC específica
```cmd
python main.py --oc OC12345678
```

### Ver ejemplos
```cmd
python examples.py
```

---

## Notas para Python 3.13

Python 3.13 es una versión muy reciente (octubre 2024). Algunas consideraciones:

1. **Usar versiones actualizadas**: El `requirements.txt` ya está configurado con versiones compatibles.

2. **Si hay problemas de compilación**: Instala las dependencias mínimas primero:
   ```cmd
   pip install -r requirements-minimal.txt
   ```

3. **Alternativa recomendada**: Si tienes muchos problemas, considera usar Python 3.12 que tiene mejor soporte de librerías.

---

## Soporte

**Equipo de Sistemas - CEDIS Cancún 427**
- Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Díaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas

---

**© 2025 Tiendas Chedraui S.A. de C.V.**
