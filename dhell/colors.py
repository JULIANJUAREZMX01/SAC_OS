COLORES = {
    # Rojos (Dominantes)
    'ROJO_PRINCIPAL': '\033[38;2;255;0;0m',      # Rojo puro, brillante
    'ROJO_OSCURO':    '\033[38;2;139;0;0m',      # Rojo sangre/oscuro para fondos o bloques
    'ROJO_NEON':      '\033[38;2;255;50;50m',    # Rojo neón para destacados
    
    # Acentos (Jugar con ellos)
    'NARANJA':        '\033[38;2;255;100;0m',    # Naranja fuego
    'VERDE_VIRUS':    '\033[38;2;50;255;50m',    # Verde tóxico/hacker
    'AZUL_CYBER':     '\033[38;2;0;200;255m',    # Azul eléctrico
    'GRIS_METAL':     '\033[38;2;100;100;100m',  # Gris oscuro metálico
    'GRIS_CLARO':     '\033[38;2;180;180;180m',  # Gris plata
    
    # Utilidades
    'FONDO_NEGRO':    '\033[48;2;0;0;0m',        # Fondo negro explícito
    'RESET':          '\033[0m'
}

# Alias para compatibilidad con código anterior, pero redirigidos a la nueva estética
COLORES['ROJO'] = COLORES['ROJO_PRINCIPAL']
COLORES['GRIS'] = COLORES['GRIS_METAL']
