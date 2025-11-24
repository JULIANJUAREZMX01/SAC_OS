"""
===============================================================================
MÓDULO DE RECEPCIÓN DE CORREOS - SISTEMA SAC
Sistema de Automatización de Consultas - CEDIS Cancún 427
===============================================================================

Este módulo permite recibir y procesar correos electrónicos mediante IMAP
para detectar conflictos reportados externamente que no fueron detectados
por el sistema de monitoreo interno.

Funcionalidades:
- Conexión segura IMAP a buzón de correo
- Detección de correos con patrones de conflicto
- Extracción de adjuntos XLSX
- Parseo de cuerpo y asunto del correo
- Filtrado por patrones/palabras clave

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
===============================================================================
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import os
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES Y DATACLASSES
# ═══════════════════════════════════════════════════════════════

class TipoConflictoCorreo(Enum):
    """Tipos de conflicto detectables en correos"""
    DISTRIBUCION_EXCEDENTE = "DISTRIBUCION_EXCEDENTE"
    DISTRIBUCION_INCOMPLETA = "DISTRIBUCION_INCOMPLETA"
    OC_VENCIDA = "OC_VENCIDA"
    OC_NO_ENCONTRADA = "OC_NO_ENCONTRADA"
    TIENDA_INACTIVA = "TIENDA_INACTIVA"
    ASN_INVALIDO = "ASN_INVALIDO"
    SKU_SIN_IP = "SKU_SIN_IP"
    PROBLEMA_RECIBO = "PROBLEMA_RECIBO"
    PROBLEMA_PREPARADO = "PROBLEMA_PREPARADO"
    PROBLEMA_CARGADO = "PROBLEMA_CARGADO"
    PROBLEMA_EXPEDICION = "PROBLEMA_EXPEDICION"
    URGENTE = "URGENTE"
    OTRO = "OTRO"


class SeveridadConflicto(Enum):
    """Severidad del conflicto detectado"""
    CRITICO = "🔴 CRÍTICO"
    ALTO = "🟠 ALTO"
    MEDIO = "🟡 MEDIO"
    BAJO = "🟢 BAJO"
    INFO = "ℹ️ INFO"


@dataclass
class AdjuntoCorreo:
    """Representa un archivo adjunto de correo"""
    nombre: str
    contenido: bytes
    tipo_mime: str
    tamaño: int
    ruta_guardado: Optional[str] = None


@dataclass
class CorreoRecibido:
    """Representa un correo recibido con potencial conflicto"""
    id_mensaje: str
    fecha_recepcion: datetime
    remitente_email: str
    remitente_nombre: str
    asunto: str
    cuerpo_texto: str
    cuerpo_html: Optional[str]
    adjuntos: List[AdjuntoCorreo] = field(default_factory=list)

    # Análisis inicial
    tipo_conflicto_detectado: Optional[TipoConflictoCorreo] = None
    severidad_detectada: Optional[SeveridadConflicto] = None
    palabras_clave_encontradas: List[str] = field(default_factory=list)

    # Datos extraídos
    oc_numeros: List[str] = field(default_factory=list)
    tiendas_mencionadas: List[str] = field(default_factory=list)
    cantidades_mencionadas: List[float] = field(default_factory=list)

    # Estado de procesamiento
    procesado: bool = False
    fecha_procesamiento: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════
# PATRONES DE DETECCIÓN DE CONFLICTOS
# ═══════════════════════════════════════════════════════════════

PATRONES_CONFLICTO = {
    TipoConflictoCorreo.DISTRIBUCION_EXCEDENTE: [
        r'distribu[cióni]+[oó]?n?\s+(sobra|excede|más|demás|extra)',
        r'se\s+(distribu[yíi]|envi[óo]|mand[óo])\s+(más|extra|demás)',
        r'supera\s+la\s+OC',
        r'cantidad\s+distribuid[aoas]+\s+(?:es\s+)?mayor',
        r'exceso\s+de\s+distribuci[óo]n',
        r'sobr[ea]\s+distribuci[óo]n',
    ],

    TipoConflictoCorreo.DISTRIBUCION_INCOMPLETA: [
        r'falta[n]?\s*.*?distribuci[óo]n',
        r'distribuci[óo]n\s+incompleta',
        r'no\s+llega\s+a\s+la\s+cantidad',
        r'menos\s+de\s*.*?unidades',
        r'faltante\s+de\s+producto',
        r'unidades\s+faltantes',
    ],

    TipoConflictoCorreo.OC_VENCIDA: [
        r'OC\s+(?:vencida|expirada|sin\s+vigencia)',
        r'vigencia\s+terminada',
        r'orden\s+(?:de\s+compra\s+)?vencida',
        r'fuera\s+de\s+vigencia',
    ],

    TipoConflictoCorreo.OC_NO_ENCONTRADA: [
        r'OC\s+no\s+(?:existe|encontrada|registrada)',
        r'no\s+se\s+encuentra\s+(?:la\s+)?OC',
        r'orden\s+(?:de\s+compra\s+)?no\s+existe',
    ],

    TipoConflictoCorreo.TIENDA_INACTIVA: [
        r'tienda\s+(?:cerrada|inactiva|no\s+existe)',
        r'destino\s+(?:cerrado|inactivo)',
        r'sucursal\s+(?:cerrada|inactiva)',
    ],

    TipoConflictoCorreo.ASN_INVALIDO: [
        r'ASN\s+(?:inv[áa]lido|incorrecto|no\s+existe)',
        r'problema\s+(?:con\s+)?ASN',
        r'error\s+(?:en\s+)?ASN',
    ],

    TipoConflictoCorreo.SKU_SIN_IP: [
        r'SKU\s+sin\s+(?:inner\s+pack|IP)',
        r'falta\s+(?:el\s+)?inner\s+pack',
        r'producto\s+sin\s+IP',
    ],

    TipoConflictoCorreo.PROBLEMA_RECIBO: [
        r'problema\s+(?:en\s+)?(?:el\s+)?recibo',
        r'error\s+(?:de\s+)?recepci[óo]n',
        r'recibo\s+(?:fallido|con\s+error)',
        r'no\s+se\s+puede\s+recibir',
    ],

    TipoConflictoCorreo.PROBLEMA_PREPARADO: [
        r'problema\s+(?:en\s+)?(?:el\s+)?preparado',
        r'error\s+(?:de\s+)?preparaci[óo]n',
        r'picking\s+(?:fallido|con\s+error)',
        r'no\s+se\s+puede\s+preparar',
    ],

    TipoConflictoCorreo.PROBLEMA_CARGADO: [
        r'problema\s+(?:en\s+)?(?:el\s+)?cargado',
        r'error\s+(?:de\s+)?carga',
        r'loading\s+(?:fallido|con\s+error)',
        r'no\s+se\s+puede\s+cargar',
    ],

    TipoConflictoCorreo.PROBLEMA_EXPEDICION: [
        r'problema\s+(?:en\s+)?(?:la\s+)?expedici[óo]n',
        r'error\s+(?:de\s+)?expedici[óo]n',
        r'despacho\s+(?:fallido|con\s+error)',
        r'env[íi]o\s+(?:fallido|con\s+error)',
    ],

    TipoConflictoCorreo.URGENTE: [
        r'urgente',
        r'ASAP',
        r'inmediato',
        r'cr[íi]tico',
        r'emergencia',
        r'prioritario',
    ],
}

# Patrones para extraer datos
PATRON_OC = re.compile(r'(?:OC|C)?[- ]?(750384\d{6}|811117\d{6}|40[0-9]{11}|C\d{8,12})', re.IGNORECASE)
PATRON_TIENDA = re.compile(r'(?:tienda|T|TDA|sucursal)\s*[#:]?\s*(\d{3,5})', re.IGNORECASE)
PATRON_CANTIDAD = re.compile(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:unidades?|pzas?|piezas?|cajas?|uds?)', re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: RECEPTOR DE CORREOS
# ═══════════════════════════════════════════════════════════════

class EmailReceiver:
    """
    Receptor de correos IMAP para detección de conflictos externos.

    Permite conectar a un buzón de correo y buscar mensajes que
    contengan reportes de conflictos no detectados por el sistema.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el receptor de correos.

        Args:
            config: Diccionario con configuración IMAP:
                - imap_host: Servidor IMAP
                - imap_port: Puerto (default 993)
                - imap_user: Usuario
                - imap_password: Contraseña
                - carpeta_adjuntos: Ruta para guardar adjuntos
        """
        self.config = config or {}
        self.imap_host = self.config.get('imap_host', 'imap.office365.com')
        self.imap_port = self.config.get('imap_port', 993)
        self.imap_user = self.config.get('imap_user', '')
        self.imap_password = self.config.get('imap_password', '')
        self.carpeta_adjuntos = Path(self.config.get('carpeta_adjuntos', 'output/adjuntos'))

        # Crear carpeta de adjuntos si no existe
        self.carpeta_adjuntos.mkdir(parents=True, exist_ok=True)

        self.conexion: Optional[imaplib.IMAP4_SSL] = None
        self._conectado = False

        logger.info(f"📧 EmailReceiver inicializado para {self.imap_host}")

    def conectar(self) -> bool:
        """
        Establece conexión con el servidor IMAP.

        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            logger.info(f"📧 Conectando a {self.imap_host}:{self.imap_port}...")

            self.conexion = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            self.conexion.login(self.imap_user, self.imap_password)
            self._conectado = True

            logger.info(f"✅ Conexión IMAP establecida exitosamente")
            return True

        except imaplib.IMAP4.error as e:
            logger.error(f"❌ Error de autenticación IMAP: {e}")
            self._conectado = False
            return False
        except Exception as e:
            logger.error(f"❌ Error conectando a IMAP: {e}")
            self._conectado = False
            return False

    def desconectar(self):
        """Cierra la conexión IMAP"""
        if self.conexion and self._conectado:
            try:
                self.conexion.logout()
                logger.info("📧 Conexión IMAP cerrada")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión IMAP: {e}")
            finally:
                self._conectado = False
                self.conexion = None

    def __enter__(self):
        """Context manager - conectar"""
        self.conectar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - desconectar"""
        self.desconectar()

    def buscar_correos_conflicto(
        self,
        carpeta: str = 'INBOX',
        dias_atras: int = 7,
        solo_no_leidos: bool = True,
        palabras_clave: List[str] = None
    ) -> List[CorreoRecibido]:
        """
        Busca correos que contengan reportes de conflictos.

        Args:
            carpeta: Carpeta IMAP a revisar (default: INBOX)
            dias_atras: Cuántos días hacia atrás buscar
            solo_no_leidos: Si solo buscar no leídos
            palabras_clave: Lista adicional de palabras a buscar

        Returns:
            Lista de CorreoRecibido con potenciales conflictos
        """
        if not self._conectado:
            logger.error("❌ No hay conexión IMAP establecida")
            return []

        try:
            # Seleccionar carpeta
            self.conexion.select(carpeta)

            # Construir criterios de búsqueda
            fecha_desde = (datetime.now() - timedelta(days=dias_atras)).strftime('%d-%b-%Y')
            criterios = f'(SINCE {fecha_desde})'

            if solo_no_leidos:
                criterios = f'(UNSEEN SINCE {fecha_desde})'

            # Buscar mensajes
            _, mensajes = self.conexion.search(None, criterios)
            ids_mensajes = mensajes[0].split()

            logger.info(f"📧 Encontrados {len(ids_mensajes)} correos en {carpeta}")

            correos_conflicto = []

            for msg_id in ids_mensajes:
                correo = self._procesar_mensaje(msg_id)
                if correo and self._es_correo_conflicto(correo, palabras_clave):
                    correos_conflicto.append(correo)

            logger.info(f"🔍 {len(correos_conflicto)} correos con potenciales conflictos detectados")
            return correos_conflicto

        except Exception as e:
            logger.error(f"❌ Error buscando correos: {e}")
            return []

    def _procesar_mensaje(self, msg_id: bytes) -> Optional[CorreoRecibido]:
        """
        Procesa un mensaje de correo y extrae su información.

        Args:
            msg_id: ID del mensaje en el servidor

        Returns:
            CorreoRecibido con la información extraída
        """
        try:
            _, msg_data = self.conexion.fetch(msg_id, '(RFC822)')

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Extraer información básica
                    asunto = self._decodificar_header(msg['Subject'])
                    remitente = msg['From']
                    nombre_remitente, email_remitente = parseaddr(remitente)

                    # Fecha
                    fecha_str = msg['Date']
                    try:
                        fecha = parsedate_to_datetime(fecha_str)
                    except Exception:
                        fecha = datetime.now()

                    # Extraer cuerpo
                    cuerpo_texto, cuerpo_html = self._extraer_cuerpo(msg)

                    # Extraer adjuntos
                    adjuntos = self._extraer_adjuntos(msg)

                    correo = CorreoRecibido(
                        id_mensaje=msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                        fecha_recepcion=fecha,
                        remitente_email=email_remitente,
                        remitente_nombre=self._decodificar_header(nombre_remitente),
                        asunto=asunto,
                        cuerpo_texto=cuerpo_texto,
                        cuerpo_html=cuerpo_html,
                        adjuntos=adjuntos
                    )

                    # Análisis inicial
                    self._analizar_correo(correo)

                    return correo

            return None

        except Exception as e:
            logger.error(f"❌ Error procesando mensaje {msg_id}: {e}")
            return None

    def _decodificar_header(self, header: str) -> str:
        """Decodifica un header de correo"""
        if not header:
            return ""

        decoded_parts = decode_header(header)
        result = []

        for content, charset in decoded_parts:
            if isinstance(content, bytes):
                charset = charset or 'utf-8'
                try:
                    result.append(content.decode(charset))
                except Exception:
                    result.append(content.decode('utf-8', errors='replace'))
            else:
                result.append(content)

        return ' '.join(result)

    def _extraer_cuerpo(self, msg: email.message.Message) -> Tuple[str, Optional[str]]:
        """
        Extrae el cuerpo del correo (texto plano y HTML).

        Returns:
            Tupla (texto_plano, html)
        """
        texto = ""
        html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignorar adjuntos
                if "attachment" in content_disposition:
                    continue

                try:
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or 'utf-8'
                        body_decoded = body.decode(charset, errors='replace')

                        if content_type == "text/plain":
                            texto = body_decoded
                        elif content_type == "text/html":
                            html = body_decoded
                except Exception:
                    continue
        else:
            # Mensaje no multipart
            try:
                body = msg.get_payload(decode=True)
                if body:
                    charset = msg.get_content_charset() or 'utf-8'
                    texto = body.decode(charset, errors='replace')
            except Exception:
                pass

        return texto, html

    def _extraer_adjuntos(self, msg: email.message.Message) -> List[AdjuntoCorreo]:
        """
        Extrae los archivos adjuntos del correo.

        Returns:
            Lista de AdjuntoCorreo
        """
        adjuntos = []

        if not msg.is_multipart():
            return adjuntos

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = self._decodificar_header(filename)

                    try:
                        contenido = part.get_payload(decode=True)
                        if contenido:
                            adjunto = AdjuntoCorreo(
                                nombre=filename,
                                contenido=contenido,
                                tipo_mime=part.get_content_type(),
                                tamaño=len(contenido)
                            )

                            # Guardar si es Excel
                            if filename.lower().endswith(('.xlsx', '.xls')):
                                ruta = self._guardar_adjunto(adjunto)
                                adjunto.ruta_guardado = ruta

                            adjuntos.append(adjunto)
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo adjunto {filename}: {e}")

        return adjuntos

    def _guardar_adjunto(self, adjunto: AdjuntoCorreo) -> Optional[str]:
        """
        Guarda un adjunto en disco.

        Returns:
            Ruta donde se guardó el archivo
        """
        try:
            # Generar nombre único
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_seguro = re.sub(r'[^\w\-_\.]', '_', adjunto.nombre)
            nombre_archivo = f"{timestamp}_{nombre_seguro}"

            ruta_completa = self.carpeta_adjuntos / nombre_archivo

            with open(ruta_completa, 'wb') as f:
                f.write(adjunto.contenido)

            logger.info(f"📎 Adjunto guardado: {ruta_completa}")
            return str(ruta_completa)

        except Exception as e:
            logger.error(f"❌ Error guardando adjunto: {e}")
            return None

    def _analizar_correo(self, correo: CorreoRecibido):
        """
        Realiza un análisis inicial del correo para detectar tipo de conflicto.

        Modifica el objeto correo in-place.
        """
        texto_busqueda = f"{correo.asunto} {correo.cuerpo_texto}".lower()

        # Detectar tipo de conflicto
        conflictos_encontrados = []
        palabras_clave = []

        for tipo_conflicto, patrones in PATRONES_CONFLICTO.items():
            for patron in patrones:
                if re.search(patron, texto_busqueda, re.IGNORECASE):
                    conflictos_encontrados.append(tipo_conflicto)
                    palabras_clave.append(patron)
                    break  # Solo contamos una vez por tipo

        # Asignar tipo principal (el más específico o crítico)
        if conflictos_encontrados:
            # Priorizar por criticidad
            prioridad = [
                TipoConflictoCorreo.DISTRIBUCION_EXCEDENTE,
                TipoConflictoCorreo.DISTRIBUCION_INCOMPLETA,
                TipoConflictoCorreo.OC_VENCIDA,
                TipoConflictoCorreo.PROBLEMA_EXPEDICION,
                TipoConflictoCorreo.PROBLEMA_CARGADO,
                TipoConflictoCorreo.PROBLEMA_PREPARADO,
                TipoConflictoCorreo.PROBLEMA_RECIBO,
            ]

            for tipo in prioridad:
                if tipo in conflictos_encontrados:
                    correo.tipo_conflicto_detectado = tipo
                    break

            if not correo.tipo_conflicto_detectado:
                correo.tipo_conflicto_detectado = conflictos_encontrados[0]

        # Determinar severidad
        if TipoConflictoCorreo.URGENTE in conflictos_encontrados:
            correo.severidad_detectada = SeveridadConflicto.CRITICO
        elif correo.tipo_conflicto_detectado in [
            TipoConflictoCorreo.DISTRIBUCION_EXCEDENTE,
            TipoConflictoCorreo.PROBLEMA_EXPEDICION
        ]:
            correo.severidad_detectada = SeveridadConflicto.CRITICO
        elif correo.tipo_conflicto_detectado in [
            TipoConflictoCorreo.DISTRIBUCION_INCOMPLETA,
            TipoConflictoCorreo.OC_VENCIDA
        ]:
            correo.severidad_detectada = SeveridadConflicto.ALTO
        elif correo.tipo_conflicto_detectado:
            correo.severidad_detectada = SeveridadConflicto.MEDIO
        else:
            correo.severidad_detectada = SeveridadConflicto.BAJO

        correo.palabras_clave_encontradas = palabras_clave

        # Extraer datos mencionados
        texto_completo = f"{correo.asunto} {correo.cuerpo_texto}"

        # OCs
        ocs = PATRON_OC.findall(texto_completo)
        correo.oc_numeros = list(set(ocs))

        # Tiendas
        tiendas = PATRON_TIENDA.findall(texto_completo)
        correo.tiendas_mencionadas = list(set(tiendas))

        # Cantidades
        cantidades = PATRON_CANTIDAD.findall(texto_completo)
        correo.cantidades_mencionadas = [
            float(c.replace(',', '')) for c in cantidades
        ]

    def _es_correo_conflicto(
        self,
        correo: CorreoRecibido,
        palabras_clave_adicionales: List[str] = None
    ) -> bool:
        """
        Determina si un correo contiene un reporte de conflicto.

        Args:
            correo: Correo a evaluar
            palabras_clave_adicionales: Palabras adicionales a buscar

        Returns:
            True si el correo parece contener un conflicto
        """
        # Si ya detectamos un tipo de conflicto, es un correo de conflicto
        if correo.tipo_conflicto_detectado and correo.tipo_conflicto_detectado != TipoConflictoCorreo.OTRO:
            return True

        # Verificar palabras clave adicionales
        if palabras_clave_adicionales:
            texto = f"{correo.asunto} {correo.cuerpo_texto}".lower()
            for palabra in palabras_clave_adicionales:
                if palabra.lower() in texto:
                    correo.tipo_conflicto_detectado = TipoConflictoCorreo.OTRO
                    correo.palabras_clave_encontradas.append(palabra)
                    return True

        # Verificar si tiene adjuntos Excel (posible reporte)
        tiene_excel = any(
            adj.nombre.lower().endswith(('.xlsx', '.xls'))
            for adj in correo.adjuntos
        )

        # Si tiene Excel y menciona OC o tienda, probablemente es conflicto
        if tiene_excel and (correo.oc_numeros or correo.tiendas_mencionadas):
            correo.tipo_conflicto_detectado = TipoConflictoCorreo.OTRO
            return True

        return False

    def marcar_como_leido(self, correo: CorreoRecibido) -> bool:
        """
        Marca un correo como leído en el servidor.

        Args:
            correo: Correo a marcar

        Returns:
            True si se marcó exitosamente
        """
        if not self._conectado:
            return False

        try:
            self.conexion.store(correo.id_mensaje.encode(), '+FLAGS', '\\Seen')
            logger.info(f"📧 Correo {correo.id_mensaje} marcado como leído")
            return True
        except Exception as e:
            logger.error(f"❌ Error marcando correo como leído: {e}")
            return False

    def obtener_estadisticas(self, carpeta: str = 'INBOX') -> Dict[str, Any]:
        """
        Obtiene estadísticas del buzón.

        Returns:
            Diccionario con estadísticas
        """
        if not self._conectado:
            return {'error': 'No conectado'}

        try:
            self.conexion.select(carpeta)

            # Total de mensajes
            _, total = self.conexion.search(None, 'ALL')
            total_count = len(total[0].split()) if total[0] else 0

            # No leídos
            _, unread = self.conexion.search(None, 'UNSEEN')
            unread_count = len(unread[0].split()) if unread[0] else 0

            return {
                'carpeta': carpeta,
                'total_mensajes': total_count,
                'no_leidos': unread_count,
                'leidos': total_count - unread_count,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {'error': str(e)}


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════

def crear_receptor_desde_config() -> EmailReceiver:
    """
    Crea un EmailReceiver usando la configuración del sistema.

    Returns:
        EmailReceiver configurado
    """
    from config import IMAP_CONFIG

    return EmailReceiver(config=IMAP_CONFIG)


def buscar_conflictos_pendientes(
    dias: int = 7,
    solo_no_leidos: bool = True
) -> List[CorreoRecibido]:
    """
    Función de conveniencia para buscar conflictos pendientes.

    Args:
        dias: Días hacia atrás a buscar
        solo_no_leidos: Si solo buscar no leídos

    Returns:
        Lista de correos con conflictos
    """
    try:
        receiver = crear_receptor_desde_config()

        with receiver:
            return receiver.buscar_correos_conflicto(
                dias_atras=dias,
                solo_no_leidos=solo_no_leidos
            )
    except Exception as e:
        logger.error(f"❌ Error buscando conflictos: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configuración de ejemplo
    config_ejemplo = {
        'imap_host': 'imap.office365.com',
        'imap_port': 993,
        'imap_user': 'tu_email@chedraui.com.mx',
        'imap_password': 'tu_password',
        'carpeta_adjuntos': 'output/adjuntos'
    }

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  📧 RECEPTOR DE CORREOS - DETECCIÓN DE CONFLICTOS             ║
    ║  Sistema SAC - CEDIS Cancún 427                               ║
    ╚═══════════════════════════════════════════════════════════════╝

    Este módulo permite recibir y analizar correos electrónicos
    para detectar conflictos reportados externamente.

    Uso:
        from modules.email.email_receiver import EmailReceiver

        receiver = EmailReceiver(config)
        with receiver:
            conflictos = receiver.buscar_correos_conflicto(dias_atras=7)
            for correo in conflictos:
                print(f"Conflicto: {correo.tipo_conflicto_detectado}")
                print(f"OCs: {correo.oc_numeros}")
    """)
