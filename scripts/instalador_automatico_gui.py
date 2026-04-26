#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
INSTALADOR AUTOMATIZADO GUI - SAC v3.0
Sistema de Automatización de Consultas - CEDIS Chedraui Cancún 427
═══════════════════════════════════════════════════════════════════════════════

Instalador completamente automatizado que:
1. Ejecuta TODO el proceso de instalación sin intervención manual
2. Instala dependencias automáticamente (sin enters, sin confirmaciones)
3. Crea estructura de directorios
4. Verifica el sistema
5. Compila el ejecutable
6. SOLO AL FINAL solicita credenciales
7. El sistema queda instalado, ejecutándose y esperando credenciales

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════════════════════
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import threading
import time
import shutil
from pathlib import Path
from datetime import datetime
import json
import queue

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL INSTALADOR
# ═══════════════════════════════════════════════════════════════════════════════

INSTALADOR_CONFIG = {
    'version': '3.0.0',
    'titulo': 'SAC - Instalador Automatizado',
    'subtitulo': 'Sistema de Automatización de Consultas',
    'organizacion': 'Tiendas Chedraui S.A. de C.V.',
    'cedis': 'CEDIS Cancún 427',
    'region': 'Región Sureste',
    'ancho_ventana': 900,
    'alto_ventana': 700,
    'color_chedraui': '#E31837',
    'color_fondo': '#F5F5F5',
    'color_exito': '#28A745',
    'color_error': '#DC3545',
    'color_advertencia': '#FFC107',
    'color_info': '#17A2B8',
}

# Directorios requeridos
DIRECTORIOS_REQUERIDOS = [
    'config',
    'docs',
    'modules',
    'modules/email',
    'modules/conflicts',
    'modules/repositories',
    'modules/rules',
    'modules/validators',
    'modules/excel_templates',
    'queries',
    'queries/obligatorias',
    'queries/preventivas',
    'queries/bajo_demanda',
    'queries/ddl',
    'queries/dml',
    'queries/templates',
    'tests',
    'output',
    'output/logs',
    'output/resultados',
    'output/backups',
    'output/snapshots',
    'assets',
]

# Archivos críticos a verificar
ARCHIVOS_CRITICOS = [
    'config.py',
    'main.py',
    'monitor.py',
    'gestor_correos.py',
    'requirements.txt',
    'README.md',
]

# Dependencias base (sin DB drivers que requieren instalación especial)
DEPENDENCIAS_BASE = [
    'pip',  # Actualizar pip primero
    'wheel',
    'setuptools',
]

# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL DEL INSTALADOR
# ═══════════════════════════════════════════════════════════════════════════════

