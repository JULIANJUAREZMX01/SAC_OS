# Scripts Deprecados (Legacy)

Esta carpeta contiene scripts que fueron reemplazados por el nuevo **Script Maestro Unificado `SAC.py`**.

## Scripts Deprecados

| Script | Razon | Reemplazo |
|--------|-------|-----------|
| `INICIO_SAC.py` | Punto de entrada fragmentado | `SAC.py` |
| `sac_launcher.py` | Launcher redundante | `SAC.py` |

## Nuevo Punto de Entrada

A partir de la version 4.0, el **unico** script que necesita ejecutar es:

```bash
python SAC.py
```

### Opciones disponibles:

```bash
python SAC.py                     # Modo automatico (detecta e instala si es necesario)
python SAC.py --menu              # Menu principal
python SAC.py --instalar          # Forzar instalacion
python SAC.py --monitor           # Monitor en tiempo real
python SAC.py --validar OC123     # Validar OC especifica
python SAC.py --reporte           # Generar reporte diario
python SAC.py --daemon            # Modo servicio
python SAC.py --status            # Ver estado del sistema
python SAC.py --help              # Ayuda completa
```

## Ejecutores Actualizados

Los archivos ejecutores ahora apuntan a `SAC.py`:

- **Windows**: `EJECUTAR_SAC.bat` -> ejecuta `SAC.py`
- **Linux/Mac**: `ejecutar_sac.sh` -> ejecuta `SAC.py`

---

**NOTA**: Estos scripts se mantienen por historial. No deben ser ejecutados directamente.

Fecha de deprecacion: Noviembre 2025
