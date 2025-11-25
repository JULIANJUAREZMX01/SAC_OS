@echo off

:: =============================================================
:: SACITY & dhell Installation Script for MC9190 (Windows Embedded)
:: -------------------------------------------------------------
:: Prerequisitos:
::   1. Conexión USB al dispositivo MC9190 con acceso a su disco
::   2. Python 3.11 (portable) instalado en el MC9190 o disponible en PATH
::   3. Permisos de administrador en el MC9190
:: =============================================================

:: 1. Definir ruta del dispositivo (asumimos que el MC9190 se monta como X:)
set DEVICE_DRIVE=E:
if not exist %DEVICE_DRIVE% (
    echo [ERROR] No se detecta la unidad %DEVICE_DRIVE%. Verifique la conexión USB.
    goto :eof
)

:: 2. Copiar el proyecto al dispositivo
echo Copiando archivos al dispositivo %DEVICE_DRIVE%\SACITY ...
xcopy "C:\Users\QUINTANA\.gemini\antigravity\scratch\SAC_V01_427_ADMJAJA" "%DEVICE_DRIVE%\SACITY" /E /I /H /Y
if %errorlevel% neq 0 (
    echo [ERROR] Error al copiar los archivos.
    goto :eof
)
:: 3. Copiar binarios Telnet y otros recursos desde ROOT_DIR
if not exist "%DEVICE_DRIVE%\SACITY\bin" (
    mkdir "%DEVICE_DRIVE%\SACITY\bin"
)
xcopy "E:\ROOT_DIR\*" "%DEVICE_DRIVE%\SACITY\bin" /E /I /H /Y
if %errorlevel% neq 0 (
    echo [ERROR] Error al copiar los binarios Telnet.
    goto :eof
)

:: 3. Crear archivo .env a partir del ejemplo
if not exist "%DEVICE_DRIVE%\SACITY\.env" (
    copy "%DEVICE_DRIVE%\SACITY\.env.example" "%DEVICE_DRIVE%\SACITY\.env"
    echo [INFO] Archivo .env creado. Edite %DEVICE_DRIVE%\SACITY\.env con sus credenciales.
) else (
    echo [INFO] Archivo .env ya existe, se mantendrá sin cambios.
)

:: 4. Instalar dependencias con pip
pushd "%DEVICE_DRIVE%\SACITY"
if not exist "venv" (
    echo Creando entorno virtual ...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Instalando paquetes requeridos ...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Falló la instalación de dependencias.
    popd
    goto :eof
)

:: 5. Ejecutar script de instalación del proyecto
python instalar_sac.py
if %errorlevel% neq 0 (
    echo [ERROR] La instalación del proyecto falló.
    popd
    goto :eof
)

:: 6. Registrar SACITY como servicio Windows (opcional)
::   El script deploy\sac_windows_service.py contiene la lógica para crear el servicio.
python deploy\sac_windows_service.py install
if %errorlevel% neq 0 (
    echo [WARN] No se pudo registrar el servicio. Puede hacerlo manualmente.
) else (
    echo [INFO] Servicio SACITY instalado correctamente.
)

popd

:: 7. Lanzar la shell dhell para validar la instalación
pushd "%DEVICE_DRIVE%\SACITY"
call venv\Scripts\activate.bat
python SAC.py
popd

echo Instalación completada.
pause
