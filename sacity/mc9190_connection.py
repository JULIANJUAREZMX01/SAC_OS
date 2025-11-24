"""
SACITY Device Connection Manager
Establece conexión con MC9190 via USB ActiveSync/RAPI
"""
import os
import sys
import subprocess
import winreg
import ctypes
from ctypes import wintypes

class MC9190Connection:
    def __init__(self):
        self.device_connected = False
        self.device_name = None
        
    def check_wmdc_installed(self):
        """Verifica si Windows Mobile Device Center está instalado"""
        paths = [
            r"C:\Program Files\Windows Mobile Device Center\wmdc.exe",
            r"C:\Program Files (x86)\Windows Mobile Device Center\wmdc.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                print(f"[OK] WMDC encontrado en: {path}")
                return path
        print("[ERROR] Windows Mobile Device Center no está instalado")
        return None
    
    def check_activesync_service(self):
        """Verifica servicios de ActiveSync"""
        try:
            result = subprocess.run(
                ['sc', 'query', 'RapiMgr'],
                capture_output=True,
                text=True
            )
            if "RUNNING" in result.stdout:
                print("[OK] Servicio RapiMgr está corriendo")
                return True
            else:
                print("[WARNING] Servicio RapiMgr no está activo")
                return False
        except Exception as e:
            print(f"[ERROR] No se pudo verificar servicios: {e}")
            return False
    
    def detect_device_usb(self):
        """Detecta dispositivo Symbol via USB"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Symbol*"} | Select-Object Status, FriendlyName, InstanceId'],
                capture_output=True,
                text=True
            )
            
            if "Symbol" in result.stdout:
                print("[OK] Dispositivo Symbol detectado:")
                print(result.stdout)
                
                # Verificar si hay errores
                if "Error" in result.stdout:
                    print("[WARNING] Dispositivo tiene errores - se requiere instalar drivers")
                    return "ERROR"
                else:
                    self.device_connected = True
                    return "OK"
            else:
                print("[ERROR] No se detectó dispositivo Symbol")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error al detectar dispositivo: {e}")
            return None
    
    def install_symbol_drivers(self):
        """Guía para instalar drivers de Symbol"""
        print("\n" + "="*60)
        print("INSTALACIÓN DE DRIVERS SYMBOL MC9190")
        print("="*60)
        print("\n1. Descarga los drivers desde:")
        print("   https://www.zebra.com/us/en/support-downloads/mobile-computers/handheld/mc9190-g.html")
        print("\n2. Busca: 'MC9190 USB Driver Package'")
        print("\n3. Ejecuta el instalador como Administrador")
        print("\n4. Reinicia el PC después de la instalación")
        print("\n5. Vuelve a conectar el dispositivo a la cradle")
        print("="*60)
    
    def check_rapi_connection(self):
        """Intenta conectar via RAPI (Remote API)"""
        try:
            # Cargar rapi.dll si existe
            rapi = ctypes.WinDLL('rapi.dll')
            
            # Intentar inicializar RAPI
            result = rapi.CeRapiInit()
            if result == 0:  # S_OK
                print("[OK] Conexión RAPI establecida")
                self.device_connected = True
                
                # Obtener información del dispositivo
                self.get_device_info(rapi)
                
                # Cerrar conexión
                rapi.CeRapiUninit()
                return True
            else:
                print(f"[ERROR] No se pudo inicializar RAPI. Código: {result}")
                return False
                
        except Exception as e:
            print(f"[ERROR] RAPI no disponible: {e}")
            print("[INFO] Asegúrate de que WMDC esté instalado y el dispositivo conectado")
            return False
    
    def get_device_info(self, rapi):
        """Obtiene información del dispositivo via RAPI"""
        try:
            # Buffer para nombre del dispositivo
            buffer = ctypes.create_unicode_buffer(256)
            
            # Intentar obtener nombre del dispositivo
            # Nota: Esta es una simplificación, RAPI tiene muchas más funciones
            print("[INFO] Dispositivo Windows CE conectado")
            
        except Exception as e:
            print(f"[WARNING] No se pudo obtener info del dispositivo: {e}")
    
    def transfer_file_to_device(self, local_path, remote_path):
        """Transfiere archivo al dispositivo via RAPI"""
        try:
            rapi = ctypes.WinDLL('rapi.dll')
            
            if rapi.CeRapiInit() == 0:
                print(f"[INFO] Transfiriendo {local_path} -> {remote_path}")
                
                # Aquí iría la lógica de transferencia usando CeCopyFile
                # Por ahora, solo mostramos el comando
                print("[INFO] Usa WMDC para transferir archivos manualmente")
                print(f"      Arrastra {local_path} a la ventana de WMDC")
                
                rapi.CeRapiUninit()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[ERROR] No se pudo transferir archivo: {e}")
            return False

def main():
    print("\n" + "="*60)
    print("SACITY - MC9190 Connection Manager")
    print("="*60 + "\n")
    
    conn = MC9190Connection()
    
    # 1. Verificar WMDC
    wmdc_path = conn.check_wmdc_installed()
    
    # 2. Verificar servicios
    conn.check_activesync_service()
    
    # 3. Detectar dispositivo
    device_status = conn.detect_device_usb()
    
    if device_status == "ERROR":
        print("\n[ACCIÓN REQUERIDA] Instalar drivers de Symbol")
        conn.install_symbol_drivers()
    elif device_status == "OK":
        print("\n[OK] Dispositivo detectado correctamente")
        
        # 4. Intentar conexión RAPI
        if conn.check_rapi_connection():
            print("\n[SUCCESS] Conexión establecida con MC9190")
            print("\nPuedes proceder a transferir archivos SACITY al dispositivo")
        else:
            print("\n[INFO] Conexión USB detectada pero RAPI no disponible")
            print("       Usa WMDC para transferir archivos manualmente")
    
    # Si WMDC no está instalado, dar instrucciones
    if not wmdc_path:
        print("\n" + "="*60)
        print("INSTALACIÓN DE WINDOWS MOBILE DEVICE CENTER")
        print("="*60)
        print("\n1. Descarga WMDC desde:")
        print("   https://www.microsoft.com/en-us/download/details.aspx?id=3182")
        print("\n2. Ejecuta el instalador")
        print("\n3. Reinicia el PC")
        print("\n4. Conecta el dispositivo MC9190 a la cradle USB")
        print("="*60)

if __name__ == "__main__":
    main()
