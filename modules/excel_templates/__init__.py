"""
Excel Templates Module - Sistema SAC
====================================

Templates corporativos Chedraui para reportes Excel.

Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
"""

from .base_template import ExcelTemplate
from .report_templates import (
    OCValidationTemplate,
    DailyPlanningTemplate,
    DistributionTemplate,
    ErrorReportTemplate,
    ASNStatusTemplate,
    InventoryTemplate,
    AuditTemplate,
    KPITemplate,
    ComparativeTemplate,
    ExecutiveDashboardTemplate,
)

__all__ = [
    'ExcelTemplate',
    'OCValidationTemplate',
    'DailyPlanningTemplate',
    'DistributionTemplate',
    'ErrorReportTemplate',
    'ASNStatusTemplate',
    'InventoryTemplate',
    'AuditTemplate',
    'KPITemplate',
    'ComparativeTemplate',
    'ExecutiveDashboardTemplate',
]
