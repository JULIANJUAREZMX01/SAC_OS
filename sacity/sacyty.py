#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
   ███████╗ █████╗  ██████╗██╗   ██╗████████╗██╗   ██╗
   ██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝╚══██╔══╝╚██╗ ██╔╝
   ███████╗███████║██║      ╚████╔╝    ██║    ╚████╔╝
   ╚════██║██╔══██║██║       ╚██╔╝     ██║     ╚██╔╝
   ███████║██║  ██║╚██████╗   ██║      ██║      ██║
   ╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝      ╚═╝      ╚═╝
================================================================================
    SACYTY - Sistema de Acceso a Consultas Y Terminales
    Lightweight DB2 Query Tool - Manhattan WMS
    CEDIS Chedraui Cancun 427
================================================================================

    Herramienta ligera estilo Velocity para consultas directas a DB2.
    Interfaz ASCII minimalista con soporte completo para queries SQL.

    Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
    Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
================================================================================
"""

import os
import sys
import time
import getpass
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import signal

# Intentar importar pandas para resultados tabulares
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ================================================================================
# COLORES ASCII - SOLO ROJO Y VERDE
# ================================================================================

class C:
    """Colores ASCII - Solo Rojo y Verde sobre fondo negro"""
    # Reset
    RESET = '\033[0m'

    # Colores principales
    RED = '\033[91m'
    GREEN = '\033[92m'

    # Variantes
    RED_BOLD = '\033[1;91m'
    GREEN_BOLD = '\033[1;92m'

    # Dim para texto secundario
    DIM = '\033[2m'

    # Bold
    BOLD = '\033[1m'

    # Limpiar pantalla
    CLEAR = '\033[2J\033[H'


# ================================================================================
# ARTE ASCII
# ================================================================================

BANNER_SACYTY = f"""
{C.RED_BOLD}================================================================================
   ███████╗ █████╗  ██████╗██╗   ██╗████████╗██╗   ██╗
   ██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝╚══██╔══╝╚██╗ ██╔╝
   ███████╗███████║██║      ╚████╔╝    ██║    ╚████╔╝
   ╚════██║██╔══██║██║       ╚██╔╝     ██║     ╚██╔╝
   ███████║██║  ██║╚██████╗   ██║      ██║      ██║
   ╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝      ╚═╝      ╚═╝
================================================================================{C.RESET}
{C.GREEN}    Sistema de Acceso a Consultas Y Terminales - DB2 Query Tool{C.RESET}
{C.DIM}    Manhattan WMS - CEDIS Chedraui Cancun 427{C.RESET}
{C.RED}================================================================================{C.RESET}
"""

BANNER_LOGIN = f"""
{C.RED}================================================================================
   ██╗      ██████╗  ██████╗ ██╗███╗   ██╗
   ██║     ██╔═══██╗██╔════╝ ██║████╗  ██║
   ██║     ██║   ██║██║  ███╗██║██╔██╗ ██║
   ██║     ██║   ██║██║   ██║██║██║╚██╗██║
   ███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║
   ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝
================================================================================{C.RESET}
"""

BANNER_CONNECTED = f"""
{C.GREEN}================================================================================
    ██████╗ ██████╗ ███╗   ██╗███████╗ ██████╗████████╗███████╗██████╗
   ██╔════╝██╔═══██╗████╗  ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗
   ██║     ██║   ██║██╔██╗ ██║█████╗  ██║        ██║   █████╗  ██║  ██║
   ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║        ██║   ██╔══╝  ██║  ██║
   ╚██████╗╚██████╔╝██║ ╚████║███████╗╚██████╗   ██║   ███████╗██████╔╝
    ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   ╚══════╝╚═════╝
================================================================================{C.RESET}
"""

BANNER_QUERY = f"""
{C.GREEN}================================================================================
    ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗
   ██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝
   ██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝
   ██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝
   ╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║
    ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝
================================================================================{C.RESET}
"""

BANNER_ERROR = f"""
{C.RED}================================================================================
   ███████╗██████╗ ██████╗  ██████╗ ██████╗
   ██╔════╝██╔══██╗██╔══██╗██╔═══██╗██╔══██╗
   █████╗  ██████╔╝██████╔╝██║   ██║██████╔╝
   ██╔══╝  ██╔══██╗██╔══██╗██║   ██║██╔══██╗
   ███████╗██║  ██║██║  ██║╚██████╔╝██║  ██║
   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
