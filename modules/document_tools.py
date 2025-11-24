"""
═══════════════════════════════════════════════════════════════
MÓDULO DE HERRAMIENTAS DE DOCUMENTOS - SAC VISION 3.0
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Herramientas para manejo de documentos:
- Excel (crear, leer, editar, formatear)
- PDF (leer, extraer texto, crear)
- Word (crear, editar)
- CSV (leer, escribir)
- Texto (leer, escribir, editar)

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import csv
import io

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class DocumentResult:
    """Resultado de operación con documentos"""
    success: bool
    message: str
    data: Any = None
    path: Optional[str] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# HERRAMIENTAS DE EXCEL
# ═══════════════════════════════════════════════════════════════

class ExcelTools:
    """Herramientas para manipulación de archivos Excel"""

    def __init__(self):
        self._pandas = None
        self._openpyxl = None
        self._init_dependencies()

    def _init_dependencies(self):
        """Inicializa dependencias"""
        try:
            import pandas as pd
            self._pandas = pd
            logger.info("✅ Pandas disponible para Excel")
        except ImportError:
            logger.warning("⚠️ pandas no instalado")

        try:
            import openpyxl
            self._openpyxl = openpyxl
            logger.info("✅ openpyxl disponible para Excel")
        except ImportError:
            logger.warning("⚠️ openpyxl no instalado")

    def read_excel(
        self,
        path: str,
        sheet_name: Union[str, int] = 0,
        header: int = 0
    ) -> DocumentResult:
        """
        Lee un archivo Excel

        Args:
            path: Ruta del archivo
            sheet_name: Nombre o índice de la hoja
            header: Fila del encabezado

        Returns:
            DocumentResult con DataFrame como data
        """
        if not self._pandas:
            return DocumentResult(
                success=False,
                message="pandas no disponible",
                error="Instala pandas: pip install pandas"
            )

        try:
            df = self._pandas.read_excel(
                path,
                sheet_name=sheet_name,
                header=header
            )

            return DocumentResult(
                success=True,
                message=f"Excel leído: {len(df)} filas, {len(df.columns)} columnas",
                data=df,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error leyendo Excel",
                error=str(e)
            )

    def write_excel(
        self,
        data: Any,
        path: str,
        sheet_name: str = "Datos",
        index: bool = False
    ) -> DocumentResult:
        """
        Escribe datos a un archivo Excel

        Args:
            data: DataFrame o lista de diccionarios
            path: Ruta de destino
            sheet_name: Nombre de la hoja
            index: Incluir índice

        Returns:
            DocumentResult
        """
        if not self._pandas:
            return DocumentResult(
                success=False,
                message="pandas no disponible",
                error="Instala pandas: pip install pandas"
            )

        try:
            # Convertir a DataFrame si es necesario
            if isinstance(data, list):
                df = self._pandas.DataFrame(data)
            else:
                df = data

            # Crear directorio si no existe
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            # Escribir Excel
            df.to_excel(path, sheet_name=sheet_name, index=index)

            return DocumentResult(
                success=True,
                message=f"Excel guardado: {len(df)} filas",
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error escribiendo Excel",
                error=str(e)
            )

    def excel_to_dict(self, path: str, sheet_name: Union[str, int] = 0) -> DocumentResult:
        """
        Convierte Excel a lista de diccionarios

        Args:
            path: Ruta del archivo
            sheet_name: Hoja a leer

        Returns:
            DocumentResult con lista de dicts como data
        """
        result = self.read_excel(path, sheet_name)

        if not result.success:
            return result

        try:
            records = result.data.to_dict(orient='records')
            return DocumentResult(
                success=True,
                message=f"Convertido: {len(records)} registros",
                data=records,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error convirtiendo",
                error=str(e)
            )

    def get_sheet_names(self, path: str) -> DocumentResult:
        """Obtiene nombres de hojas de un Excel"""
        if not self._pandas:
            return DocumentResult(
                success=False,
                message="pandas no disponible"
            )

        try:
            xl = self._pandas.ExcelFile(path)
            return DocumentResult(
                success=True,
                message=f"{len(xl.sheet_names)} hojas encontradas",
                data=xl.sheet_names,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error obteniendo hojas",
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# HERRAMIENTAS DE PDF
# ═══════════════════════════════════════════════════════════════

class PDFTools:
    """Herramientas para manipulación de archivos PDF"""

    def __init__(self):
        self._pypdf = None
        self._reportlab = None
        self._init_dependencies()

    def _init_dependencies(self):
        """Inicializa dependencias"""
        try:
            import pypdf
            self._pypdf = pypdf
            logger.info("✅ pypdf disponible para PDF")
        except ImportError:
            try:
                import PyPDF2 as pypdf
                self._pypdf = pypdf
                logger.info("✅ PyPDF2 disponible para PDF")
            except ImportError:
                logger.warning("⚠️ pypdf/PyPDF2 no instalado")

        try:
            from reportlab.pdfgen import canvas
            self._reportlab = canvas
            logger.info("✅ reportlab disponible para crear PDF")
        except ImportError:
            logger.warning("⚠️ reportlab no instalado")

    def read_pdf(self, path: str) -> DocumentResult:
        """
        Lee texto de un archivo PDF

        Args:
            path: Ruta del archivo PDF

        Returns:
            DocumentResult con texto extraído
        """
        if not self._pypdf:
            return DocumentResult(
                success=False,
                message="pypdf no disponible",
                error="Instala pypdf: pip install pypdf"
            )

        try:
            with open(path, 'rb') as file:
                reader = self._pypdf.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"

                return DocumentResult(
                    success=True,
                    message=f"PDF leído: {len(reader.pages)} páginas",
                    data={
                        'text': text,
                        'pages': len(reader.pages),
                        'metadata': dict(reader.metadata) if reader.metadata else {}
                    },
                    path=path
                )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error leyendo PDF",
                error=str(e)
            )

    def get_pdf_info(self, path: str) -> DocumentResult:
        """Obtiene información de un PDF"""
        if not self._pypdf:
            return DocumentResult(
                success=False,
                message="pypdf no disponible"
            )

        try:
            with open(path, 'rb') as file:
                reader = self._pypdf.PdfReader(file)

                info = {
                    'pages': len(reader.pages),
                    'encrypted': reader.is_encrypted,
                    'metadata': {}
                }

                if reader.metadata:
                    for key in reader.metadata:
                        try:
                            info['metadata'][key] = str(reader.metadata[key])
                        except:
                            pass

                return DocumentResult(
                    success=True,
                    message=f"PDF: {info['pages']} páginas",
                    data=info,
                    path=path
                )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error obteniendo info",
                error=str(e)
            )

    def create_simple_pdf(
        self,
        path: str,
        content: str,
        title: str = "Documento SAC"
    ) -> DocumentResult:
        """
        Crea un PDF simple con texto

        Args:
            path: Ruta de destino
            content: Contenido de texto
            title: Título del documento

        Returns:
            DocumentResult
        """
        if not self._reportlab:
            return DocumentResult(
                success=False,
                message="reportlab no disponible",
                error="Instala reportlab: pip install reportlab"
            )

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            # Crear directorio si no existe
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter

            # Título
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, title)

            # Contenido
            c.setFont("Helvetica", 10)
            y = height - 80
            for line in content.split('\n'):
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 50
                c.drawString(50, y, line[:100])  # Limitar longitud de línea
                y -= 14

            c.save()

            return DocumentResult(
                success=True,
                message="PDF creado",
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error creando PDF",
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# HERRAMIENTAS DE CSV
# ═══════════════════════════════════════════════════════════════

class CSVTools:
    """Herramientas para manipulación de archivos CSV"""

    def read_csv(
        self,
        path: str,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> DocumentResult:
        """
        Lee un archivo CSV

        Args:
            path: Ruta del archivo
            delimiter: Delimitador
            encoding: Codificación

        Returns:
            DocumentResult con lista de diccionarios
        """
        try:
            records = []
            with open(path, 'r', encoding=encoding, newline='') as file:
                reader = csv.DictReader(file, delimiter=delimiter)
                for row in reader:
                    records.append(dict(row))

            return DocumentResult(
                success=True,
                message=f"CSV leído: {len(records)} registros",
                data=records,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error leyendo CSV",
                error=str(e)
            )

    def write_csv(
        self,
        data: List[Dict],
        path: str,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> DocumentResult:
        """
        Escribe datos a un archivo CSV

        Args:
            data: Lista de diccionarios
            path: Ruta de destino
            delimiter: Delimitador
            encoding: Codificación

        Returns:
            DocumentResult
        """
        if not data:
            return DocumentResult(
                success=False,
                message="Datos vacíos",
                error="No hay datos para escribir"
            )

        try:
            # Crear directorio si no existe
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            fieldnames = list(data[0].keys())

            with open(path, 'w', encoding=encoding, newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)

            return DocumentResult(
                success=True,
                message=f"CSV guardado: {len(data)} registros",
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error escribiendo CSV",
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# HERRAMIENTAS DE TEXTO
# ═══════════════════════════════════════════════════════════════

class TextTools:
    """Herramientas para manipulación de archivos de texto"""

    def read_text(self, path: str, encoding: str = 'utf-8') -> DocumentResult:
        """Lee un archivo de texto"""
        try:
            with open(path, 'r', encoding=encoding) as file:
                content = file.read()

            lines = content.count('\n') + 1
            return DocumentResult(
                success=True,
                message=f"Texto leído: {lines} líneas, {len(content)} caracteres",
                data=content,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error leyendo texto",
                error=str(e)
            )

    def write_text(
        self,
        content: str,
        path: str,
        encoding: str = 'utf-8',
        append: bool = False
    ) -> DocumentResult:
        """Escribe contenido a un archivo de texto"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            mode = 'a' if append else 'w'
            with open(path, mode, encoding=encoding) as file:
                file.write(content)

            return DocumentResult(
                success=True,
                message=f"Texto guardado: {len(content)} caracteres",
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error escribiendo texto",
                error=str(e)
            )

    def search_in_text(self, path: str, pattern: str, encoding: str = 'utf-8') -> DocumentResult:
        """Busca un patrón en un archivo de texto"""
        try:
            import re

            with open(path, 'r', encoding=encoding) as file:
                content = file.read()

            matches = []
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(pattern, line):
                    matches.append({
                        'line_number': i,
                        'content': line.strip()
                    })

            return DocumentResult(
                success=True,
                message=f"Encontrados: {len(matches)} coincidencias",
                data=matches,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error buscando",
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════
# CLASE INTEGRADORA
# ═══════════════════════════════════════════════════════════════

class DocumentTools:
    """
    Clase integradora de todas las herramientas de documentos

    Proporciona acceso unificado a:
    - Excel
    - PDF
    - CSV
    - Texto
    """

    def __init__(self):
        self.excel = ExcelTools()
        self.pdf = PDFTools()
        self.csv = CSVTools()
        self.text = TextTools()

        logger.info("📄 Document Tools inicializado")

    def detect_file_type(self, path: str) -> str:
        """Detecta el tipo de archivo por extensión"""
        ext = Path(path).suffix.lower()
        type_map = {
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.xlsm': 'excel',
            '.pdf': 'pdf',
            '.csv': 'csv',
            '.txt': 'text',
            '.md': 'text',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.py': 'code',
            '.js': 'code',
            '.sql': 'code',
        }
        return type_map.get(ext, 'unknown')

    def read_file(self, path: str) -> DocumentResult:
        """
        Lee un archivo automáticamente detectando el tipo

        Args:
            path: Ruta del archivo

        Returns:
            DocumentResult con contenido
        """
        file_type = self.detect_file_type(path)

        if file_type == 'excel':
            return self.excel.read_excel(path)
        elif file_type == 'pdf':
            return self.pdf.read_pdf(path)
        elif file_type == 'csv':
            return self.csv.read_csv(path)
        elif file_type == 'json':
            return self._read_json(path)
        else:
            return self.text.read_text(path)

    def _read_json(self, path: str) -> DocumentResult:
        """Lee un archivo JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            return DocumentResult(
                success=True,
                message="JSON leído",
                data=data,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error leyendo JSON",
                error=str(e)
            )

    def get_file_info(self, path: str) -> DocumentResult:
        """Obtiene información de un archivo"""
        try:
            file_path = Path(path)

            if not file_path.exists():
                return DocumentResult(
                    success=False,
                    message="Archivo no encontrado",
                    error=f"No existe: {path}"
                )

            stat = file_path.stat()
            info = {
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'type': self.detect_file_type(path),
                'extension': file_path.suffix,
                'size_bytes': stat.st_size,
                'size_human': self._human_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            }

            return DocumentResult(
                success=True,
                message=f"Info: {info['name']} ({info['size_human']})",
                data=info,
                path=path
            )

        except Exception as e:
            return DocumentResult(
                success=False,
                message="Error obteniendo info",
                error=str(e)
            )

    @staticmethod
    def _human_size(bytes_size: int) -> str:
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def is_available(self) -> Dict[str, bool]:
        """Verifica qué capacidades están disponibles"""
        return {
            'excel_read': self.excel._pandas is not None,
            'excel_write': self.excel._pandas is not None and self.excel._openpyxl is not None,
            'pdf_read': self.pdf._pypdf is not None,
            'pdf_create': self.pdf._reportlab is not None,
            'csv': True,
            'text': True,
            'json': True
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════

_document_tools: Optional[DocumentTools] = None


def get_document_tools() -> DocumentTools:
    """Obtiene la instancia global de DocumentTools"""
    global _document_tools
    if _document_tools is None:
        _document_tools = DocumentTools()
    return _document_tools


def read_document(path: str) -> Dict:
    """Lee un documento automáticamente"""
    tools = get_document_tools()
    result = tools.read_file(path)
    if result.success:
        return {'success': True, 'data': result.data, 'message': result.message}
    return {'success': False, 'error': result.error}


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PARA PRUEBAS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  📄 MÓDULO DE DOCUMENT TOOLS - SAC VISION 3.0                        ║
║  Prueba de capacidades                                                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    tools = DocumentTools()

    print("📋 Capacidades disponibles:")
    caps = tools.is_available()
    for cap, available in caps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {cap}")

    print("\n✅ Prueba completada")
