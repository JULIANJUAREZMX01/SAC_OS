# 🛠️ Sistema de Mantenimiento Windows - CEDIS Chedraui 427

> **Scripts de limpieza, diagnóstico y optimización para sistemas Windows**

---

## 📋 Descripción

Colección completa de scripts de mantenimiento para sistemas Windows, organizados por categoría y con un menú interactivo para facilitar su ejecución.

**Desarrollado por:** Julián Alexander Juárez Alvarado (ADMJAJA)
**Cargo:** Jefe de Sistemas - CEDIS Chedraui Logística Cancún
**Organización:** Tiendas Chedraui S.A. de C.V.

---

## 🚀 Inicio Rápido

### Ejecutar el Menú Principal

```cmd
# Ejecutar como Administrador
menu_principal.bat
```

### Ejecutar la Limpieza Completa

```powershell
# Ejecutar PowerShell como Administrador
powershell -ExecutionPolicy Bypass -File "07_completo\limpieza_completa.ps1"
```

---

## 📁 Estructura de Carpetas

```
mantenimiento_windows/
│
├── menu_principal.bat          # Menú interactivo principal
├── README.md                   # Esta documentación
│
├── 01_limpieza/                # Scripts de limpieza del sistema
│   ├── limpiar_disco.bat       # Liberador de espacio en disco
│   ├── limpiar_temporales.bat  # Limpiar archivos temporales
│   └── limpiar_dns.bat         # Limpiar caché DNS
│
├── 02_diagnostico/             # Scripts de diagnóstico y reparación
│   ├── verificar_sistema.bat   # SFC + DISM
│   ├── verificar_disco.bat     # CHKDSK
│   └── salud_disco.bat         # Estado de salud del disco
│
├── 03_optimizacion/            # Scripts de optimización de rendimiento
│   ├── desfragmentar_hdd.bat   # Desfragmentar HDD (NO usar en SSD)
│   ├── optimizar_ssd.bat       # TRIM para SSD
│   └── limpiar_actualizaciones.bat  # Limpiar archivos de Windows Update
│
├── 04_servicios/               # Gestión de servicios y procesos
│   ├── ver_servicios.ps1       # Ver servicios en ejecución
│   ├── ver_procesos_cpu.ps1    # Top 10 procesos por CPU
│   ├── ver_procesos_memoria.ps1 # Top 10 procesos por memoria
│   └── deshabilitar_servicios_telemetria.bat  # Deshabilitar telemetría
│
├── 05_red/                     # Optimización de red
│   ├── resetear_red.bat        # Reset completo de configuración de red
│   └── optimizar_tcpip.bat     # Optimizar TCP/IP
│
├── 06_inicio/                  # Optimización de inicio
│   ├── ver_programas_inicio.bat # Ver programas de inicio
│   ├── deshabilitar_inicio_rapido.ps1  # Deshabilitar Fast Startup
│   └── limpiar_cache_iconos.bat # Limpiar caché de iconos
│
└── 07_completo/                # Scripts de limpieza completa
    ├── limpieza_completa.ps1   # Script maestro de limpieza
    └── vaciar_papelera.ps1     # Vaciar papelera de reciclaje
```

---

## 📊 Categorías de Scripts

### 1️⃣ Limpieza del Sistema

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `limpiar_disco.bat` | Ejecuta el Liberador de Espacio en Disco de Windows | 5-15 min |
| `limpiar_temporales.bat` | Elimina archivos temporales del usuario y sistema | 1-5 min |
| `limpiar_dns.bat` | Limpia la caché DNS y renueva configuración IP | < 1 min |

### 2️⃣ Diagnóstico y Reparación

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `verificar_sistema.bat` | Ejecuta SFC + DISM para reparar archivos del sistema | 30-60 min |
| `verificar_disco.bat` | Programa CHKDSK para el próximo reinicio | Requiere reinicio |
| `salud_disco.bat` | Muestra estado de salud de los discos | < 1 min |

### 3️⃣ Optimización de Rendimiento

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `desfragmentar_hdd.bat` | Desfragmenta discos HDD (**NO usar en SSD**) | 1-4 horas |
| `optimizar_ssd.bat` | Ejecuta TRIM para optimizar SSD | < 5 min |
| `limpiar_actualizaciones.bat` | Limpia archivos obsoletos de Windows Update | 10-30 min |

