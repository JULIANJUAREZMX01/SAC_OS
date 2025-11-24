import sys
import time
import os
import shlex

# Importar módulos locales
from dhell.colors import COLORES
import dhell.animations as anim
from dhell.comms import SacityComms

# Shortcuts de colores
ROJO_NEON = COLORES['ROJO_NEON']
ROJO_OSCURO = COLORES['ROJO_OSCURO']
GRIS = COLORES['GRIS_METAL']
VERDE = COLORES['VERDE_VIRUS']
RESET = COLORES['RESET']
NARANJA = COLORES['NARANJA']

class SacityShell:
    def __init__(self):
        self.running = True
        self.prompt = f"{ROJO_NEON}SACITY>{RESET} "
        self.comms = SacityComms()
        self.user = "OPERADOR_427"
        
    def run(self):
        # Secuencia de inicio
        anim.asegurar_utf8()
        anim.animacion_inicio_sistema()
        anim.animacion_login()
        
        print(f"\n{ROJO_NEON}BIENVENIDO AL NUCLEO SACITY{RESET}")
        print(f"{GRIS}Escriba 'help' para lista de comandos.{RESET}")
        
        while self.running:
            try:
                # Input handling
                sys.stdout.write(self.prompt)
                sys.stdout.flush()
                
                raw_input = sys.stdin.readline()
                if not raw_input:
                    break
                    
                raw_input = raw_input.strip()
                if not raw_input:
                    continue
                
                # Parse command safely
                try:
                    cmd_parts = shlex.split(raw_input)
                except ValueError:
                    print(f"{ROJO_OSCURO}Error de sintaxis{RESET}")
                    continue
                    
                cmd = cmd_parts[0].lower()
                args = cmd_parts[1:]
                
                self.dispatch_command(cmd, args)
                    
            except KeyboardInterrupt:
                print("")
                print(f"{NARANJA}Interrupción detectada.{RESET}")
            except EOFError:
                self.running = False

    def dispatch_command(self, cmd, args):
        if cmd == 'exit':
            self.cmd_exit()
        elif cmd == 'help':
            self.cmd_help()
        elif cmd == 'status':
            self.cmd_status()
        elif cmd == 'scan':
            self.cmd_scan(args)
        elif cmd == 'connect':
            self.cmd_connect(args)
        elif cmd == 'clear' or cmd == 'cls':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif cmd == 'demo':
            anim.demo_seguridad()
        else:
            print(f"{ROJO_OSCURO}Comando desconocido: {cmd}{RESET}")

    def cmd_exit(self):
        anim.efecto_glitch("CERRANDO SESION...", ROJO_OSCURO)
        if self.comms.connected:
            self.comms.desconectar()
        time.sleep(0.5)
        self.running = False

    def cmd_help(self):
        print(f"\n{ROJO_OSCURO}--- COMANDOS DISPONIBLES ---{RESET}")
        cmds = [
            ("connect <host> [port]", "Conectar a servidor Telnet/TCP"),
            ("scan [codigo]", "Simular escaneo de codigo de barras"),
            ("status", "Ver estado del sistema y red"),
            ("demo", "Ejecutar demo visual de seguridad"),
            ("clear", "Limpiar pantalla"),
            ("exit", "Salir del sistema")
        ]
        for name, desc in cmds:
            print(f" {ROJO_NEON}{name:<25}{GRIS}{desc}{RESET}")
        print("")

    def cmd_status(self):
        print(f"\n{ROJO_OSCURO}--- ESTADO DEL SISTEMA ---{RESET}")
        print(f" {GRIS}USUARIO :{RESET} {self.user}")
        
        net_status = self.comms.estado()
        status_color = VERDE if net_status['connected'] else ROJO_OSCURO
        status_text = "CONECTADO" if net_status['connected'] else "DESCONECTADO"
        
        print(f" {GRIS}RED     :{RESET} {status_color}{status_text}{RESET}")
        if net_status['connected']:
            print(f" {GRIS}HOST    :{RESET} {net_status['host']}:{net_status['port']}")
            
        # Simulación de batería
        print(f" {GRIS}BATERIA :{RESET} {VERDE}98% [|||||]{RESET}")
        print("")

    def cmd_connect(self, args):
        if len(args) < 1:
            print(f"{ROJO_OSCURO}Uso: connect <host> [port]{RESET}")
            return
            
        host = args[0]
        port = int(args[1]) if len(args) > 1 else 23
        
        print(f"{GRIS}Iniciando enlace con {host}:{port}...{RESET}")
        anim.loading_bar("Negociando Protocolo", duration=1)
        
        result = self.comms.conectar(host, port)
        
        if result is True:
            print(f"{VERDE}>>> CONEXION ESTABLECIDA{RESET}")
        else:
            print(f"{ROJO_NEON}>>> ERROR DE CONEXION: {result}{RESET}")

    def cmd_scan(self, args):
        code = args[0] if args else f"SCAN-{int(time.time())}"
        anim.animacion_escaneo("MANUAL", code)

if __name__ == "__main__":
    shell = SacityShell()
    shell.run()
