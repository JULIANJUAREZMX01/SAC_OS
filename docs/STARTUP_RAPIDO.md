# ⚡ STARTUP RÁPIDO - 5 MINUTOS

## Sistema SAC v1.0 - CEDIS Cancún 427

Para usuarios con experiencia. Si es la primera vez, lee `PRODUCTION_READY.md`.

---

## 🚀 5 PASOS - 5 MINUTOS

### 1. Instalar Dependencias (2 minutos)
```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales (2 minutos)
```bash
python setup_env_seguro.py
# Responder preguntas interactivas
# Usuario DB2: tu_usuario
# Contraseña DB2: tu_contraseña
# Email corporativo: tu_email@chedraui.com.mx
# Contraseña email: tu_contraseña
```

### 3. Verificar Sistema (30 segundos)
```bash
python health_check.py
# ✅ LISTO PARA PRODUCCIÓN
```

### 4. Iniciar Sistema (30 segundos)
```bash
python production_startup.py
```

### 5. Usar la Aplicación
```bash
python main.py
# Selecciona opción del menú
```

---

## 🎯 OPERACIONES COMUNES

### Validar una OC
```bash
python main.py --oc OC123456789
```

### Generar Reporte Diario
```bash
python main.py --reporte-diario
```

### Ver Logs
```bash
tail -f output/logs/sac_427.log
```

### Monitoreo Continuo
```bash
python production_startup.py --monitor
```

---

## ⚠️ PROBLEMAS RÁPIDOS

| Problema | Solución |
|----------|----------|
| "No module named..." | `pip install -r requirements.txt` |
| ".env not found" | `python setup_env_seguro.py` |
| "Wrong credentials" | Ejecutar `python setup_env_seguro.py` de nuevo |
| "Can't connect to DB" | Verificar conectividad y credenciales |
| "Email not working" | Verificar credenciales de email y conectividad |

---

## 📞 HELP

```bash
python main.py --help
python health_check.py --help
python production_startup.py --help
```

---

**¡Listo para trabajar!** 🎉
