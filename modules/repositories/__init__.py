"""
Repositorios para acceso a datos - SAC CEDIS 427
=================================================

Este paquete implementa el patron Repository para acceso
estructurado a las entidades de Manhattan WMS.

Repositorios disponibles:
- BaseRepository: Clase base con operaciones CRUD genericas
- OCRepository: Ordenes de Compra
- DistributionRepository: Distribuciones
- ASNRepository: Advanced Shipping Notices

Uso:
    from modules.repositories import OCRepository, DistributionRepository

    # Crear repositorio
    oc_repo = OCRepository()

    # Buscar OC
    df = oc_repo.find_by_oc_number('C750384123456')

    # Obtener OCs pendientes
    df_pending = oc_repo.find_pending_ocs()

Autor: Julian Alexander Juarez Alvarado (ADMJAJA)
Cargo: Jefe de Sistemas - CEDIS Cancun 427
"""

from .base_repository import BaseRepository
from .oc_repository import OCRepository
from .distribution_repository import DistributionRepository
from .asn_repository import ASNRepository

__all__ = [
    'BaseRepository',
    'OCRepository',
    'DistributionRepository',
    'ASNRepository',
]
