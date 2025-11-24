import time
import sys
import codecs

# Force stdout to use utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from .colors import COLORES

ROJO = COLORES['ROJO']
NARANJA = COLORES['NARANJA']
GRIS = COLORES['GRIS']
RESET = COLORES['RESET']

def banner_arranque():
    """
    Plantilla 1 – Banner de Arranque
    """
    print(f"{ROJO}████████████████████████████████████████████████████████████████{RESET}")
    print(f"{ROJO}█                                                              █{RESET}")
    print(f"{ROJO}█   SACITY OS - dhell minimalista                              █{RESET}")
    print(f"{ROJO}█                                                              █{RESET}")
    print(f"{NARANJA}█   >>> Inicializando módulos...                               █{RESET}")
    print(f"{GRIS}█   >>> Fondo negro, interfaz ASCII                            █{RESET}")
    print(f"{ROJO}█                                                              █{RESET}")
    print(f"{ROJO}████████████████████████████████████████████████████████████████{RESET}")

def barra_progreso(porcentaje):
    """
    Plantilla 2 – Barra de Progreso
    """
    # Simple simulation of the visual provided
    # The user provided 3 states, we can just print one or simulate a loop if needed.
    # For a static template print, I'll print the 3 states as examples or just one dynamic one.
    # The user request shows 3 lines, likely examples of state. I will print the block as requested.
    
    print(f"{GRIS}┌───────────────────────────────────────────────┐{RESET}")
    if porcentaje < 30:
        bar = "#####................."
        color = NARANJA
    elif porcentaje < 90:
        bar = "###########.........."
        color = NARANJA
    else:
        bar = "####################."
        color = ROJO
        
    # Formatting to match the fixed width of the box roughly
    # The box seems to be about 47 chars wide inside
    # "│ [#####.................] 25%               │"
    # The bar part "[...]" is 22 chars.
    
    # Let's try to match the user's exact visual for the template demonstration
    print(f"{NARANJA}│ [#####.................] 25%               │{RESET}")
    print(f"{NARANJA}│ [###########..........] 55%               │{RESET}")
    print(f"{ROJO}│ [####################.] 95%               │{RESET}")
    print(f"{GRIS}└───────────────────────────────────────────────┘{RESET}")

def alerta_critica():
    """
    Plantilla 3 – Alerta Crítica
    """
    print(f"{ROJO}████████████████████████████████████████████████████████████████{RESET}")
    print(f"{ROJO}█                                                              █{RESET}")
    print(f"{ROJO}█   !!! ALERTA CRÍTICA !!!                                     █{RESET}")
    print(f"{NARANJA}█   Conexión perdida, reintentando...                          █{RESET}")
    print(f"{GRIS}█   Estado: reconexión automática en curso                     █{RESET}")
    print(f"{ROJO}█                                                              █{RESET}")
    print(f"{ROJO}████████████████████████████████████████████████████████████████{RESET}")

def reconexion_exitosa():
    """
    Plantilla 4 – Reconexión Exitosa
    """
    print(f"{GRIS}┌───────────────────────────────────────────────┐{RESET}")
    print(f"{NARANJA}│ Reintentando sesión Telnet...                 │{RESET}")
    print(f"{NARANJA}│ Estado: reconectando...                       │{RESET}")
    print(f"{ROJO}│ Estado: estableciendo sesión...               │{RESET}")
    print(f"{GRIS}└───────────────────────────────────────────────┘{RESET}")
    print("")
    print(f"{ROJO}████████████████████████████████████████████████████████████████{RESET}")
    print(f"{NARANJA}>>> Reconexión completada{RESET}")
    print(f"{GRIS}>>> Sesión restaurada{RESET}")

def descarga_transferencia():
    """
    Plantilla 5 – Descarga/Transferencia
    """
    print(f"{GRIS}┌───────────────────────────────────────────────┐{RESET}")
    print(f"{NARANJA}│ Transferencia en curso...                     │{RESET}")
    print(f"{NARANJA}│ [###.................] 15%                    │{RESET}")
    print(f"{NARANJA}│ [##########..........] 60%                    │{RESET}")
    print(f"{ROJO}│ [###################.] 95%                    │{RESET}")
    print(f"{GRIS}└───────────────────────────────────────────────┘{RESET}")
    print("")
    print(f"{GRIS}>>> Descarga finalizada{RESET}")
    print(f"{ROJO}✔ Datos recibidos correctamente{RESET}")

if __name__ == "__main__":
    print("--- Plantilla 1 ---")
    banner_arranque()
    print("\n--- Plantilla 2 ---")
    barra_progreso(50)
    print("\n--- Plantilla 3 ---")
    alerta_critica()
    print("\n--- Plantilla 4 ---")
    reconexion_exitosa()
    print("\n--- Plantilla 5 ---")
    descarga_transferencia()