class InstaladorAutomaticoGUI:
    """
    Instalador GUI completamente automatizado para SAC.
    Ejecuta todas las fases sin intervención del usuario hasta el final.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{INSTALADOR_CONFIG['titulo']} v{INSTALADOR_CONFIG['version']}")
        self.root.geometry(f"{INSTALADOR_CONFIG['ancho_ventana']}x{INSTALADOR_CONFIG['alto_ventana']}")
        self.root.resizable(True, True)
        self.root.configure(bg=INSTALADOR_CONFIG['color_fondo'])

        # Centrar ventana
        self._centrar_ventana()

        # Variables de estado
        self.instalacion_completada = False
        self.fase_actual = 0
        self.total_fases = 7
        self.errores = []
        self.advertencias = []
        self.log_queue = queue.Queue()
        self.proceso_activo = None
        self.cancelar_instalacion = False

        # Directorio base
        self.base_dir = Path(__file__).parent.parent.absolute()

        # Credenciales (se llenan al final)
        self.credenciales = {
            'db_user': tk.StringVar(value=''),
            'db_password': tk.StringVar(value=''),
            'email_user': tk.StringVar(value=''),
            'email_password': tk.StringVar(value=''),
            'telegram_token': tk.StringVar(value=''),
            'telegram_chat_ids': tk.StringVar(value=''),
        }

        # Fases de instalación
        self.fases = [
            {'nombre': 'Verificación de Requisitos', 'icono': '🔍', 'estado': 'pendiente'},
            {'nombre': 'Actualización de Herramientas', 'icono': '🔧', 'estado': 'pendiente'},
            {'nombre': 'Instalación de Dependencias', 'icono': '📦', 'estado': 'pendiente'},
            {'nombre': 'Creación de Estructura', 'icono': '📁', 'estado': 'pendiente'},
            {'nombre': 'Verificación del Sistema', 'icono': '✅', 'estado': 'pendiente'},
            {'nombre': 'Compilación de Ejecutable', 'icono': '⚙️', 'estado': 'pendiente'},
            {'nombre': 'Configuración de Credenciales', 'icono': '🔐', 'estado': 'pendiente'},
        ]

        # Construir interfaz
        self._construir_interfaz()

        # Iniciar verificación de logs
        self._procesar_cola_logs()

    def _centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        ancho = INSTALADOR_CONFIG['ancho_ventana']
        alto = INSTALADOR_CONFIG['alto_ventana']
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')

    def _construir_interfaz(self):
        """Construye la interfaz gráfica completa"""
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg=INSTALADOR_CONFIG['color_fondo'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header con logo Chedraui
        self._crear_header()

        # Panel de fases
        self._crear_panel_fases()

        # Barra de progreso general
        self._crear_barra_progreso()

        # Área de log
        self._crear_area_log()

        # Panel de estado actual
        self._crear_panel_estado()

        # Botones de acción
        self._crear_botones()

    def _crear_header(self):
        """Crea el header con branding Chedraui"""
        header_frame = tk.Frame(self.main_frame, bg=INSTALADOR_CONFIG['color_chedraui'], height=100)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)

        # Título principal
        titulo = tk.Label(
            header_frame,
            text=f"🏪 {INSTALADOR_CONFIG['titulo']}",
            font=('Segoe UI', 24, 'bold'),
            fg='white',
            bg=INSTALADOR_CONFIG['color_chedraui']
        )
        titulo.pack(pady=(15, 5))

        # Subtítulo
        subtitulo = tk.Label(
            header_frame,
            text=f"{INSTALADOR_CONFIG['subtitulo']} | {INSTALADOR_CONFIG['cedis']} | {INSTALADOR_CONFIG['region']}",
            font=('Segoe UI', 11),
            fg='white',
            bg=INSTALADOR_CONFIG['color_chedraui']
        )
        subtitulo.pack()

        # Versión
        version = tk.Label(
            header_frame,
            text=f"Versión {INSTALADOR_CONFIG['version']} - Instalación 100% Automatizada",
            font=('Segoe UI', 9, 'italic'),
            fg='#FFCCCC',
            bg=INSTALADOR_CONFIG['color_chedraui']
        )
        version.pack()

    def _crear_panel_fases(self):
        """Crea el panel con las fases de instalación"""
        fases_frame = tk.LabelFrame(
            self.main_frame,
            text=" 📋 Fases de Instalación ",
            font=('Segoe UI', 10, 'bold'),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg=INSTALADOR_CONFIG['color_chedraui']
        )
        fases_frame.pack(fill=tk.X, pady=(0, 10))

        # Frame interno para las fases
        self.fases_container = tk.Frame(fases_frame, bg=INSTALADOR_CONFIG['color_fondo'])
        self.fases_container.pack(fill=tk.X, padx=10, pady=10)

        self.labels_fases = []
        for i, fase in enumerate(self.fases):
            # Frame para cada fase
            fase_frame = tk.Frame(self.fases_container, bg=INSTALADOR_CONFIG['color_fondo'])
            fase_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

            # Indicador de estado
            estado_label = tk.Label(
                fase_frame,
                text=fase['icono'],
                font=('Segoe UI', 16),
                bg=INSTALADOR_CONFIG['color_fondo']
            )
            estado_label.pack()

            # Nombre de la fase
            nombre_label = tk.Label(
                fase_frame,
                text=fase['nombre'],
                font=('Segoe UI', 8),
                bg=INSTALADOR_CONFIG['color_fondo'],
                wraplength=100
            )
            nombre_label.pack()

            # Indicador visual
            indicador = tk.Label(
                fase_frame,
                text="○",
                font=('Segoe UI', 12),
                fg='gray',
                bg=INSTALADOR_CONFIG['color_fondo']
            )
            indicador.pack()

            self.labels_fases.append({
                'estado': estado_label,
                'nombre': nombre_label,
                'indicador': indicador,
                'frame': fase_frame
            })

    def _crear_barra_progreso(self):
        """Crea la barra de progreso general"""
        progreso_frame = tk.Frame(self.main_frame, bg=INSTALADOR_CONFIG['color_fondo'])
        progreso_frame.pack(fill=tk.X, pady=(0, 10))

        # Label de progreso
        self.progreso_label = tk.Label(
            progreso_frame,
            text="Listo para iniciar instalación automatizada",
            font=('Segoe UI', 10),
            bg=INSTALADOR_CONFIG['color_fondo']
        )
        self.progreso_label.pack(anchor=tk.W)

        # Barra de progreso
        style = ttk.Style()
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#E0E0E0',
            background=INSTALADOR_CONFIG['color_chedraui'],
            thickness=25
        )

        self.barra_progreso = ttk.Progressbar(
            progreso_frame,
            style="Custom.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL,
            length=400,
            mode='determinate',
            maximum=100
        )
        self.barra_progreso.pack(fill=tk.X, pady=5)

        # Porcentaje
        self.porcentaje_label = tk.Label(
            progreso_frame,
            text="0%",
            font=('Segoe UI', 10, 'bold'),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg=INSTALADOR_CONFIG['color_chedraui']
        )
        self.porcentaje_label.pack(anchor=tk.E)

    def _crear_area_log(self):
        """Crea el área de log con scroll"""
        log_frame = tk.LabelFrame(
            self.main_frame,
            text=" 📝 Registro de Instalación ",
            font=('Segoe UI', 10, 'bold'),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg=INSTALADOR_CONFIG['color_chedraui']
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=('Consolas', 9),
            bg='#1E1E1E',
            fg='#FFFFFF',
            insertbackground='white',
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configurar tags de colores
        self.log_text.tag_configure('info', foreground='#00BFFF')
        self.log_text.tag_configure('exito', foreground='#00FF00')
        self.log_text.tag_configure('error', foreground='#FF4444')
        self.log_text.tag_configure('advertencia', foreground='#FFD700')
        self.log_text.tag_configure('fase', foreground='#FF69B4', font=('Consolas', 10, 'bold'))
        self.log_text.tag_configure('comando', foreground='#87CEEB')
        self.log_text.tag_configure('header', foreground='#E31837', font=('Consolas', 10, 'bold'))

    def _crear_panel_estado(self):
        """Crea el panel de estado actual"""
        estado_frame = tk.Frame(self.main_frame, bg=INSTALADOR_CONFIG['color_fondo'])
        estado_frame.pack(fill=tk.X, pady=(0, 10))

        # Estado actual
        self.estado_actual = tk.Label(
            estado_frame,
            text="⏳ Esperando inicio de instalación...",
            font=('Segoe UI', 11),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg=INSTALADOR_CONFIG['color_info']
        )
        self.estado_actual.pack(anchor=tk.W)

        # Detalle de operación
        self.detalle_operacion = tk.Label(
            estado_frame,
            text="",
            font=('Segoe UI', 9),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg='gray'
        )
        self.detalle_operacion.pack(anchor=tk.W)

    def _crear_botones(self):
        """Crea los botones de acción"""
        botones_frame = tk.Frame(self.main_frame, bg=INSTALADOR_CONFIG['color_fondo'])
        botones_frame.pack(fill=tk.X)

        # Botón Cancelar
        self.btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Segoe UI', 10),
            bg='#DC3545',
            fg='white',
            width=15,
            command=self._cancelar,
            state=tk.DISABLED
        )
        self.btn_cancelar.pack(side=tk.RIGHT, padx=5)

        # Botón Iniciar
        self.btn_iniciar = tk.Button(
            botones_frame,
            text="🚀 INICIAR INSTALACIÓN AUTOMÁTICA",
            font=('Segoe UI', 12, 'bold'),
            bg=INSTALADOR_CONFIG['color_chedraui'],
            fg='white',
            width=35,
            command=self._iniciar_instalacion
        )
        self.btn_iniciar.pack(side=tk.RIGHT, padx=5)

        # Información adicional
        info_label = tk.Label(
            botones_frame,
            text="💡 La instalación es completamente automática. Solo se pedirán credenciales al final.",
            font=('Segoe UI', 8),
            bg=INSTALADOR_CONFIG['color_fondo'],
            fg='gray'
        )
        info_label.pack(side=tk.LEFT)

    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTODOS DE LOG Y PROGRESO
    # ═══════════════════════════════════════════════════════════════════════════

    def _log(self, mensaje: str, tipo: str = 'info'):
        """Añade mensaje al log con formato"""
        self.log_queue.put((mensaje, tipo))

    def _procesar_cola_logs(self):
        """Procesa los mensajes en la cola de logs"""
        try:
            while True:
                mensaje, tipo = self.log_queue.get_nowait()
                self._escribir_log(mensaje, tipo)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._procesar_cola_logs)

    def _escribir_log(self, mensaje: str, tipo: str = 'info'):
        """Escribe en el área de log"""
        self.log_text.configure(state=tk.NORMAL)

        timestamp = datetime.now().strftime('%H:%M:%S')
        prefijos = {
            'info': '📋',
            'exito': '✅',
            'error': '❌',
            'advertencia': '⚠️',
            'fase': '🔄',
            'comando': '💻',
            'header': '═══'
        }

        prefijo = prefijos.get(tipo, '•')
        linea = f"[{timestamp}] {prefijo} {mensaje}\n"

        self.log_text.insert(tk.END, linea, tipo)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _actualizar_progreso(self, porcentaje: int, mensaje: str = None):
        """Actualiza la barra de progreso"""
        self.barra_progreso['value'] = porcentaje
        self.porcentaje_label.config(text=f"{porcentaje}%")
        if mensaje:
            self.progreso_label.config(text=mensaje)
        self.root.update_idletasks()

    def _actualizar_fase(self, indice: int, estado: str):
        """Actualiza el estado visual de una fase"""
        colores = {
            'pendiente': ('gray', '○'),
            'en_progreso': (INSTALADOR_CONFIG['color_info'], '◐'),
            'completado': (INSTALADOR_CONFIG['color_exito'], '●'),
            'error': (INSTALADOR_CONFIG['color_error'], '✖'),
        }

        color, simbolo = colores.get(estado, ('gray', '○'))

        if indice < len(self.labels_fases):
            self.labels_fases[indice]['indicador'].config(text=simbolo, fg=color)
            self.root.update_idletasks()

    def _actualizar_estado(self, mensaje: str, detalle: str = ""):
        """Actualiza el estado actual mostrado"""
        self.estado_actual.config(text=mensaje)
        self.detalle_operacion.config(text=detalle)
        self.root.update_idletasks()

    # ═══════════════════════════════════════════════════════════════════════════
    # EJECUCIÓN DE COMANDOS
    # ═══════════════════════════════════════════════════════════════════════════

    def _ejecutar_comando(self, comando: list, descripcion: str = "",
                          capturar_salida: bool = True, timeout: int = 600) -> tuple:
        """
        Ejecuta un comando de forma automatizada sin intervención.
        Retorna (éxito: bool, salida: str)
        """
        self._log(f"Ejecutando: {' '.join(comando)}", 'comando')

        try:
            # Configurar para ejecución silenciosa
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
            env['PIP_NO_INPUT'] = '1'  # Desactivar inputs de pip

            # Ejecutar proceso
            proceso = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,  # Sin entrada estándar
                text=True,
                cwd=str(self.base_dir),
                env=env,
                bufsize=1
            )

            self.proceso_activo = proceso
            salida_completa = []

            # Leer salida línea por línea
            while True:
                if self.cancelar_instalacion:
                    proceso.terminate()
                    return False, "Instalación cancelada por el usuario"

                linea = proceso.stdout.readline()
                if not linea and proceso.poll() is not None:
                    break

                if linea:
                    linea_limpia = linea.strip()
                    if linea_limpia:
                        salida_completa.append(linea_limpia)
                        # Mostrar solo líneas relevantes
                        if any(kw in linea_limpia.lower() for kw in
                               ['installing', 'successfully', 'error', 'warning', 'collecting', 'building']):
                            self._log(f"  → {linea_limpia[:100]}", 'info')

            codigo_retorno = proceso.returncode
            self.proceso_activo = None

            if codigo_retorno == 0:
                self._log(f"✓ {descripcion or 'Comando'} completado exitosamente", 'exito')
                return True, '\n'.join(salida_completa)
            else:
                self._log(f"✗ Error en {descripcion or 'comando'} (código {codigo_retorno})", 'error')
                return False, '\n'.join(salida_completa)

        except subprocess.TimeoutExpired:
            self._log(f"⏱ Timeout en {descripcion}", 'error')
            return False, "Tiempo de espera agotado"
        except Exception as e:
            self._log(f"Error ejecutando comando: {str(e)}", 'error')
            return False, str(e)

    def _ejecutar_pip(self, paquetes: list, descripcion: str = "") -> bool:
        """Ejecuta pip install de forma automatizada"""
        comando = [
            sys.executable, '-m', 'pip', 'install',
            '--upgrade',
            '--no-input',  # Sin confirmaciones
            '--disable-pip-version-check',
            '--progress-bar', 'off',  # Sin barra de progreso interactiva
            '-q',  # Modo silencioso
        ] + paquetes

        exito, _ = self._ejecutar_comando(comando, descripcion)
        return exito

    # ═══════════════════════════════════════════════════════════════════════════
    # FASES DE INSTALACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def _iniciar_instalacion(self):
        """Inicia el proceso de instalación automatizada"""
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_cancelar.config(state=tk.NORMAL)
        self.cancelar_instalacion = False

        # Ejecutar en hilo separado
        threading.Thread(target=self._ejecutar_instalacion, daemon=True).start()

    def _ejecutar_instalacion(self):
        """Ejecuta todas las fases de instalación"""
        self._log("═" * 60, 'header')
        self._log("INICIANDO INSTALACIÓN AUTOMATIZADA DE SAC", 'header')
        self._log(f"Versión: {INSTALADOR_CONFIG['version']}", 'header')
        self._log(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'header')
        self._log("═" * 60, 'header')

        fases_funciones = [
            self._fase_verificar_requisitos,
            self._fase_actualizar_herramientas,
            self._fase_instalar_dependencias,
            self._fase_crear_estructura,
            self._fase_verificar_sistema,
            self._fase_compilar_ejecutable,
            self._fase_configurar_credenciales,
        ]

        for i, fase_func in enumerate(fases_funciones):
            if self.cancelar_instalacion:
                self._log("Instalación cancelada", 'advertencia')
                break

            self._actualizar_fase(i, 'en_progreso')
            self._log(f"", 'fase')
            self._log(f"FASE {i+1}/{len(fases_funciones)}: {self.fases[i]['nombre'].upper()}", 'fase')
            self._log(f"-" * 50, 'info')

            try:
                exito = fase_func()

                if exito:
                    self._actualizar_fase(i, 'completado')
                    progreso = int(((i + 1) / len(fases_funciones)) * 100)
                    self._actualizar_progreso(progreso, f"Fase {i+1} completada")
                else:
                    self._actualizar_fase(i, 'error')
                    if i < 5:  # Fases críticas (antes de credenciales)
                        self._log("Error crítico en fase de instalación", 'error')
                        break

            except Exception as e:
                self._log(f"Error en fase {i+1}: {str(e)}", 'error')
                self._actualizar_fase(i, 'error')
                self.errores.append(str(e))

        # Finalización
        self._finalizar_instalacion()

    def _fase_verificar_requisitos(self) -> bool:
        """Fase 1: Verificar requisitos del sistema"""
        self._actualizar_estado("🔍 Verificando requisitos del sistema...",
                               "Comprobando Python, pip y permisos")

        # Verificar versión de Python
        version_python = sys.version_info
        self._log(f"Python versión: {version_python.major}.{version_python.minor}.{version_python.micro}", 'info')

        if version_python.major < 3 or (version_python.major == 3 and version_python.minor < 8):
            self._log("Se requiere Python 3.8 o superior", 'error')
            return False

        self._log("✓ Versión de Python compatible", 'exito')

        # Verificar pip
        try:
            resultado = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True, text=True, timeout=30
            )
            if resultado.returncode == 0:
                self._log(f"✓ pip disponible: {resultado.stdout.strip()[:50]}", 'exito')
            else:
                self._log("pip no está disponible", 'error')
                return False
        except Exception as e:
            self._log(f"Error verificando pip: {e}", 'error')
            return False

        # Verificar permisos de escritura
        test_file = self.base_dir / '.instalador_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
            self._log("✓ Permisos de escritura verificados", 'exito')
        except Exception as e:
            self._log(f"Sin permisos de escritura: {e}", 'error')
            return False

        # Verificar espacio en disco (mínimo 500MB)
        try:
            uso_disco = shutil.disk_usage(self.base_dir)
            espacio_libre_mb = uso_disco.free / (1024 * 1024)
            self._log(f"Espacio libre: {espacio_libre_mb:.0f} MB", 'info')
            if espacio_libre_mb < 500:
                self._log("Se requieren al menos 500 MB libres", 'advertencia')
        except Exception:
            pass

        self._log("✓ Requisitos del sistema verificados", 'exito')
        return True

    def _fase_actualizar_herramientas(self) -> bool:
        """Fase 2: Actualizar pip, wheel y setuptools"""
        self._actualizar_estado("🔧 Actualizando herramientas de instalación...",
                               "Actualizando pip, wheel y setuptools")

        # Actualizar pip
        self._log("Actualizando pip...", 'info')
        exito = self._ejecutar_pip(['pip'], "Actualización de pip")
        if not exito:
            self._log("Advertencia: No se pudo actualizar pip, continuando...", 'advertencia')

        # Instalar wheel y setuptools
        self._log("Instalando wheel y setuptools...", 'info')
        exito = self._ejecutar_pip(['wheel', 'setuptools'], "Instalación de herramientas base")

        if exito:
            self._log("✓ Herramientas de instalación actualizadas", 'exito')
        else:
            self._log("Advertencia: Algunas herramientas no se actualizaron", 'advertencia')

        return True  # Continuar aunque falle

    def _fase_instalar_dependencias(self) -> bool:
        """Fase 3: Instalar todas las dependencias"""
        self._actualizar_estado("📦 Instalando dependencias...",
                               "Instalando paquetes de requirements.txt")

        requirements_file = self.base_dir / 'requirements.txt'

        if not requirements_file.exists():
            self._log("Archivo requirements.txt no encontrado", 'error')
            return False

        # Leer requirements
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lineas = f.readlines()

            # Filtrar comentarios y líneas vacías
            dependencias = []
            for linea in lineas:
                linea = linea.strip()
                if linea and not linea.startswith('#'):
                    # Remover comentarios inline
                    if '#' in linea:
                        linea = linea.split('#')[0].strip()
                    if linea:
                        dependencias.append(linea)

            self._log(f"Encontradas {len(dependencias)} dependencias para instalar", 'info')

        except Exception as e:
            self._log(f"Error leyendo requirements.txt: {e}", 'error')
            return False

        # Instalar dependencias en grupos para mejor feedback
        grupos = {
            'Core (pandas, numpy)': ['pandas', 'numpy'],
            'Excel y Reportes': ['openpyxl', 'XlsxWriter', 'Pillow', 'reportlab'],
            'Configuración': ['python-dotenv', 'pydantic', 'pydantic-settings', 'PyYAML'],
            'Interfaz': ['rich', 'colorama', 'tqdm'],
            'Programación': ['schedule', 'python-dateutil', 'pytz'],
            'Web y API': ['requests', 'Flask', 'Jinja2'],
            'Notificaciones': ['python-telegram-bot'],
            'Testing': ['pytest', 'pytest-cov', 'pytest-asyncio'],
            'Compilación': ['pyinstaller'],
        }

        total_grupos = len(grupos)
        for idx, (nombre_grupo, paquetes) in enumerate(grupos.items()):
            if self.cancelar_instalacion:
                return False

            self._log(f"Instalando grupo: {nombre_grupo}", 'info')
            self._actualizar_estado(
                f"📦 Instalando dependencias ({idx+1}/{total_grupos})...",
                f"Grupo: {nombre_grupo}"
            )

            # Instalar grupo
            exito = self._ejecutar_pip(paquetes, nombre_grupo)

            if not exito:
                self._log(f"Advertencia: Algunos paquetes de {nombre_grupo} no se instalaron", 'advertencia')

            # Actualizar progreso parcial
            progreso_fase = 30 + int((idx + 1) / total_grupos * 20)
            self._actualizar_progreso(progreso_fase, f"Instalando: {nombre_grupo}")

        # Instalar desde requirements.txt completo para asegurar versiones
        self._log("Verificando todas las dependencias con requirements.txt...", 'info')
        comando = [
            sys.executable, '-m', 'pip', 'install',
            '-r', str(requirements_file),
            '--no-input',
            '--disable-pip-version-check',
            '-q'
        ]
        self._ejecutar_comando(comando, "Instalación completa de requirements.txt")

        self._log("✓ Dependencias instaladas", 'exito')
        return True

    def _fase_crear_estructura(self) -> bool:
        """Fase 4: Crear estructura de directorios"""
        self._actualizar_estado("📁 Creando estructura de directorios...",
                               "Creando carpetas necesarias")

        creados = 0
        existentes = 0

        for directorio in DIRECTORIOS_REQUERIDOS:
            ruta = self.base_dir / directorio
            try:
                if not ruta.exists():
                    ruta.mkdir(parents=True, exist_ok=True)
                    self._log(f"  ✓ Creado: {directorio}", 'exito')
                    creados += 1
                else:
                    existentes += 1
            except Exception as e:
                self._log(f"  ✗ Error creando {directorio}: {e}", 'error')

        # Crear archivo __init__.py en directorios de módulos
        init_dirs = ['modules', 'queries', 'tests', 'config']
        for init_dir in init_dirs:
            init_file = self.base_dir / init_dir / '__init__.py'
            if not init_file.exists():
                try:
                    init_file.write_text('# -*- coding: utf-8 -*-\n')
                    self._log(f"  ✓ Creado: {init_dir}/__init__.py", 'exito')
                except Exception:
                    pass

        self._log(f"✓ Estructura creada: {creados} nuevos, {existentes} existentes", 'exito')
        return True

    def _fase_verificar_sistema(self) -> bool:
        """Fase 5: Verificar integridad del sistema"""
        self._actualizar_estado("✅ Verificando integridad del sistema...",
                               "Comprobando archivos y módulos")

        # Verificar archivos críticos
        archivos_faltantes = []
        for archivo in ARCHIVOS_CRITICOS:
            ruta = self.base_dir / archivo
            if ruta.exists():
                self._log(f"  ✓ Encontrado: {archivo}", 'exito')
            else:
                self._log(f"  ✗ Faltante: {archivo}", 'error')
                archivos_faltantes.append(archivo)

        if archivos_faltantes:
            self._log(f"Advertencia: {len(archivos_faltantes)} archivos críticos faltantes", 'advertencia')

        # Verificar importación de módulos
        modulos_verificar = ['config', 'monitor', 'gestor_correos']
        for modulo in modulos_verificar:
            try:
                # Agregar base_dir al path temporalmente
                if str(self.base_dir) not in sys.path:
                    sys.path.insert(0, str(self.base_dir))

                __import__(modulo)
                self._log(f"  ✓ Módulo importable: {modulo}", 'exito')
            except ImportError as e:
                self._log(f"  ⚠ Módulo no importable: {modulo} ({e})", 'advertencia')
            except Exception as e:
                self._log(f"  ⚠ Error verificando {modulo}: {e}", 'advertencia')

        self._log("✓ Verificación del sistema completada", 'exito')
        return True

    def _fase_compilar_ejecutable(self) -> bool:
        """Fase 6: Compilar ejecutable con PyInstaller"""
        self._actualizar_estado("⚙️ Compilando ejecutable...",
                               "Creando ejecutable con PyInstaller")

        # Verificar PyInstaller
        try:
            import PyInstaller
            self._log(f"PyInstaller versión: {PyInstaller.__version__}", 'info')
        except ImportError:
            self._log("PyInstaller no disponible, instalando...", 'advertencia')
            if not self._ejecutar_pip(['pyinstaller'], "PyInstaller"):
                self._log("No se pudo instalar PyInstaller", 'error')
                return False

        # Buscar archivo spec o main.py
        spec_file = self.base_dir / 'SAC_CEDIS.spec'
        main_file = self.base_dir / 'main.py'

        if spec_file.exists():
            self._log(f"Usando archivo spec: {spec_file.name}", 'info')
            target = str(spec_file)
        elif main_file.exists():
            self._log("Usando main.py para compilación", 'info')
            target = str(main_file)
        else:
            self._log("No se encontró archivo para compilar", 'error')
            return False

        # Limpiar builds anteriores
        for carpeta in ['build', 'dist']:
            ruta = self.base_dir / carpeta
            if ruta.exists():
                try:
                    shutil.rmtree(ruta)
                    self._log(f"  ✓ Limpiado: {carpeta}/", 'info')
                except Exception as e:
                    self._log(f"  ⚠ No se pudo limpiar {carpeta}: {e}", 'advertencia')

        # Compilar
        self._log("Iniciando compilación (esto puede tomar varios minutos)...", 'info')

        comando = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '--log-level=WARN',
            target
        ]

        exito, salida = self._ejecutar_comando(comando, "Compilación de ejecutable", timeout=900)

        if exito:
            # Verificar que se creó el ejecutable
            dist_dir = self.base_dir / 'dist'
            if dist_dir.exists() and any(dist_dir.iterdir()):
                self._log("✓ Ejecutable compilado exitosamente", 'exito')

                # Listar contenido de dist
                for item in dist_dir.iterdir():
                    self._log(f"  → Generado: dist/{item.name}", 'info')

                return True
            else:
                self._log("La compilación terminó pero no se encontró el ejecutable", 'advertencia')
                return False
        else:
            self._log("Error durante la compilación", 'error')
            self._log("El sistema funcionará pero sin ejecutable compilado", 'advertencia')
            return False

    def _fase_configurar_credenciales(self) -> bool:
        """Fase 7: Configurar credenciales (formulario al final)"""
        self._actualizar_estado("🔐 Configuración de Credenciales...",
                               "Esperando ingreso de credenciales")

        self._log("", 'info')
        self._log("═" * 50, 'header')
        self._log("CONFIGURACIÓN DE CREDENCIALES", 'header')
        self._log("El sistema está instalado y listo.", 'info')
        self._log("Complete las credenciales para finalizar.", 'info')
        self._log("═" * 50, 'header')

        # Mostrar formulario de credenciales en el hilo principal
        self.root.after(0, self._mostrar_formulario_credenciales)

        # Esperar a que se complete el formulario
        self.esperando_credenciales = True
        while self.esperando_credenciales and not self.cancelar_instalacion:
            time.sleep(0.5)

        if self.cancelar_instalacion:
            return False

        return self.credenciales_guardadas

    def _mostrar_formulario_credenciales(self):
        """Muestra el formulario de credenciales en una ventana separada"""
        # Crear ventana de credenciales
        self.ventana_creds = tk.Toplevel(self.root)
        self.ventana_creds.title("🔐 Configuración de Credenciales - SAC")
        self.ventana_creds.geometry("500x550")
        self.ventana_creds.resizable(False, False)
        self.ventana_creds.transient(self.root)
        self.ventana_creds.grab_set()

        # Centrar
        self.ventana_creds.update_idletasks()
        x = (self.ventana_creds.winfo_screenwidth() // 2) - 250
        y = (self.ventana_creds.winfo_screenheight() // 2) - 275
        self.ventana_creds.geometry(f"500x550+{x}+{y}")

        # Frame principal
        main_frame = tk.Frame(self.ventana_creds, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo = tk.Label(
            main_frame,
            text="🔐 Configuración de Credenciales",
            font=('Segoe UI', 14, 'bold'),
            fg=INSTALADOR_CONFIG['color_chedraui']
        )
        titulo.pack(pady=(0, 5))

        # Subtítulo
        subtitulo = tk.Label(
            main_frame,
            text="El sistema está instalado. Configure las credenciales para finalizar.",
            font=('Segoe UI', 9),
            fg='gray'
        )
        subtitulo.pack(pady=(0, 20))

        # === SECCIÓN BASE DE DATOS ===
        db_frame = tk.LabelFrame(main_frame, text=" 💾 Base de Datos DB2 ", font=('Segoe UI', 10, 'bold'))
        db_frame.pack(fill=tk.X, pady=(0, 15))

        # Usuario DB
        tk.Label(db_frame, text="Usuario:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(db_frame, textvariable=self.credenciales['db_user'], width=35).grid(row=0, column=1, padx=5, pady=5)

        # Password DB
        tk.Label(db_frame, text="Contraseña:", font=('Segoe UI', 9)).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(db_frame, textvariable=self.credenciales['db_password'], show='*', width=35).grid(row=1, column=1, padx=5, pady=5)

        # === SECCIÓN EMAIL ===
        email_frame = tk.LabelFrame(main_frame, text=" 📧 Correo Electrónico (Office 365) ", font=('Segoe UI', 10, 'bold'))
        email_frame.pack(fill=tk.X, pady=(0, 15))

        # Email
        tk.Label(email_frame, text="Correo:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(email_frame, textvariable=self.credenciales['email_user'], width=35).grid(row=0, column=1, padx=5, pady=5)

        # Password Email
        tk.Label(email_frame, text="Contraseña:", font=('Segoe UI', 9)).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(email_frame, textvariable=self.credenciales['email_password'], show='*', width=35).grid(row=1, column=1, padx=5, pady=5)

        # === SECCIÓN TELEGRAM (Opcional) ===
        telegram_frame = tk.LabelFrame(main_frame, text=" 📱 Telegram (Opcional) ", font=('Segoe UI', 10, 'bold'))
        telegram_frame.pack(fill=tk.X, pady=(0, 15))

        # Token
        tk.Label(telegram_frame, text="Bot Token:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(telegram_frame, textvariable=self.credenciales['telegram_token'], width=35).grid(row=0, column=1, padx=5, pady=5)

        # Chat IDs
        tk.Label(telegram_frame, text="Chat IDs:", font=('Segoe UI', 9)).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(telegram_frame, textvariable=self.credenciales['telegram_chat_ids'], width=35).grid(row=1, column=1, padx=5, pady=5)

        # Nota
        nota = tk.Label(
            main_frame,
            text="💡 Puede dejar Telegram vacío y configurarlo después.\n"
                 "Las credenciales se guardarán de forma segura en el archivo .env",
            font=('Segoe UI', 8),
            fg='gray',
            justify=tk.CENTER
        )
        nota.pack(pady=10)

        # Botones
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        btn_omitir = tk.Button(
            btn_frame,
            text="⏭ Omitir (Configurar después)",
            font=('Segoe UI', 9),
            command=self._omitir_credenciales,
            width=25
        )
        btn_omitir.pack(side=tk.LEFT)

        btn_guardar = tk.Button(
            btn_frame,
            text="💾 Guardar y Finalizar",
            font=('Segoe UI', 10, 'bold'),
            bg=INSTALADOR_CONFIG['color_chedraui'],
            fg='white',
            command=self._guardar_credenciales,
            width=25
        )
        btn_guardar.pack(side=tk.RIGHT)

        # Manejar cierre de ventana
        self.ventana_creds.protocol("WM_DELETE_WINDOW", self._omitir_credenciales)

    def _guardar_credenciales(self):
        """Guarda las credenciales en el archivo .env"""
        try:
            # Leer template de env
            env_template = self.base_dir / 'env'
            env_file = self.base_dir / '.env'

            if env_template.exists():
                contenido = env_template.read_text(encoding='utf-8')
            else:
                # Crear contenido básico
                contenido = self._generar_env_basico()

            # Reemplazar credenciales
            reemplazos = {
                'DB_USER=': f"DB_USER={self.credenciales['db_user'].get()}",
                'DB_PASSWORD=': f"DB_PASSWORD={self.credenciales['db_password'].get()}",
                'EMAIL_USER=': f"EMAIL_USER={self.credenciales['email_user'].get()}",
                'EMAIL_PASSWORD=': f"EMAIL_PASSWORD={self.credenciales['email_password'].get()}",
                'EMAIL_FROM=': f"EMAIL_FROM={self.credenciales['email_user'].get()}",
            }

            # Telegram (si se proporcionó)
            if self.credenciales['telegram_token'].get():
                reemplazos['TELEGRAM_BOT_TOKEN='] = f"TELEGRAM_BOT_TOKEN={self.credenciales['telegram_token'].get()}"
            if self.credenciales['telegram_chat_ids'].get():
                reemplazos['TELEGRAM_CHAT_IDS='] = f"TELEGRAM_CHAT_IDS={self.credenciales['telegram_chat_ids'].get()}"

            # Aplicar reemplazos
            lineas = contenido.split('\n')
            nuevas_lineas = []
            for linea in lineas:
                linea_modificada = linea
                for patron, reemplazo in reemplazos.items():
                    if linea.startswith(patron):
                        linea_modificada = reemplazo
                        break
                nuevas_lineas.append(linea_modificada)

            # Guardar .env
            env_file.write_text('\n'.join(nuevas_lineas), encoding='utf-8')

            self._log("✓ Credenciales guardadas en .env", 'exito')
            self.credenciales_guardadas = True

        except Exception as e:
            self._log(f"Error guardando credenciales: {e}", 'error')
            self.credenciales_guardadas = False

        self.ventana_creds.destroy()
        self.esperando_credenciales = False

    def _omitir_credenciales(self):
        """Omite la configuración de credenciales"""
        self._log("⚠ Credenciales omitidas - Configurar manualmente en .env", 'advertencia')
        self.credenciales_guardadas = True  # Continuar de todas formas
        self.ventana_creds.destroy()
        self.esperando_credenciales = False

    def _generar_env_basico(self) -> str:
        """Genera un archivo .env básico si no existe template"""
        return """# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN SAC - CEDIS Cancún 427
