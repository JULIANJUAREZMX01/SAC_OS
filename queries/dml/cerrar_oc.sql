-- ============================================
-- NOMBRE: Cerrar Orden de Compra
-- CATEGORÍA: DML - Corrección
-- TIPO: UPDATE
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-22
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Cierra una OC cambiando su status a '5' (Cerrada).
-- Usado cuando la OC ya fue procesada pero quedó abierta.
--
-- CASOS DE USO:
-- - OC completamente recibida pero no cerrada automáticamente
-- - Cierre manual solicitado por analista
-- - Limpieza de OCs antiguas
--
-- PARÁMETROS:
-- {{orderkey}} - Número de OC a cerrar
-- {{usuario}} - Usuario que realiza el cambio
-- {{motivo}} - Motivo del cierre (para notas)
--
-- TABLAS AFECTADAS:
-- - ORDERS (UPDATE)
--
-- STATUS VÁLIDOS EN MANHATTAN:
-- '0' = Abierta
-- '1' = En Proceso
-- '2' = Parcial
-- '5' = Cerrada
-- '9' = Completada
-- '95' = Cancelada

UPDATE WMWHSE1.ORDERS
SET
    STATUS = '5',
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = '{{usuario}}',
    NOTES = COALESCE(NOTES, '') || ' | Cerrada por SAC: {{motivo}} [' || '{{usuario}}' || ' ' || CHAR(CURRENT_TIMESTAMP) || ']'
WHERE
    ORDERKEY = '{{orderkey}}'
    AND STATUS IN ('0', '1', '2');  -- Solo cerrar si está abierta/proceso/parcial

-- QUERY DE VERIFICACIÓN:
-- SELECT ORDERKEY, STATUS, EDITDATE, EDITWHO, NOTES
-- FROM WMWHSE1.ORDERS WHERE ORDERKEY = '{{orderkey}}';
