#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SCRIPT DE VERIFICACIÓN DEL SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Este script verifica la integridad completa del proyecto:
- Estructura de carpetas
- Existencia de archivos
- Imports correctos
- Configuración válida
- Documentación completa

Ejecutar después de cualquier reorganización o actualización.

Uso:
    python verificar_sistema.py

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
═══════════════════════════════════════════════════════════════
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict
import importlib.util

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    """Imprime encabezado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{texto.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")

def print_success(texto):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✓ {texto}{Colors.ENDC}")

def print_warning(texto):
    """Imprime advertencia"""
    print(f"{Colors.YELLOW}⚠ {texto}{Colors.ENDC}")

def print_error(texto):
    """Imprime error"""
    print(f"{Colors.RED}✗ {texto}{Colors.ENDC}")

def print_info(texto):
    """Imprime información"""
    print(f"{Colors.BLUE}ℹ {texto}{Colors.ENDC}")


class VerificadorSistema:
    """Verificador de integridad del sistema SAC"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.errores = []
        self.advertencias = []
        self.exitos = []
        
    def verificar_estructura_carpetas(self) -> bool:
        """Verifica que todas las carpetas necesarias existan"""
        print_header("VERIFICACIÓN DE ESTRUCTURA DE CARPETAS")
        
        carpetas_requeridas = {
            'config': 'Configuración del sistema',
            'docs': 'Documentación completa',
            'modules': 'Módulos Python',
            'queries': 'Consultas SQL',
            'tests': 'Tests unitarios',
            'output': 'Directorio de salida',
            'output/logs': 'Logs del sistema',
            'output/resultados': 'Resultados y reportes',
        }
        
        todas_ok = True
        
        for carpeta, descripcion in carpetas_requeridas.items():
            ruta = self.base_dir / carpeta
            if ruta.exists() and ruta.is_dir():
                print_success(f"{carpeta.ljust(25)} → {descripcion}")
                self.exitos.append(f"Carpeta {carpeta} existe")
            else:
                print_error(f"{carpeta.ljust(25)} → NO EXISTE")
                self.errores.append(f"Falta carpeta: {carpeta}")
                todas_ok = False
        
        return todas_ok
    
    def verificar_archivos_principales(self) -> bool:
        """Verifica archivos principales del proyecto"""
        print_header("VERIFICACIÓN DE ARCHIVOS PRINCIPALES")
        
        archivos_requeridos = {
            'config.py': 'Configuración centralizada',
            'main.py': 'Script principal',
            'monitor.py': 'Sistema de monitoreo',
            'gestor_correos.py': 'Gestor de correos',
            'examples.py': 'Ejemplos de uso',
            'requirements.txt': 'Dependencias Python',
            '.gitignore': 'Exclusiones de Git',
            'README.md': 'Documentación principal',
        }
        
        todas_ok = True
        
        for archivo, descripcion in archivos_requeridos.items():
            ruta = self.base_dir / archivo
            if ruta.exists() and ruta.is_file():
                tamaño = ruta.stat().st_size
                tamaño_kb = tamaño / 1024
                print_success(f"{archivo.ljust(25)} → {descripcion} ({tamaño_kb:.2f} KB)")
                self.exitos.append(f"Archivo {archivo} existe ({tamaño_kb:.2f} KB)")
            else:
                print_error(f"{archivo.ljust(25)} → NO EXISTE")
                self.errores.append(f"Falta archivo: {archivo}")
                todas_ok = False
        
        return todas_ok
    
    def verificar_modulos(self) -> bool:
        """Verifica módulos en carpeta modules/"""
        print_header("VERIFICACIÓN DE MÓDULOS")
        
        modulos_requeridos = {
            '__init__.py': 'Inicializador del paquete',
            'modulo_cartones.py': 'Gestión de cartones',
            'modulo_lpn.py': 'Procesamiento de LPN',
            'modulo_ubicaciones.py': 'Gestión de ubicaciones',
            'modulo_usuarios.py': 'Administración de usuarios',
            'reportes_excel.py': 'Generación de reportes',
        }
        
        todas_ok = True
        modules_dir = self.base_dir / 'modules'
        
        for modulo, descripcion in modulos_requeridos.items():
            ruta = modules_dir / modulo
            if ruta.exists() and ruta.is_file():
                tamaño = ruta.stat().st_size
                tamaño_kb = tamaño / 1024
                print_success(f"{modulo.ljust(30)} → {descripcion} ({tamaño_kb:.2f} KB)")
                self.exitos.append(f"Módulo {modulo} existe")
            else:
                print_error(f"{modulo.ljust(30)} → NO EXISTE")
                self.errores.append(f"Falta módulo: {modulo}")
                todas_ok = False
        
        return todas_ok
    
    def verificar_documentacion(self) -> bool:
        """Verifica documentación completa"""
        print_header("VERIFICACIÓN DE DOCUMENTACIÓN")

        # Documentación esencial (debe existir)
        docs_esenciales = {
            'INSTALACION_WINDOWS.md': 'Guía de instalación Windows',
        }

        # Documentación opcional (informativo si existe)
        docs_opcionales = {
            'README.md': 'Documentación principal',
            'QUICK_START.md': 'Inicio rápido',
            'INDICE_DOCUMENTACION.md': 'Índice de documentación',
            'NUEVAS_FUNCIONALIDADES.md': 'Roadmap y nuevas features',
            'RESUMEN_EJECUTIVO.md': 'Resumen ejecutivo',
            'FUNCIONALIDADES_COMPLETAS.md': 'Funcionalidades completas',
            'LICENCIA.md': 'Licencia del proyecto',
            'RESUMEN_PROYECTO.md': 'Resumen del proyecto',
        }

        todas_ok = True
        docs_dir = self.base_dir / 'docs'

        # Verificar documentación esencial
        for doc, descripcion in docs_esenciales.items():
            ruta = docs_dir / doc
            if ruta.exists() and ruta.is_file():
                tamaño = ruta.stat().st_size
                tamaño_kb = tamaño / 1024
                print_success(f"{doc.ljust(35)} → {descripcion} ({tamaño_kb:.2f} KB)")
                self.exitos.append(f"Documentación {doc} existe")
            else:
                print_warning(f"{doc.ljust(35)} → NO EXISTE (recomendado)")
                self.advertencias.append(f"Documentación recomendada: {doc}")

        # Verificar documentación opcional (solo info)
        docs_encontrados = 0
        for doc, descripcion in docs_opcionales.items():
            ruta = docs_dir / doc
            if ruta.exists() and ruta.is_file():
                tamaño = ruta.stat().st_size
                tamaño_kb = tamaño / 1024
                print_success(f"{doc.ljust(35)} → {descripcion} ({tamaño_kb:.2f} KB)")
                self.exitos.append(f"Documentación {doc} existe")
                docs_encontrados += 1

        print_info(f"Documentación adicional encontrada: {docs_encontrados} archivo(s)")

        return todas_ok
    
    def verificar_configuracion(self) -> bool:
        """Verifica archivos de configuración"""
        print_header("VERIFICACIÓN DE CONFIGURACIÓN")
        
        config_requeridos = {
            '.env.example': 'Plantilla de variables de entorno',
            '__init__.py': 'Inicializador del paquete con configuración',
        }
        
        todas_ok = True
        config_dir = self.base_dir / 'config'
        
        for archivo, descripcion in config_requeridos.items():
            ruta = config_dir / archivo
            if ruta.exists() and ruta.is_file():
                print_success(f"{archivo.ljust(25)} → {descripcion}")
                self.exitos.append(f"Config {archivo} existe")
            else:
                print_error(f"{archivo.ljust(25)} → NO EXISTE")
                self.errores.append(f"Falta config: {archivo}")
                todas_ok = False
        
        # Verificar si existe .env (advertencia si no existe)
        env_file = self.base_dir / '.env'
        if env_file.exists():
            print_success(f"{'.env'.ljust(25)} → Credenciales configuradas")
        else:
            print_warning(f"{'.env'.ljust(25)} → No configurado (usar .env.example como plantilla)")
            self.advertencias.append("Archivo .env no configurado - copiar de config/.env.example")
        
        return todas_ok
    
    def verificar_imports(self) -> bool:
        """Verifica que todos los imports funcionen"""
        print_header("VERIFICACIÓN DE IMPORTS")
        
        # Agregar directorio actual al path
        sys.path.insert(0, str(self.base_dir))
        
        imports_a_verificar = [
            ('config', 'Configuración central'),
            ('monitor', 'Sistema de monitoreo'),
            ('gestor_correos', 'Gestor de correos'),
            ('modules.reportes_excel', 'Generador de reportes'),
        ]
        
        todas_ok = True
        
        for modulo, descripcion in imports_a_verificar:
            try:
                # Intentar importar el módulo
                spec = importlib.util.find_spec(modulo)
                if spec is not None:
                    print_success(f"{modulo.ljust(30)} → {descripcion}")
                    self.exitos.append(f"Import {modulo} exitoso")
                else:
                    print_error(f"{modulo.ljust(30)} → NO SE PUEDE IMPORTAR")
                    self.errores.append(f"No se puede importar: {modulo}")
                    todas_ok = False
            except Exception as e:
                print_error(f"{modulo.ljust(30)} → ERROR: {str(e)}")
                self.errores.append(f"Error al importar {modulo}: {str(e)}")
                todas_ok = False
        
        return todas_ok
    
    def verificar_config_py(self) -> bool:
        """Verifica el contenido de config.py"""
        print_header("VERIFICACIÓN DE config.py")
        
        try:
            from config import (
                DB_CONFIG, CEDIS, EMAIL_CONFIG, PATHS,
                LOGGING_CONFIG, SYSTEM_CONFIG, COLORS
            )
            
            print_success("Todas las configuraciones se importan correctamente")
            
            # Verificar configuraciones críticas
            if DB_CONFIG.get('user') == 'tu_usuario':
                print_warning("DB_USER no configurado (valor por defecto)")
                self.advertencias.append("Configurar DB_USER en .env")
            else:
                print_success(f"DB_USER configurado: {DB_CONFIG.get('user')}")
            
            if EMAIL_CONFIG.get('user') == 'tu_email@chedraui.com.mx':
                print_warning("EMAIL_USER no configurado (valor por defecto)")
                self.advertencias.append("Configurar EMAIL_USER en .env")
            else:
                print_success(f"EMAIL_USER configurado: {EMAIL_CONFIG.get('user')}")
            
            print_info(f"CEDIS configurado: {CEDIS.get('name')} ({CEDIS.get('code')})")
            
            return True
            
        except Exception as e:
            print_error(f"Error al verificar config.py: {str(e)}")
            self.errores.append(f"Error en config.py: {str(e)}")
            return False
    
    def generar_reporte(self):
        """Genera reporte final de verificación"""
        print_header("REPORTE FINAL DE VERIFICACIÓN")
        
        total_verificaciones = len(self.exitos) + len(self.errores) + len(self.advertencias)
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Total de verificaciones: {total_verificaciones}")
        print_success(f"   Exitosas: {len(self.exitos)}")
        print_warning(f"   Advertencias: {len(self.advertencias)}")
        print_error(f"   Errores: {len(self.errores)}")
        
        if self.errores:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRORES ENCONTRADOS:{Colors.ENDC}")
            for i, error in enumerate(self.errores, 1):
                print(f"   {i}. {error}")
        
        if self.advertencias:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  ADVERTENCIAS:{Colors.ENDC}")
            for i, advertencia in enumerate(self.advertencias, 1):
                print(f"   {i}. {advertencia}")
        
        # Estado final
        print(f"\n{'='*70}")
        if len(self.errores) == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ SISTEMA VERIFICADO CORRECTAMENTE{Colors.ENDC}".center(80))
            print(f"{Colors.GREEN}Todos los componentes están en orden{Colors.ENDC}".center(80))
            if self.advertencias:
                print(f"\n{Colors.YELLOW}Hay {len(self.advertencias)} advertencia(s) que deberías revisar{Colors.ENDC}".center(80))
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SE ENCONTRARON {len(self.errores)} ERROR(ES){Colors.ENDC}".center(80))
            print(f"{Colors.RED}Por favor, corrige los errores antes de usar el sistema{Colors.ENDC}".center(80))
        print(f"{'='*70}\n")
    
    def ejecutar_verificacion_completa(self):
        """Ejecuta todas las verificaciones"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║       VERIFICADOR DE INTEGRIDAD - SISTEMA SAC v1.0               ║")
        print("║               CEDIS Cancún 427 - Tiendas Chedraui                ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        print_info(f"Directorio base: {self.base_dir}")
        print_info(f"Python: {sys.version.split()[0]}")
        
        # Ejecutar todas las verificaciones
        resultados = {
            'Estructura de carpetas': self.verificar_estructura_carpetas(),
            'Archivos principales': self.verificar_archivos_principales(),
            'Módulos': self.verificar_modulos(),
            'Documentación': self.verificar_documentacion(),
            'Configuración': self.verificar_configuracion(),
            'Imports': self.verificar_imports(),
            'config.py': self.verificar_config_py(),
        }
        
        # Generar reporte final
        self.generar_reporte()
        
        # Retornar código de salida
        return 0 if len(self.errores) == 0 else 1


def main():
    """Función principal"""
    try:
        verificador = VerificadorSistema()
        codigo_salida = verificador.ejecutar_verificacion_completa()
        sys.exit(codigo_salida)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Verificación interrumpida por el usuario{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error fatal durante la verificación: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