# Generado automáticamente por el instalador
# ═══════════════════════════════════════════════════════════════

# === CREDENCIALES OBLIGATORIAS ===
DB_USER=
DB_PASSWORD=
EMAIL_USER=
EMAIL_PASSWORD=

# === BASE DE DATOS DB2 ===
DB_HOST=WM260BASD
DB_PORT=50000
DB_DATABASE=WM260BASD
DB_SCHEMA=WMWHSE1
DB_DRIVER={IBM DB2 ODBC DRIVER}
DB_TIMEOUT=30

# === CEDIS ===
CEDIS_CODE=427
CEDIS_NAME=CEDIS Cancún
CEDIS_REGION=Sureste
CEDIS_ALMACEN=C22

# === EMAIL (Office 365) ===
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_PROTOCOL=TLS
EMAIL_FROM=
EMAIL_FROM_NAME=Sistema SAC - CEDIS Cancún 427

# === TELEGRAM (Opcional) ===
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_IDS=
TELEGRAM_ENABLED=false

# === SISTEMA ===
SYSTEM_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
TIMEZONE=America/Cancun
LOG_LEVEL=INFO
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # FINALIZACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    def _finalizar_instalacion(self):
        """Finaliza el proceso de instalación"""
        self._log("", 'info')
        self._log("═" * 60, 'header')

        if not self.errores and not self.cancelar_instalacion:
            self._log("✅ INSTALACIÓN COMPLETADA EXITOSAMENTE", 'header')
            self._actualizar_progreso(100, "¡Instalación completada!")
            self._actualizar_estado(
                "✅ Sistema instalado y listo",
                "SAC está configurado y esperando para ejecutarse"
            )

            # Mensaje de éxito
            self._log("═" * 60, 'header')
            self._log("", 'info')
            self._log("El sistema SAC está instalado y configurado.", 'exito')
            self._log("", 'info')
            self._log("Para ejecutar SAC:", 'info')
            self._log("  → python main.py", 'comando')
            self._log("  → python main.py --menu", 'comando')
            self._log("", 'info')
            self._log("Para el dashboard web:", 'info')
            self._log("  → python dashboard.py", 'comando')
            self._log("", 'info')

            # Verificar ejecutable
            dist_dir = self.base_dir / 'dist'
            if dist_dir.exists():
                for item in dist_dir.iterdir():
                    self._log(f"Ejecutable disponible en: dist/{item.name}", 'exito')

            self.instalacion_completada = True

            # Mostrar mensaje de éxito
            self.root.after(0, lambda: messagebox.showinfo(
                "Instalación Exitosa",
                "✅ SAC se ha instalado correctamente.\n\n"
                "El sistema está listo para ejecutarse.\n\n"
                "Ejecute: python main.py"
            ))

        else:
            self._log("⚠️ INSTALACIÓN COMPLETADA CON ADVERTENCIAS", 'header')
            self._actualizar_estado(
                "⚠️ Instalación completada con advertencias",
                "Revise el log para más detalles"
            )

            if self.errores:
                self._log("Errores encontrados:", 'error')
                for error in self.errores:
                    self._log(f"  • {error}", 'error')

        self._log("═" * 60, 'header')

        # Restaurar botones
        self.root.after(0, self._restaurar_botones)

    def _restaurar_botones(self):
        """Restaura el estado de los botones"""
        self.btn_cancelar.config(state=tk.DISABLED)

        if self.instalacion_completada:
            self.btn_iniciar.config(
                text="🚀 Ejecutar SAC",
                state=tk.NORMAL,
                command=self._ejecutar_sac
            )
        else:
            self.btn_iniciar.config(
                text="🔄 Reintentar Instalación",
                state=tk.NORMAL,
                command=self._iniciar_instalacion
            )

    def _ejecutar_sac(self):
        """Ejecuta SAC después de la instalación"""
        try:
            # Ejecutar main.py en proceso separado
            subprocess.Popen(
                [sys.executable, str(self.base_dir / 'main.py'), '--menu'],
                cwd=str(self.base_dir)
            )
            self._log("SAC iniciado correctamente", 'exito')

            # Cerrar instalador después de un momento
            self.root.after(2000, self.root.destroy)

        except Exception as e:
            self._log(f"Error ejecutando SAC: {e}", 'error')
            messagebox.showerror("Error", f"No se pudo iniciar SAC:\n{e}")

    def _cancelar(self):
        """Cancela la instalación"""
        if messagebox.askyesno("Confirmar", "¿Está seguro de cancelar la instalación?"):
            self.cancelar_instalacion = True
            if self.proceso_activo:
                self.proceso_activo.terminate()
            self._log("Instalación cancelada por el usuario", 'advertencia')

    def ejecutar(self):
        """Ejecuta el instalador"""
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    print("═" * 60)
    print("  SAC - Instalador Automatizado v3.0")
    print("  Sistema de Automatización de Consultas")
    print("  CEDIS Chedraui Cancún 427")
    print("═" * 60)
    print()
    print("Iniciando interfaz gráfica de instalación...")
    print()

    try:
        instalador = InstaladorAutomaticoGUI()
        instalador.ejecutar()
    except tk.TclError as e:
        print(f"Error: No se puede iniciar la interfaz gráfica.")
        print(f"Detalle: {e}")
        print()
        print("Asegúrese de tener un entorno gráfico disponible.")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