### 4️⃣ Gestión de Servicios y Procesos

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `ver_servicios.ps1` | Lista servicios en ejecución | < 1 min |
| `ver_procesos_cpu.ps1` | Muestra los 10 procesos que más CPU consumen | < 1 min |
| `ver_procesos_memoria.ps1` | Muestra los 10 procesos que más memoria consumen | < 1 min |
| `deshabilitar_servicios_telemetria.bat` | Deshabilita servicios de telemetría de Microsoft | < 1 min |

### 5️⃣ Optimización de Red

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `resetear_red.bat` | Resetea completamente la configuración de red | < 1 min |
| `optimizar_tcpip.bat` | Optimiza la configuración TCP/IP | < 1 min |

### 6️⃣ Optimización de Inicio

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `ver_programas_inicio.bat` | Lista todos los programas de inicio | < 1 min |
| `deshabilitar_inicio_rapido.ps1` | Deshabilita Fast Startup (si causa problemas) | < 1 min |
| `limpiar_cache_iconos.bat` | Limpia la caché de iconos de Windows | < 1 min |

### 7️⃣ Limpieza Completa

| Script | Descripción | Tiempo Estimado |
|--------|-------------|-----------------|
| `limpieza_completa.ps1` | Script maestro que ejecuta limpieza automatizada | 15-45 min |
| `vaciar_papelera.ps1` | Vacía la papelera de reciclaje | < 1 min |

---

## ⚠️ Requisitos Importantes

### Privilegios de Administrador

**TODOS los scripts requieren ejecutarse como Administrador:**

1. Clic derecho en el archivo `.bat` o `.ps1`
2. Seleccionar "Ejecutar como administrador"

### Para scripts PowerShell (.ps1)

Si recibe error de política de ejecución, use:

```powershell
powershell -ExecutionPolicy Bypass -File "nombre_script.ps1"
```

---

## 🔒 Advertencias de Seguridad

### ⚡ Desfragmentación

- **NUNCA** ejecutar `desfragmentar_hdd.bat` en discos **SSD**
- La desfragmentación en SSD reduce su vida útil
- Use `optimizar_ssd.bat` para discos SSD

### 🔌 Verificación de Disco (CHKDSK)

- El disco del sistema requiere **reinicio** para verificarse
- Guarde todo su trabajo antes de ejecutar
- El proceso puede tomar horas dependiendo del tamaño del disco

### 🌐 Reset de Red

- Ejecutar `resetear_red.bat` **desconectará temporalmente** la red
- Requiere **reinicio** para aplicar todos los cambios
- Puede necesitar reconfigurar conexiones VPN o WiFi

### 🚫 Servicios de Telemetría

- Deshabilitar telemetría puede afectar diagnósticos de Microsoft
- Es seguro para uso empresarial
- Mejora el rendimiento al reducir procesos en segundo plano

---

## 💡 Recomendaciones de Uso

### Mantenimiento Semanal

1. Ejecutar `limpiar_temporales.bat`
2. Ejecutar `limpiar_dns.bat`
3. Vaciar papelera de reciclaje

### Mantenimiento Mensual

1. Ejecutar `limpieza_completa.ps1`
2. Ejecutar `limpiar_actualizaciones.bat`
3. Revisar programas de inicio

### Mantenimiento Trimestral

1. Ejecutar `verificar_sistema.bat` (SFC + DISM)
2. Ejecutar `verificar_disco.bat` (CHKDSK)
3. Verificar salud del disco

---

## 📈 Beneficios Esperados

| Área | Mejora |
|------|--------|
| Espacio en disco | +5-20 GB liberados |
| Tiempo de arranque | -10-30 segundos |
| Rendimiento general | +10-25% |
| Estabilidad | Menos errores y congelamientos |
| Red | Mejor velocidad de conexión |

---

## 🤝 Soporte

**CEDIS Cancún 427**
Tiendas Chedraui S.A. de C.V.
Región Sureste

**Equipo de Sistemas:**
- Julián Alexander Juárez Alvarado (ADMJAJA) - Jefe de Sistemas
- Larry Adanael Basto Díaz - Analista de Sistemas
- Adrian Quintana Zuñiga - Analista de Sistemas

---

## 📜 Licencia

© 2025 Tiendas Chedraui S.A. de C.V. - Todos los derechos reservados.

Uso exclusivo para equipos de la organización.

---

> *"Las máquinas y los sistemas al servicio de los analistas"*
