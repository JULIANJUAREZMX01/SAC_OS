"""
═══════════════════════════════════════════════════════════════
VALIDADOR DE ENTRADA DE USUARIO
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Módulo para validación robusta de entrada del usuario
previene errores, SQL injection y datos malformados.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import re
import logging
from typing import Optional, List, Tuple
from email.utils import parseaddr

logger = logging.getLogger(__name__)


class ErrorValidacion(Exception):
    """Excepción base para errores de validación"""
    pass


class ValidadorEntrada:
    """Validador de entrada de usuario con métodos específicos por tipo"""

    # Patrones válidos
    PATRON_OC = r'^C\d{6}$|^750384\d{6}$|^811117\d{6}$|^40[0-9]{11}$'
    PATRON_LPN = r'^LPN[0-9]{7,10}$'
    PATRON_ASN = r'^ASN[0-9]{8,12}$'
    PATRON_SKU = r'^[A-Z0-9]{8,12}$'
    PATRON_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    @staticmethod
    def validar_oc(oc_numero: str, permitir_prefijos: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Valida formato de número de OC.

        Args:
            oc_numero: Número de OC a validar
            permitir_prefijos: Si se permiten prefijos como 'C'

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_limpio, mensaje_error)
        """
        if not oc_numero:
            return False, "", "OC no puede estar vacío"

        oc_limpio = str(oc_numero).strip().upper()

        # Validar longitud
        if len(oc_limpio) < 7 or len(oc_limpio) > 20:
            return False, oc_limpio, f"OC debe tener 7-20 caracteres, got {len(oc_limpio)}"

        # Validar que solo contiene alfanuméricos
        if not re.match(r'^[A-Z0-9]+$', oc_limpio):
            return False, oc_limpio, "OC debe contener solo letras (A-Z) y números (0-9)"

        # Validar contra patrones conocidos
        patrones = [
            ('Patrón C######', r'^C\d{6}$'),
            ('Patrón 750384#####', r'^750384\d{6}$'),
            ('Patrón 811117#####', r'^811117\d{6}$'),
            ('Patrón 40###########', r'^40[0-9]{11}$'),
        ]

        valido = False
        patron_match = None
        for nombre_patron, patron in patrones:
            if re.match(patron, oc_limpio):
                valido = True
                patron_match = nombre_patron
                break

        if not valido:
            return False, oc_limpio, (
                f"OC '{oc_limpio}' no coincide con patrones conocidos. "
                f"Patrones válidos: {', '.join([p[0] for p in patrones])}"
            )

        logger.info(f"✅ OC '{oc_limpio}' validado - {patron_match}")
        return True, oc_limpio, None

    @staticmethod
    def validar_email(email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida formato de dirección email.

        Args:
            email: Dirección email a validar

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_limpio, mensaje_error)
        """
        if not email:
            return False, "", "Email no puede estar vacío"

        email_limpio = str(email).strip().lower()

        # Validar formato básico
        if len(email_limpio) > 254:
            return False, email_limpio, "Email no puede exceder 254 caracteres"

        if not re.match(ValidadorEntrada.PATRON_EMAIL, email_limpio):
            return False, email_limpio, f"Formato de email inválido: '{email_limpio}'"

        # Usar parseaddr para validación adicional
        nombre, direccion = parseaddr(email_limpio)
        if direccion != email_limpio:
            return False, email_limpio, f"Email contiene caracteres inválidos"

        logger.info(f"✅ Email '{email_limpio}' validado")
        return True, email_limpio, None

    @staticmethod
    def validar_emails_multiples(emails: str, separador: str = ',') -> Tuple[List[str], List[str]]:
        """
        Valida lista de emails separados por coma.

        Args:
            emails: String con emails separados
            separador: Carácter separador (default ',')

        Returns:
            Tuple[List[str], List[str]]: (emails_validos, emails_invalidos_con_motivo)
        """
        if not emails or not str(emails).strip():
            return [], ["La lista de emails no puede estar vacía"]

        emails_str = str(emails)
        items = [e.strip() for e in emails_str.split(separador) if e.strip()]

        validos = []
        invalidos = []

        for email in items:
            es_valido, email_limpio, error = ValidadorEntrada.validar_email(email)
            if es_valido:
                if email_limpio not in validos:  # Evitar duplicados
                    validos.append(email_limpio)
            else:
                invalidos.append(f"'{email}': {error}")

        return validos, invalidos

    @staticmethod
    def validar_lpn(lpn_numero: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida formato de número LPN.

        Args:
            lpn_numero: Número LPN a validar

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_limpio, mensaje_error)
        """
        if not lpn_numero:
            return False, "", "LPN no puede estar vacío"

        lpn_limpio = str(lpn_numero).strip().upper()

        if not re.match(ValidadorEntrada.PATRON_LPN, lpn_limpio):
            return False, lpn_limpio, (
                f"LPN '{lpn_limpio}' inválido. Formato: LPN[7-10 dígitos]"
            )

        logger.info(f"✅ LPN '{lpn_limpio}' validado")
        return True, lpn_limpio, None

    @staticmethod
    def validar_asn(asn_numero: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida formato de número ASN.

        Args:
            asn_numero: Número ASN a validar

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_limpio, mensaje_error)
        """
        if not asn_numero:
            return False, "", "ASN no puede estar vacío"

        asn_limpio = str(asn_numero).strip().upper()

        if not re.match(ValidadorEntrada.PATRON_ASN, asn_limpio):
            return False, asn_limpio, (
                f"ASN '{asn_limpio}' inválido. Formato: ASN[8-12 dígitos]"
            )

        logger.info(f"✅ ASN '{asn_limpio}' validado")
        return True, asn_limpio, None

    @staticmethod
    def validar_cantidad(cantidad: str, minimo: int = 1, maximo: int = 999999999) -> Tuple[bool, int, Optional[str]]:
        """
        Valida cantidad numérica.

        Args:
            cantidad: Cantidad a validar
            minimo: Valor mínimo permitido
            maximo: Valor máximo permitido

        Returns:
            Tuple[bool, int, Optional[str]]: (es_valido, valor, mensaje_error)
        """
        if not cantidad or not str(cantidad).strip():
            return False, 0, "Cantidad no puede estar vacía"

        try:
            valor = int(str(cantidad).strip())

            if valor < minimo:
                return False, valor, f"Cantidad debe ser >= {minimo}"

            if valor > maximo:
                return False, valor, f"Cantidad debe ser <= {maximo}"

            logger.info(f"✅ Cantidad '{valor}' validada")
            return True, valor, None

        except ValueError:
            return False, 0, f"'{cantidad}' no es un número entero válido"

    @staticmethod
    def validar_sku(sku: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida formato de SKU.

        Args:
            sku: SKU a validar

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_limpio, mensaje_error)
        """
        if not sku:
            return False, "", "SKU no puede estar vacío"

        sku_limpio = str(sku).strip().upper()

        if not re.match(ValidadorEntrada.PATRON_SKU, sku_limpio):
            return False, sku_limpio, (
                f"SKU '{sku_limpio}' inválido. Debe tener 8-12 caracteres alfanuméricos"
            )

        logger.info(f"✅ SKU '{sku_limpio}' validado")
        return True, sku_limpio, None

    @staticmethod
    def sanitizar_nombre(nombre: str, max_largo: int = 100) -> Tuple[bool, str, Optional[str]]:
        """
        Sanitiza nombre de persona o archivo.

        Args:
            nombre: Nombre a sanitizar
            max_largo: Largo máximo permitido

        Returns:
            Tuple[bool, str, Optional[str]]: (es_valido, valor_sanitizado, mensaje_error)
        """
        if not nombre or not str(nombre).strip():
            return False, "", "Nombre no puede estar vacío"

        nombre_limpio = str(nombre).strip()

        if len(nombre_limpio) > max_largo:
            return False, nombre_limpio, f"Nombre no puede exceder {max_largo} caracteres"

        # Permitir letras, números, espacios y guiones
        if not re.match(r'^[a-zA-Z0-9\s\-\.áéíóúñÁÉÍÓÚÑ]+$', nombre_limpio):
            return False, nombre_limpio, "Nombre contiene caracteres no permitidos"

        logger.info(f"✅ Nombre '{nombre_limpio}' sanitizado")
        return True, nombre_limpio, None

    @staticmethod
    def detectar_sql_injection(valor: str) -> Tuple[bool, Optional[str]]:
        """
        Detecta patrones comunes de SQL injection.

        Args:
            valor: Valor a verificar

        Returns:
            Tuple[bool, Optional[str]]: (es_seguro, motivo_si_no_es_seguro)
        """
        if not valor:
            return True, None

        valor_lower = str(valor).lower()

        # Patrones de SQL injection comunes
        patrones_peligrosos = [
            r"'\s*or\s*'",           # ' or '
            r"'\s*or\s*1\s*=\s*1",   # ' or 1=1
            r"union\s+select",       # UNION SELECT
            r"drop\s+table",         # DROP TABLE
            r"insert\s+into",        # INSERT INTO
            r"delete\s+from",        # DELETE FROM
            r"update\s+\w+\s+set",   # UPDATE ... SET
            r"--\s*$",               # Comentario SQL --
            r";\s*drop",             # ; DROP
            r"xp_",                  # Extended stored proc
            r"sp_",                  # System stored proc
        ]

        for patron in patrones_peligrosos:
            if re.search(patron, valor_lower):
                return False, f"Valor contiene patrón sospechoso: {patron}"

        return True, None
