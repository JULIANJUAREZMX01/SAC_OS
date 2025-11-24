"""
═══════════════════════════════════════════════════════════════
GESTOR DE DESTINATARIOS
Sistema de Automatización de Consultas - CEDIS Cancún 427
═══════════════════════════════════════════════════════════════

Sistema de gestión de destinatarios de correo con categorías,
listas de distribución y validación de emails.

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
═══════════════════════════════════════════════════════════════
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ENUMERACIONES
# ═══════════════════════════════════════════════════════════════

class RecipientCategory(Enum):
    """Categorías de destinatarios"""
    CRITICAL = "CRITICO"           # Alertas críticas
    OPERATIONS = "OPERACIONES"     # Operaciones diarias
    PLANNING = "PLANNING"          # Equipo de planning
    MANAGEMENT = "GERENCIA"        # Gerencia/Supervisión
    SYSTEMS = "SISTEMAS"           # Equipo de sistemas
    ALL = "TODOS"                  # Todos los destinatarios
    DAILY_REPORT = "REPORTE_DIARIO"
    WEEKLY_REPORT = "REPORTE_SEMANAL"
    ALERTS = "ALERTAS"
    NOTIFICATIONS = "NOTIFICACIONES"


# ═══════════════════════════════════════════════════════════════
# CLASE RECIPIENT
# ═══════════════════════════════════════════════════════════════

@dataclass
class Recipient:
    """
    Representa un destinatario de correo

    Attributes:
        email: Dirección de correo
        name: Nombre del destinatario
        categories: Categorías a las que pertenece
        enabled: Si está habilitado para recibir correos
        added_at: Fecha de registro
        last_sent: Última vez que recibió un correo
        metadata: Datos adicionales
    """
    email: str
    name: str = ""
    categories: Set[RecipientCategory] = field(default_factory=set)
    enabled: bool = True
    added_at: datetime = field(default_factory=datetime.now)
    last_sent: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Normaliza el email"""
        self.email = self.email.strip().lower()
        if isinstance(self.categories, list):
            self.categories = set(self.categories)

    def has_category(self, category: RecipientCategory) -> bool:
        """Verifica si pertenece a una categoría"""
        return category in self.categories or RecipientCategory.ALL in self.categories

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'email': self.email,
            'name': self.name,
            'categories': [c.value for c in self.categories],
            'enabled': self.enabled,
            'added_at': self.added_at.isoformat(),
            'last_sent': self.last_sent.isoformat() if self.last_sent else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Recipient':
        """Crea desde diccionario"""
        categories = {RecipientCategory(c) for c in data.get('categories', [])}
        return cls(
            email=data['email'],
            name=data.get('name', ''),
            categories=categories,
            enabled=data.get('enabled', True),
            metadata=data.get('metadata', {})
        )


# ═══════════════════════════════════════════════════════════════
# CLASE DISTRIBUTION LIST
# ═══════════════════════════════════════════════════════════════

@dataclass
class DistributionList:
    """
    Lista de distribución de correo

    Attributes:
        name: Nombre de la lista
        description: Descripción de la lista
        emails: Lista de correos
        enabled: Si está habilitada
    """
    name: str
    description: str = ""
    emails: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'name': self.name,
            'description': self.description,
            'emails': self.emails,
            'enabled': self.enabled
        }


# ═══════════════════════════════════════════════════════════════
# CLASE RECIPIENTS MANAGER
# ═══════════════════════════════════════════════════════════════