================================================================================{C.RESET}
"""

BANNER_EXIT = f"""
{C.RED}================================================================================
    ██████╗  ██████╗  ██████╗ ██████╗ ██████╗ ██╗   ██╗███████╗
   ██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔════╝
   ██║  ███╗██║   ██║██║   ██║██║  ██║██████╔╝ ╚████╔╝ █████╗
   ██║   ██║██║   ██║██║   ██║██║  ██║██╔══██╗  ╚██╔╝  ██╔══╝
   ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║   ███████╗
    ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝   ╚══════╝
================================================================================{C.RESET}
{C.GREEN}    Gracias por usar SACYTY - Hasta pronto!{C.RESET}
{C.DIM}    "Las maquinas y los sistemas al servicio de los analistas"{C.RESET}
{C.RED}================================================================================{C.RESET}
"""


# ================================================================================
# CONFIGURACION DE BASE DE DATOS
# ================================================================================

class DBConfig:
    """Configuracion de conexion a DB2"""

    # Valores por defecto (Manhattan WMS)
    DEFAULT_HOST = 'WM260BASD'
    DEFAULT_PORT = 50000
    DEFAULT_DATABASE = 'WM260BASD'
    DEFAULT_SCHEMA = 'WMWHSE1'
    DEFAULT_DRIVER = '{IBM DB2 ODBC DRIVER}'
    DEFAULT_TIMEOUT = 30

    def __init__(self):
        self.host = os.getenv('DB_HOST', self.DEFAULT_HOST)
        self.port = int(os.getenv('DB_PORT', self.DEFAULT_PORT))
        self.database = os.getenv('DB_DATABASE', self.DEFAULT_DATABASE)
        self.schema = os.getenv('DB_SCHEMA', self.DEFAULT_SCHEMA)
        self.driver = os.getenv('DB_DRIVER', self.DEFAULT_DRIVER)
        self.timeout = int(os.getenv('DB_TIMEOUT', self.DEFAULT_TIMEOUT))
        self.user = None
        self.password = None

    def set_credentials(self, user: str, password: str):
        """Establece las credenciales de usuario"""
        self.user = user
        self.password = password

    def get_connection_string(self) -> str:
        """Genera el string de conexion ODBC"""
        return (
            f"DRIVER={self.driver};"
            f"HOSTNAME={self.host};"
            f"PORT={self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"CONNECTTIMEOUT={self.timeout};"
        )

    def get_ibm_connection_string(self) -> str:
        """Genera el string de conexion para ibm_db"""
        return (
            f"DATABASE={self.database};"
            f"HOSTNAME={self.host};"
            f"PORT={self.port};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.user};"
            f"PWD={self.password};"
        )


# ================================================================================
# CONEXION A BASE DE DATOS
# ================================================================================

class DB2Connector:
    """Conector simple a DB2 para SACYTY"""

    def __init__(self, config: DBConfig):
        self.config = config
        self.connection = None
        self.cursor = None
        self.driver_type = None
        self._detect_driver()

    def _detect_driver(self):
        """Detecta el driver disponible"""
        try:
            import pyodbc
            self.driver_type = 'pyodbc'
            return
        except ImportError:
            pass

        try:
            import ibm_db
            self.driver_type = 'ibm_db'
            return
        except ImportError:
            pass

        self.driver_type = None

    def connect(self) -> Tuple[bool, str]:
        """
        Conecta a la base de datos

        Returns:
            Tuple[bool, str]: (exito, mensaje)
        """
        if not self.driver_type:
            return False, "No hay driver DB2 disponible. Instala pyodbc o ibm-db"

        if not self.config.user or not self.config.password:
            return False, "Credenciales no configuradas"

        try:
            if self.driver_type == 'pyodbc':
                import pyodbc
                conn_str = self.config.get_connection_string()
                self.connection = pyodbc.connect(conn_str, timeout=self.config.timeout)
                self.cursor = self.connection.cursor()
            else:
                import ibm_db
                conn_str = self.config.get_ibm_connection_string()
                self.connection = ibm_db.connect(conn_str, "", "")

            return True, f"Conectado a {self.config.database}@{self.config.host}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        """Desconecta de la base de datos"""
        try:
            if self.cursor:
                if self.driver_type == 'pyodbc':
                    self.cursor.close()
                self.cursor = None

            if self.connection:
                if self.driver_type == 'pyodbc':
                    self.connection.close()
                else:
                    import ibm_db
                    ibm_db.close(self.connection)
                self.connection = None
        except Exception:
            pass

    def is_connected(self) -> bool:
        """Verifica si hay conexion activa"""
        if not self.connection:
            return False

        try:
            if self.driver_type == 'pyodbc':
                self.cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
                self.cursor.fetchone()
            else:
                import ibm_db
                stmt = ibm_db.exec_immediate(self.connection, "SELECT 1 FROM SYSIBM.SYSDUMMY1")
                ibm_db.fetch_row(stmt)
            return True
        except Exception:
            return False

    def execute_query(self, sql: str) -> Tuple[bool, any, str]:
        """
        Ejecuta una consulta SQL

        Args:
            sql: Consulta SQL a ejecutar

        Returns:
            Tuple[bool, data, str]: (exito, datos/None, mensaje)
        """
        if not self.connection:
            return False, None, "No hay conexion activa"

        start_time = time.time()

        try:
            if self.driver_type == 'pyodbc':
                self.cursor.execute(sql)

                # Verificar si es SELECT (tiene resultados)
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    rows = self.cursor.fetchall()
                    elapsed = time.time() - start_time

                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame.from_records(rows, columns=columns)
                        return True, df, f"{len(rows)} filas en {elapsed:.3f}s"
                    else:
                        return True, (columns, rows), f"{len(rows)} filas en {elapsed:.3f}s"
                else:
                    # INSERT, UPDATE, DELETE
                    rows_affected = self.cursor.rowcount
                    self.connection.commit()
                    elapsed = time.time() - start_time
                    return True, None, f"{rows_affected} filas afectadas en {elapsed:.3f}s"

            else:
                # ibm_db
                import ibm_db
                stmt = ibm_db.exec_immediate(self.connection, sql)

                # Obtener columnas
                col_count = ibm_db.num_fields(stmt)
                if col_count > 0:
                    columns = []
                    for i in range(col_count):
                        columns.append(ibm_db.field_name(stmt, i))

                    rows = []
                    row = ibm_db.fetch_tuple(stmt)
                    while row:
                        rows.append(row)
                        row = ibm_db.fetch_tuple(stmt)

                    elapsed = time.time() - start_time

                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame(rows, columns=columns)
                        return True, df, f"{len(rows)} filas en {elapsed:.3f}s"
                    else:
                        return True, (columns, rows), f"{len(rows)} filas en {elapsed:.3f}s"
                else:
                    rows_affected = ibm_db.num_rows(stmt)
                    ibm_db.commit(self.connection)
                    elapsed = time.time() - start_time
                    return True, None, f"{rows_affected} filas afectadas en {elapsed:.3f}s"

        except Exception as e:
            return False, None, str(e)


# ================================================================================
# FORMATEADOR DE RESULTADOS
# ================================================================================

class ResultFormatter:
    """Formatea resultados para la terminal"""

    @staticmethod
    def format_table(data, max_col_width: int = 40, max_rows: int = 100) -> str:
        """Formatea datos como tabla ASCII"""
        if data is None:
            return ""

        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return ResultFormatter._format_dataframe(data, max_col_width, max_rows)
        elif isinstance(data, tuple) and len(data) == 2:
            columns, rows = data
            return ResultFormatter._format_list(columns, rows, max_col_width, max_rows)
        else:
            return str(data)

    @staticmethod
    def _format_dataframe(df: 'pd.DataFrame', max_col_width: int, max_rows: int) -> str:
        """Formatea un DataFrame como tabla"""
        if df.empty:
            return f"{C.DIM}(Sin resultados){C.RESET}"

        # Limitar filas
        truncated = False
        if len(df) > max_rows:
            df = df.head(max_rows)
            truncated = True

        # Calcular anchos de columna
        col_widths = {}
        for col in df.columns:
            max_len = max(len(str(col)), df[col].astype(str).str.len().max())
            col_widths[col] = min(max_len, max_col_width)

        # Construir tabla
        lines = []

        # Separador
        sep = f"{C.RED}+" + "+".join(["-" * (w + 2) for w in col_widths.values()]) + f"+{C.RESET}"

        # Header
        lines.append(sep)
        header = f"{C.GREEN}|" + "|".join([
            f" {str(col)[:w].ljust(w)} "
            for col, w in col_widths.items()
        ]) + f"|{C.RESET}"
        lines.append(header)
        lines.append(sep)

        # Datos
        for _, row in df.iterrows():
            line = f"{C.DIM}|{C.RESET}" + f"{C.DIM}|{C.RESET}".join([
                f" {str(row[col])[:w].ljust(w)} "
                for col, w in col_widths.items()
            ]) + f"{C.DIM}|{C.RESET}"
            lines.append(line)

        lines.append(sep)

        if truncated:
            lines.append(f"{C.RED}... (mostrando {max_rows} de {len(df)} filas){C.RESET}")

        return "\n".join(lines)

    @staticmethod
    def _format_list(columns: list, rows: list, max_col_width: int, max_rows: int) -> str:
        """Formatea listas como tabla"""
        if not rows:
            return f"{C.DIM}(Sin resultados){C.RESET}"

        # Limitar filas
        truncated = False
        total_rows = len(rows)
        if len(rows) > max_rows:
            rows = rows[:max_rows]
            truncated = True

        # Calcular anchos
        col_widths = []
        for i, col in enumerate(columns):
            max_len = len(str(col))
            for row in rows:
                if i < len(row):
                    max_len = max(max_len, len(str(row[i])))
            col_widths.append(min(max_len, max_col_width))

        # Construir tabla
        lines = []

        # Separador
        sep = f"{C.RED}+" + "+".join(["-" * (w + 2) for w in col_widths]) + f"+{C.RESET}"

        # Header
        lines.append(sep)
        header = f"{C.GREEN}|" + "|".join([
            f" {str(columns[i])[:w].ljust(w)} "
            for i, w in enumerate(col_widths)
        ]) + f"|{C.RESET}"
        lines.append(header)
        lines.append(sep)

        # Datos
        for row in rows:
            line = f"{C.DIM}|{C.RESET}" + f"{C.DIM}|{C.RESET}".join([
                f" {str(row[i] if i < len(row) else '')[:w].ljust(w)} "
                for i, w in enumerate(col_widths)
            ]) + f"{C.DIM}|{C.RESET}"
            lines.append(line)

        lines.append(sep)

        if truncated:
            lines.append(f"{C.RED}... (mostrando {max_rows} de {total_rows} filas){C.RESET}")

        return "\n".join(lines)


# ================================================================================
# HISTORIAL DE COMANDOS
# ================================================================================

class CommandHistory:
    """Historial de comandos ejecutados"""

    def __init__(self, max_size: int = 100):
        self.history: List[str] = []
        self.max_size = max_size
        self.position = 0

    def add(self, command: str):
        """Agrega un comando al historial"""
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
            if len(self.history) > self.max_size:
                self.history.pop(0)
        self.position = len(self.history)

    def get_previous(self) -> Optional[str]:
        """Obtiene el comando anterior"""
        if self.position > 0:
            self.position -= 1
            return self.history[self.position]
        return None

    def get_next(self) -> Optional[str]:
        """Obtiene el siguiente comando"""
        if self.position < len(self.history) - 1:
            self.position += 1
            return self.history[self.position]
        return None

    def show(self):
        """Muestra el historial"""
        print(f"\n{C.GREEN}=== HISTORIAL DE COMANDOS ==={C.RESET}")
        for i, cmd in enumerate(self.history[-20:], 1):
            print(f"{C.DIM}{i:3d}:{C.RESET} {cmd[:70]}{'...' if len(cmd) > 70 else ''}")
        print()


# ================================================================================
# QUERIES PREDEFINIDAS
# ================================================================================

QUICK_QUERIES = {
    '1': ('OC Pendientes', '''
SELECT EXTERNRECEIPTKEY AS OC, STORERKEY, STATUS,
       ADDDATE, ADDWHO, QTY_EXPECTED
FROM WMWHSE1.RECEIPT
WHERE STATUS < '9'
ORDER BY ADDDATE DESC
FETCH FIRST 50 ROWS ONLY
'''),
    '2': ('ASN Pendientes', '''
SELECT RECEIPTKEY, EXTERNRECEIPTKEY AS OC, STATUS,
       ADDDATE, EDITDATE
FROM WMWHSE1.RECEIPT
WHERE STATUS IN ('0','1','2')
ORDER BY ADDDATE DESC
FETCH FIRST 50 ROWS ONLY
'''),
    '3': ('SKU Info', '''
SELECT SKU, DESCR, STORERKEY, PACKKEY,
       STDCUBE, STDGROSSWGT
FROM WMWHSE1.SKU
FETCH FIRST 50 ROWS ONLY
'''),
    '4': ('Usuarios Activos', '''
SELECT USERKEY, USERNAME, USERGROUP, STATUS,
       LASTLOGON
FROM WMWHSE1.STORER
WHERE STATUS = '1'
ORDER BY LASTLOGON DESC
FETCH FIRST 30 ROWS ONLY
'''),
    '5': ('LPN Recientes', '''
SELECT LPN, RECEIPTKEY, STATUS, ADDDATE,
       LOCATION, SKU
FROM WMWHSE1.LPNDETAIL
ORDER BY ADDDATE DESC
FETCH FIRST 50 ROWS ONLY
'''),
    '6': ('Ubicaciones', '''
SELECT LOC, LOCATIONTYPE, PUTAWAYZONE, STATUS
FROM WMWHSE1.LOC
FETCH FIRST 50 ROWS ONLY
'''),
}


# ================================================================================
# CLASE PRINCIPAL SACYTY
# ================================================================================

class SACYTY:
    """Sistema de Acceso a Consultas Y Terminales"""

    VERSION = "1.0.0"

    def __init__(self):
        self.config = DBConfig()
        self.connector = None
        self.user = None
        self.history = CommandHistory()
        self.running = True
        self.connected = False

        # Configurar manejador de señales
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """Maneja Ctrl+C"""
        print(f"\n\n{C.RED}Interrupcion detectada...{C.RESET}")
        self.exit()

    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_status_bar(self):
        """Imprime la barra de estado"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = f"{C.GREEN}ONLINE{C.RESET}" if self.connected else f"{C.RED}OFFLINE{C.RESET}"

        print(f"{C.RED}================================================================================{C.RESET}")
        print(f"{C.DIM}  Usuario:{C.RESET} {C.GREEN}{self.user or 'N/A'}{C.RESET} | "
              f"{C.DIM}DB:{C.RESET} {C.GREEN}{self.config.database}{C.RESET} | "
              f"{C.DIM}Estado:{C.RESET} {status} | "
              f"{C.DIM}Hora:{C.RESET} {now}")
        print(f"{C.RED}================================================================================{C.RESET}")

    def login(self) -> bool:
        """Proceso de login"""
        self.clear_screen()
        print(BANNER_LOGIN)

        print(f"{C.GREEN}  Ingresa tus credenciales de DB2 (Manhattan WMS){C.RESET}")
        print(f"{C.DIM}  Host: {self.config.host} | Database: {self.config.database}{C.RESET}")
        print(f"{C.RED}================================================================================{C.RESET}\n")

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            print(f"  {C.DIM}Intento {attempt}/{max_attempts}{C.RESET}")

            try:
                user = input(f"  {C.GREEN}Usuario:{C.RESET} ").strip()
                if not user:
                    print(f"  {C.RED}Usuario requerido{C.RESET}\n")
                    continue

                password = getpass.getpass(f"  {C.GREEN}Password:{C.RESET} ")
                if not password:
                    print(f"  {C.RED}Password requerido{C.RESET}\n")
                    continue

            except (EOFError, KeyboardInterrupt):
                return False

            print(f"\n  {C.DIM}Conectando...{C.RESET}")

            # Configurar credenciales
            self.config.set_credentials(user, password)
            self.connector = DB2Connector(self.config)

            # Intentar conexion
            success, message = self.connector.connect()

            if success:
                self.user = user
                self.connected = True
                print(f"\n  {C.GREEN}[OK] {message}{C.RESET}")
                time.sleep(1)
                return True
            else:
                print(f"\n  {C.RED}[ERROR] {message}{C.RESET}\n")
                self.connector = None

        print(f"\n{C.RED}  Maximo de intentos alcanzado{C.RESET}")
        return False

    def show_help(self):
        """Muestra la ayuda"""
        help_text = f"""
{C.GREEN}=== COMANDOS DISPONIBLES ==={C.RESET}

{C.RED}CONSULTAS:{C.RESET}
  {C.GREEN}SQL{C.RESET}          Escribe cualquier query SQL directamente
  {C.GREEN}/q1-6{C.RESET}        Queries rapidas predefinidas
  {C.GREEN}/queries{C.RESET}     Lista de queries predefinidas

{C.RED}NAVEGACION:{C.RESET}
  {C.GREEN}/history{C.RESET}     Historial de comandos
  {C.GREEN}/clear{C.RESET}       Limpiar pantalla
  {C.GREEN}/status{C.RESET}      Estado de la conexion

{C.RED}SISTEMA:{C.RESET}
  {C.GREEN}/reconnect{C.RESET}   Reconectar a DB2
  {C.GREEN}/help{C.RESET}        Mostrar esta ayuda
  {C.GREEN}/exit{C.RESET}        Salir de SACYTY
  {C.GREEN}exit{C.RESET}         Salir de SACYTY

{C.RED}TIPS:{C.RESET}
  - Termina las queries con ; para ejecutar
  - Queries multilinea: escribe sin ; y presiona Enter
  - Para cancelar una query multilinea, escribe /cancel
"""
        print(help_text)

    def show_quick_queries(self):
        """Muestra las queries predefinidas"""
        print(f"\n{C.GREEN}=== QUERIES RAPIDAS ==={C.RESET}")
        for key, (name, _) in QUICK_QUERIES.items():
            print(f"  {C.GREEN}/q{key}{C.RESET} - {name}")
        print()

    def execute_quick_query(self, key: str):
        """Ejecuta una query predefinida"""
        if key in QUICK_QUERIES:
            name, sql = QUICK_QUERIES[key]
            print(f"\n{C.GREEN}Ejecutando: {name}{C.RESET}")
            self.execute_sql(sql.strip())
        else:
            print(f"{C.RED}Query no encontrada: /q{key}{C.RESET}")

    def execute_sql(self, sql: str):
        """Ejecuta una consulta SQL"""
        if not self.connected:
            print(f"{C.RED}No hay conexion activa{C.RESET}")
            return

        # Limpiar query
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]

        if not sql:
            return

        # Agregar al historial
        self.history.add(sql)

        # Ejecutar
        print(f"\n{C.DIM}Ejecutando...{C.RESET}")
        success, data, message = self.connector.execute_query(sql)

        if success:
            print(f"{C.GREEN}[OK] {message}{C.RESET}\n")
            if data is not None:
                print(ResultFormatter.format_table(data))
        else:
            print(f"{C.RED}[ERROR] {message}{C.RESET}")

        print()

    def show_status(self):
        """Muestra el estado de la conexion"""
        print(f"\n{C.GREEN}=== ESTADO DEL SISTEMA ==={C.RESET}")
        print(f"  {C.DIM}Version:{C.RESET} {self.VERSION}")
        print(f"  {C.DIM}Usuario:{C.RESET} {self.user or 'N/A'}")
        print(f"  {C.DIM}Host:{C.RESET} {self.config.host}")
        print(f"  {C.DIM}Puerto:{C.RESET} {self.config.port}")
        print(f"  {C.DIM}Database:{C.RESET} {self.config.database}")
        print(f"  {C.DIM}Schema:{C.RESET} {self.config.schema}")

        if self.connector:
            driver = self.connector.driver_type or 'Ninguno'
            print(f"  {C.DIM}Driver:{C.RESET} {driver}")

        is_connected = self.connector.is_connected() if self.connector else False
        status = f"{C.GREEN}CONECTADO{C.RESET}" if is_connected else f"{C.RED}DESCONECTADO{C.RESET}"
        print(f"  {C.DIM}Estado:{C.RESET} {status}")
        print()

    def reconnect(self):
        """Reconecta a la base de datos"""
        print(f"\n{C.DIM}Reconectando...{C.RESET}")

        if self.connector:
            self.connector.disconnect()

        self.connector = DB2Connector(self.config)
        success, message = self.connector.connect()

        if success:
            self.connected = True
            print(f"{C.GREEN}[OK] {message}{C.RESET}")
        else:
            self.connected = False
            print(f"{C.RED}[ERROR] {message}{C.RESET}")

    def process_command(self, cmd: str):
        """Procesa un comando"""
        cmd_lower = cmd.lower().strip()

        # Comandos especiales
        if cmd_lower in ['exit', 'quit', '/exit', '/quit']:
            self.exit()
            return

        if cmd_lower in ['/help', '/?', 'help']:
            self.show_help()
            return

        if cmd_lower == '/clear':
            self.clear_screen()
            self.print_status_bar()
            return

        if cmd_lower == '/history':
            self.history.show()
            return

        if cmd_lower == '/status':
            self.show_status()
            return

        if cmd_lower == '/reconnect':
            self.reconnect()
            return

        if cmd_lower == '/queries':
            self.show_quick_queries()
            return

        # Queries rapidas /q1, /q2, etc
        if cmd_lower.startswith('/q') and len(cmd_lower) >= 3:
            key = cmd_lower[2:]
            self.execute_quick_query(key)
            return

        # Si es SQL, ejecutar
        if cmd.strip():
            self.execute_sql(cmd)

    def read_multiline_sql(self, first_line: str) -> str:
        """Lee una query SQL multilinea"""
        lines = [first_line]

        print(f"{C.DIM}... (continua, termina con ; o escribe /cancel){C.RESET}")

        while True:
            try:
                line = input(f"{C.DIM}...{C.RESET} ")
            except (EOFError, KeyboardInterrupt):
                return ""

            if line.strip().lower() == '/cancel':
                print(f"{C.DIM}Query cancelada{C.RESET}")
                return ""

            lines.append(line)

            # Verificar si termina con ;
            full_sql = '\n'.join(lines)
            if full_sql.strip().endswith(';'):
                return full_sql

    def main_loop(self):
        """Loop principal de SACYTY"""
        self.clear_screen()
        print(BANNER_CONNECTED)

        print(f"{C.GREEN}  Bienvenido a SACYTY!{C.RESET}")
        print(f"{C.DIM}  Escribe /help para ver los comandos disponibles{C.RESET}")
        print(f"{C.DIM}  Escribe SQL directamente para ejecutar consultas{C.RESET}\n")

        self.print_status_bar()

        while self.running:
            try:
                # Prompt
                prompt = f"\n{C.GREEN}SACYTY>{C.RESET} "
                cmd = input(prompt).strip()

                if not cmd:
                    continue

                # Verificar si es multilinea (no termina con ; y parece SQL)
                sql_keywords = ['select', 'insert', 'update', 'delete', 'with', 'create', 'alter', 'drop']
                first_word = cmd.split()[0].lower() if cmd.split() else ''

                if first_word in sql_keywords and not cmd.strip().endswith(';'):
                    cmd = self.read_multiline_sql(cmd)
                    if not cmd:
                        continue

                self.process_command(cmd)

            except (EOFError, KeyboardInterrupt):
                print()
                self.exit()
                break

    def exit(self):
        """Sale de SACYTY"""
        self.running = False

        if self.connector:
            self.connector.disconnect()

        self.clear_screen()
        print(BANNER_EXIT)

    def run(self):
        """Ejecuta SACYTY"""
        self.clear_screen()
        print(BANNER_SACYTY)

        # Verificar driver disponible
        test_connector = DB2Connector(self.config)
        if not test_connector.driver_type:
            print(f"\n{C.RED}ERROR: No hay driver DB2 disponible{C.RESET}")
            print(f"{C.DIM}Instala uno de los siguientes:{C.RESET}")
            print(f"  pip install pyodbc")
            print(f"  pip install ibm-db")
            return

        print(f"{C.DIM}  Driver detectado: {test_connector.driver_type}{C.RESET}\n")

        time.sleep(1)

        # Login
        if self.login():
            self.main_loop()
        else:
            print(f"\n{C.RED}No se pudo establecer conexion{C.RESET}")
            time.sleep(2)


# ================================================================================
# PUNTO DE ENTRADA
# ================================================================================

def main():
    """Funcion principal"""
    app = SACYTY()
    app.run()


if __name__ == "__main__":
    main()
