import time
import sys
import random
import codecs
from .colors import COLORES
from . import config

# Configuración de colores (Dominio del Rojo - Seguridad)
ROJO = COLORES['ROJO_PRINCIPAL']
ROJO_OSCURO = COLORES['ROJO_OSCURO']
ROJO_NEON = COLORES['ROJO_NEON']
NARANJA = COLORES['NARANJA']
VERDE = COLORES['VERDE_VIRUS'] # Reutilizamos el verde neón para "Autorizado"
AZUL = COLORES['AZUL_CYBER']
GRIS = COLORES['GRIS_METAL']
RESET = COLORES['RESET']

def asegurar_utf8():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def limpiar_linea():
    sys.stdout.write('\r' + ' ' * 80 + '\r')
    sys.stdout.flush()

def sleep_optimizado(segundos):
    """Aplica el multiplicador de velocidad global"""
    time.sleep(segundos * config.SPEED_MULTIPLIER)

def efecto_glitch(texto, color_final=ROJO, probabilidad=0.1):
    """Efecto de estabilización de datos (menos caótico que el virus)"""
    if config.ECO_MODE:
        sys.stdout.write(f"{color_final}{texto}{RESET}\n")
        return

    chars_code = "010101XYZ-[]"
    buffer = list(texto)
    
    pasos = 1 if config.ECO_MODE else 2
    
    for _ in range(pasos):
        temp_str = ""
        for char in buffer:
            if char != " " and random.random() < probabilidad:
                temp_str += random.choice(chars_code)
            else:
                temp_str += char
        sys.stdout.write(f"\r{ROJO_OSCURO}{temp_str}{RESET}")
        sys.stdout.flush()
        sleep_optimizado(0.05)
    
    sys.stdout.write(f"\r{color_final}{texto}{RESET}\n")

def barra_seguridad(progreso, ancho=40):
    """Barra de progreso de escaneo de seguridad"""
    llenos = int(ancho * (progreso / 100))
    vacios = ancho - llenos
    
    # Barra sólida y autoritaria
    barra = f"{ROJO_NEON}{'█' * llenos}{GRIS}{'=' * vacios}{RESET}"
    return barra

def animacion_inicio_sistema():
    """Arranque de Protocolo de Seguridad"""
    limpiar_linea()
    print(f"{ROJO_OSCURO}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{ROJO_OSCURO}║ {ROJO_NEON}SACITY DEFENSE GRID v1.0 - SECURITY PROTOCOL ACTIVE      {ROJO_OSCURO}║{RESET}")
    print(f"{ROJO_OSCURO}╚══════════════════════════════════════════════════════════════╝{RESET}")
    sleep_optimizado(0.5)
    
    if config.ECO_MODE:
        print(f"{ROJO}>>> PROTOCOLO LIGERO ACTIVO{RESET}")
        return

    modulos = ["FIREWALL", "ENCRIPTACION", "BIOMETRIA", "BASE_DATOS", "DHELL_UI"]
    for mod in modulos:
        sys.stdout.write(f"{ROJO}>>> INICIALIZANDO {mod}...")
        sys.stdout.flush()
        sleep_optimizado(0.2)
        sys.stdout.write(f"\r{ROJO}>>> {mod} [ {VERDE}VERIFICADO{ROJO} ]          \n")
        sleep_optimizado(0.1)
    
    print("")
    efecto_glitch("ESTABLECIENDO ENLACE SEGURO...", ROJO_NEON)
    sleep_optimizado(0.5)

def animacion_login():
    """Login de Alta Seguridad"""
    print(f"\n{ROJO_OSCURO}--- CONTROL DE ACCESO ---{RESET}")
    sys.stdout.write(f"{ROJO}IDENTIDAD > {RESET}")
    sleep_optimizado(0.5)
    
    if config.ECO_MODE:
        print(f"{ROJO_NEON}OPERADOR_427{RESET}")
    else:
        efecto_glitch("OPERADOR_427", ROJO_NEON, 0.2)
    
    sys.stdout.write(f"{ROJO}CREDENCIAL > {RESET}")
    sleep_optimizado(0.5)
    print(f"{ROJO_OSCURO}********{RESET}")
    
    sys.stdout.write(f"{ROJO}ANALIZANDO PERMISOS...{RESET}")
    sleep_optimizado(1)
    sys.stdout.write(f"\r{ROJO}ANALIZANDO PERMISOS... {VERDE}AUTORIZADO{RESET}\n")

def animacion_escaneo(tipo, dato):
    """Escaneo de Producto/Ubicación (Feedback Visual Crítico)"""
    print(f"\n{GRIS}--- ESCANER DE SEGURIDAD ---{RESET}")
    
    if not config.ECO_MODE:
        # Efecto de "Targeting"
        sys.stdout.write(f"\r{ROJO_OSCURO}[   ] ANALIZANDO OBJETIVO...{RESET}")
        sys.stdout.flush()
        sleep_optimizado(0.1)
        sys.stdout.write(f"\r{ROJO_NEON}[ O ] ANALIZANDO OBJETIVO...{RESET}")
        sys.stdout.flush()
        sleep_optimizado(0.1)
    
    limpiar_linea()
    print(f"{ROJO_NEON}>>> OBJETIVO VALIDADO [{tipo}]{RESET}")
    
    if tipo == "OC":
        efecto_glitch(f"DATA: {dato}", NARANJA)
        print(f"{ROJO}ESTADO: {VERDE}CONFORME A PROTOCOLO (RECIBO){RESET}")
    elif tipo == "UPC":
        efecto_glitch(f"PROD: {dato}", AZUL)
        print(f"{ROJO}SKU: {ROJO_OSCURO}750123456789{RESET}")
    
    print(f"{ROJO_OSCURO}----------------------{RESET}")

def animacion_alerta(mensaje):
    """Alerta de Seguridad del Sistema"""
    print("")
    iteraciones = 2 if config.ECO_MODE else 4
    for i in range(iteraciones):
        color = ROJO_NEON if i % 2 == 0 else ROJO_OSCURO
        sys.stdout.write(f"\r{color}⚠ ALERTA DE SEGURIDAD: {mensaje} ⚠{RESET}")
        sys.stdout.flush()
        sleep_optimizado(0.2)
    print(f"\n{NARANJA}>>> REGISTRANDO INCIDENTE EN BITACORA{RESET}\n")

def animacion_descarga():
    """Sincronización de Datos Segura"""
    print(f"\n{ROJO}>>> SINCRONIZANDO BASE DE DATOS...{RESET}")
    paso = 20 if config.ECO_MODE else 5
    for i in range(0, 101, paso):
        sys.stdout.write(f"\r{barra_seguridad(i)} {ROJO}{i}%{RESET}")
        sys.stdout.flush()
        sleep_optimizado(0.05)
    sys.stdout.write(f"\r{barra_seguridad(100)} {ROJO}100%{RESET}")
    print(f"\n{VERDE}>>> DATOS ASEGURADOS{RESET}")

def demo_seguridad():
    asegurar_utf8()
    animacion_inicio_sistema()
    sleep_optimizado(1)
    animacion_login()
    sleep_optimizado(1)
    animacion_escaneo("OC", "ORDEN_450099")
    sleep_optimizado(1)
    animacion_alerta("INTENTO DE ACCESO NO AUTORIZADO")
    sleep_optimizado(1)
    animacion_descarga()

if __name__ == "__main__":
    demo_seguridad()