class RecipientsManager:
    """
    Gestor de destinatarios de correo electrónico

    Características:
    - Gestión de destinatarios por categoría
    - Listas de distribución
    - Validación de emails
    - Persistencia en archivo JSON
    - Búsqueda y filtrado

    Ejemplo:
        manager = RecipientsManager()

        # Agregar destinatario
        manager.add_recipient(
            "usuario@chedraui.com.mx",
            categories=[RecipientCategory.PLANNING, RecipientCategory.DAILY_REPORT]
        )

        # Obtener destinatarios de una categoría
        planning_emails = manager.get_recipients(RecipientCategory.PLANNING)
    """

    def __init__(self, config_file: str = None):
        """
        Inicializa el gestor de destinatarios

        Args:
            config_file: Archivo JSON de configuración
        """
        self._recipients: Dict[str, Recipient] = {}
        self._distribution_lists: Dict[str, DistributionList] = {}
        self._config_file = Path(config_file) if config_file else None

        # Cargar configuración si existe
        if self._config_file and self._config_file.exists():
            self._load_config()
        else:
            self._init_defaults()

        logger.info(f"📧 RecipientsManager inicializado con {len(self._recipients)} destinatarios")

    def _init_defaults(self):
        """Inicializa destinatarios por defecto"""
        # Categorías predefinidas vacías
        self._distribution_lists = {
            'planning': DistributionList(
                name='planning',
                description='Equipo de Planning CEDIS'
            ),
            'sistemas': DistributionList(
                name='sistemas',
                description='Equipo de Sistemas'
            ),
            'gerencia': DistributionList(
                name='gerencia',
                description='Gerencia y Supervisión'
            ),
            'operaciones': DistributionList(
                name='operaciones',
                description='Operaciones del almacén'
            ),
            'alertas_criticas': DistributionList(
                name='alertas_criticas',
                description='Destinatarios de alertas críticas'
            )
        }

    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN DE DESTINATARIOS
    # ═══════════════════════════════════════════════════════════════

    def add_recipient(self, email: str, name: str = "",
                      categories: List[RecipientCategory] = None,
                      metadata: Dict = None) -> bool:
        """
        Agrega un nuevo destinatario

        Args:
            email: Dirección de correo
            name: Nombre del destinatario
            categories: Categorías a las que pertenece
            metadata: Datos adicionales

        Returns:
            bool: True si se agregó correctamente
        """
        if not self.validate_email(email):
            logger.error(f"❌ Email inválido: {email}")
            return False

        email = email.strip().lower()

        if email in self._recipients:
            logger.warning(f"⚠️ El destinatario ya existe: {email}")
            # Actualizar categorías existentes
            if categories:
                self._recipients[email].categories.update(categories)
            return True

        recipient = Recipient(
            email=email,
            name=name,
            categories=set(categories) if categories else set(),
            metadata=metadata or {}
        )

        self._recipients[email] = recipient
        self._save_config()

        logger.info(f"✅ Destinatario agregado: {email}")
        return True

    def remove_recipient(self, email: str) -> bool:
        """
        Elimina un destinatario

        Args:
            email: Dirección de correo

        Returns:
            bool: True si se eliminó
        """
        email = email.strip().lower()

        if email not in self._recipients:
            logger.warning(f"⚠️ Destinatario no encontrado: {email}")
            return False

        del self._recipients[email]
        self._save_config()

        logger.info(f"🗑️ Destinatario eliminado: {email}")
        return True

    def get_recipient(self, email: str) -> Optional[Recipient]:
        """Obtiene un destinatario por email"""
        return self._recipients.get(email.strip().lower())

    def update_recipient(self, email: str, **kwargs) -> bool:
        """
        Actualiza datos de un destinatario

        Args:
            email: Dirección de correo
            **kwargs: Campos a actualizar (name, categories, enabled, metadata)

        Returns:
            bool: True si se actualizó
        """
        email = email.strip().lower()

        if email not in self._recipients:
            return False

        recipient = self._recipients[email]

        if 'name' in kwargs:
            recipient.name = kwargs['name']
        if 'categories' in kwargs:
            recipient.categories = set(kwargs['categories'])
        if 'enabled' in kwargs:
            recipient.enabled = kwargs['enabled']
        if 'metadata' in kwargs:
            recipient.metadata.update(kwargs['metadata'])

        self._save_config()
        return True

    # ═══════════════════════════════════════════════════════════════
    # CONSULTAS
    # ═══════════════════════════════════════════════════════════════

    def get_recipients(self, category: RecipientCategory = None) -> List[str]:
        """
        Obtiene lista de correos por categoría

        Args:
            category: Categoría a filtrar (None = todos)

        Returns:
            List[str]: Lista de direcciones de correo
        """
        emails = []

        for recipient in self._recipients.values():
            if not recipient.enabled:
                continue

            if category is None or recipient.has_category(category):
                emails.append(recipient.email)

        return sorted(set(emails))

    def get_recipients_details(self, category: RecipientCategory = None) -> List[Dict]:
        """
        Obtiene detalles de destinatarios por categoría

        Args:
            category: Categoría a filtrar

        Returns:
            List[Dict]: Lista de datos de destinatarios
        """
        results = []

        for recipient in self._recipients.values():
            if category is None or recipient.has_category(category):
                results.append(recipient.to_dict())

        return results

    def get_all_emails(self, include_disabled: bool = False) -> List[str]:
        """Obtiene todos los correos"""
        emails = []
        for r in self._recipients.values():
            if include_disabled or r.enabled:
                emails.append(r.email)
        return sorted(emails)

    def get_categories_for_email(self, email: str) -> List[RecipientCategory]:
        """Obtiene las categorías de un email"""
        email = email.strip().lower()
        recipient = self._recipients.get(email)
        if recipient:
            return list(recipient.categories)
        return []

    # ═══════════════════════════════════════════════════════════════
    # LISTAS DE DISTRIBUCIÓN
    # ═══════════════════════════════════════════════════════════════

    def get_distribution_list(self, name: str) -> List[str]:
        """
        Obtiene una lista de distribución

        Args:
            name: Nombre de la lista

        Returns:
            List[str]: Lista de correos
        """
        dist_list = self._distribution_lists.get(name.lower())
        if dist_list and dist_list.enabled:
            return dist_list.emails
        return []

    def create_distribution_list(self, name: str, description: str = "",
                                 emails: List[str] = None) -> bool:
        """
        Crea una nueva lista de distribución

        Args:
            name: Nombre de la lista
            description: Descripción
            emails: Lista inicial de correos

        Returns:
            bool: True si se creó
        """
        name = name.lower()

        if name in self._distribution_lists:
            logger.warning(f"⚠️ La lista ya existe: {name}")
            return False

        # Validar emails
        valid_emails = [e for e in (emails or []) if self.validate_email(e)]

        self._distribution_lists[name] = DistributionList(
            name=name,
            description=description,
            emails=valid_emails
        )

        self._save_config()
        logger.info(f"✅ Lista de distribución creada: {name}")
        return True

    def add_to_distribution_list(self, list_name: str, email: str) -> bool:
        """Agrega un email a una lista de distribución"""
        list_name = list_name.lower()

        if list_name not in self._distribution_lists:
            return False

        if not self.validate_email(email):
            return False

        email = email.strip().lower()
        if email not in self._distribution_lists[list_name].emails:
            self._distribution_lists[list_name].emails.append(email)
            self._save_config()

        return True

    def remove_from_distribution_list(self, list_name: str, email: str) -> bool:
        """Elimina un email de una lista de distribución"""
        list_name = list_name.lower()
        email = email.strip().lower()

        if list_name not in self._distribution_lists:
            return False

        if email in self._distribution_lists[list_name].emails:
            self._distribution_lists[list_name].emails.remove(email)
            self._save_config()
            return True

        return False

    def list_distribution_lists(self) -> List[str]:
        """Lista todas las listas de distribución"""
        return list(self._distribution_lists.keys())

    # ═══════════════════════════════════════════════════════════════
    # VALIDACIÓN
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida el formato de un email

        Args:
            email: Dirección a validar

        Returns:
            bool: True si es válido
        """
        if not email:
            return False

        # Patrón básico de validación de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def validate_recipients_list(self, emails: List[str]) -> tuple:
        """
        Valida una lista de correos

        Args:
            emails: Lista de correos a validar

        Returns:
            tuple: (válidos, inválidos)
        """
        valid = []
        invalid = []

        for email in emails:
            if self.validate_email(email):
                valid.append(email.strip().lower())
            else:
                invalid.append(email)

        return valid, invalid

    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════

    def _save_config(self):
        """Guarda la configuración en archivo"""
        if not self._config_file:
            return

        try:
            data = {
                'recipients': {
                    email: r.to_dict() for email, r in self._recipients.items()
                },
                'distribution_lists': {
                    name: dl.to_dict() for name, dl in self._distribution_lists.items()
                },
                'updated_at': datetime.now().isoformat()
            }

            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            self._config_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")

    def _load_config(self):
        """Carga la configuración desde archivo"""
        if not self._config_file or not self._config_file.exists():
            return

        try:
            data = json.loads(self._config_file.read_text(encoding='utf-8'))

            # Cargar destinatarios
            for email, rdata in data.get('recipients', {}).items():
                self._recipients[email] = Recipient.from_dict(rdata)

            # Cargar listas de distribución
            for name, dldata in data.get('distribution_lists', {}).items():
                self._distribution_lists[name] = DistributionList(
                    name=dldata['name'],
                    description=dldata.get('description', ''),
                    emails=dldata.get('emails', []),
                    enabled=dldata.get('enabled', True)
                )

            logger.info(f"📂 Configuración cargada: {len(self._recipients)} destinatarios")
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")

    def export_config(self, file_path: str) -> bool:
        """Exporta la configuración a un archivo"""
        try:
            original = self._config_file
            self._config_file = Path(file_path)
            self._save_config()
            self._config_file = original
            logger.info(f"✅ Configuración exportada a: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error exportando: {e}")
            return False

    def import_config(self, file_path: str) -> bool:
        """Importa configuración desde un archivo"""
        try:
            original = self._config_file
            self._config_file = Path(file_path)
            self._load_config()
            self._config_file = original
            self._save_config()  # Guardar en archivo original
            logger.info(f"✅ Configuración importada desde: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error importando: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de destinatarios"""
        enabled = sum(1 for r in self._recipients.values() if r.enabled)
        disabled = len(self._recipients) - enabled

        by_category = {}
        for cat in RecipientCategory:
            count = len(self.get_recipients(cat))
            if count > 0:
                by_category[cat.value] = count

        return {
            'total_recipients': len(self._recipients),
            'enabled': enabled,
            'disabled': disabled,
            'by_category': by_category,
            'distribution_lists': len(self._distribution_lists)
        }


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    GESTOR DE DESTINATARIOS - CHEDRAUI CEDIS
    ═══════════════════════════════════════════════════════════════
    """)

    manager = RecipientsManager()

    # Agregar destinatarios de ejemplo
    manager.add_recipient(
        "planning@chedraui.com.mx",
        name="Equipo Planning",
        categories=[RecipientCategory.PLANNING, RecipientCategory.DAILY_REPORT]
    )

    manager.add_recipient(
        "sistemas@chedraui.com.mx",
        name="Equipo Sistemas",
        categories=[RecipientCategory.SYSTEMS, RecipientCategory.CRITICAL]
    )

    # Mostrar estadísticas
    stats = manager.get_stats()
    print(f"\n📊 Estadísticas:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Obtener destinatarios de Planning
    planning = manager.get_recipients(RecipientCategory.PLANNING)
    print(f"\n📧 Destinatarios Planning: {planning}")
