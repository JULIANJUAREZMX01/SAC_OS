# SACITY - Guía de Instalación de Drivers y Conexión

## Estado Actual del Dispositivo

Según la detección del sistema, el **Symbol MC9190** está conectado físicamente vía USB Cradle, pero los drivers tienen errores:

```
Status: Error - Symbol USB Sync Cradle
Status: Unknown - Symbol USB ActiveSync RNDIS
```

## Pasos para Establecer Conexión

### 1. Instalar Windows Mobile Device Center (WMDC)

**Descarga**: [Microsoft Download Center](https://www.microsoft.com/en-us/download/details.aspx?id=3182)

**Instalación**:
```powershell
# Ejecutar como Administrador
.\drvupdate-amd64.exe
```

**Verificar instalación**:
```powershell
Test-Path "C:\Program Files\Windows Mobile Device Center\wmdc.exe"
```

### 2. Instalar Drivers Symbol MC9190

**Descarga**: [Zebra Support](https://www.zebra.com/us/en/support-downloads/mobile-computers/handheld/mc9190-g.html)

Buscar: **"MC9190 USB Driver Package"** o **"Symbol USB ActiveSync Drivers"**

**Instalación**:
1. Desconectar el dispositivo de la cradle
2. Ejecutar el instalador de drivers como Administrador
3. Reiniciar el PC
4. Volver a conectar el dispositivo

### 3. Verificar Conexión

Ejecutar el script de conexión:
```powershell
cd C:\Users\QUINTANA\.sistemas_SAC\SAC_V01_427_ADMJAJA\sacity
python mc9190_connection.py
```

### 4. Transferir Archivos SACITY

Una vez establecida la conexión:

**Opción A - Via WMDC (Recomendado)**:
1. Abrir Windows Mobile Device Center
2. Hacer clic en "Explorador de archivos"
3. Navegar a `\Program Files\SACITY\`
4. Copiar los archivos:
   - `sacity_client_ce.py`
   - `sacity_tui.py`
   - `sacity_shell.py`
   - `sacity_config.json`

**Opción B - Via Script**:
```python
python sacity_installer_suite.py --auto
```

## Información del Dispositivo (De las imágenes)

```
Scanner:    SE960
Display:    PJ037PD-01A
Keyboard:   53-Key Keyboard
Platform:   Windows Embedded
WLAN:       Jedi 802.11bga
USB:        Processor USB (0x01)
Flash:      1GB
RAM:        256MB
```

## Troubleshooting

### Error: "Dispositivo no reconocido"
- Verificar que la cradle esté conectada correctamente
- Probar con otro puerto USB
- Verificar que el dispositivo esté encendido

### Error: "RAPI no disponible"
- Instalar/Reinstalar WMDC
- Verificar que el servicio RapiMgr esté corriendo:
  ```powershell
  Get-Service RapiMgr
  Start-Service RapiMgr
  ```

### Error: "Drivers no instalados"
- Desinstalar drivers antiguos desde Device Manager
- Reinstalar drivers de Symbol
- Reiniciar PC

## Próximos Pasos

1. ✅ Proyecto consolidado en: `C:\Users\QUINTANA\.sistemas_SAC\SAC_V01_427_ADMJAJA\sacity\`
2. ⏳ Instalar WMDC
3. ⏳ Instalar Drivers Symbol
4. ⏳ Establecer conexión RAPI
5. ⏳ Transferir archivos SACITY
6. ⏳ Configurar autostart en el dispositivo
