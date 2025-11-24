# Guía de Inicio Rápido - SAC

## Instalación en 5 minutos

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciales
```bash
cp env .env
# Editar .env con tus credenciales
```

### 3. Verificar instalación
```bash
python verificar_sistema.py
```

### 4. Ejecutar
```bash
python main.py
```

## Modos de Ejecución

| Comando | Descripción |
|---------|-------------|
| `python main.py` | Menú interactivo |
| `python main.py --oc OC123` | Validar OC específica |
| `python maestro.py` | Orquestador maestro |
| `python dashboard.py` | Dashboard web |

---
© 2025 CEDIS Cancún 427
