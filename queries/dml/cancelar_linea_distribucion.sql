-- ============================================
-- NOMBRE: Cancelar Línea de Distribución
-- CATEGORÍA: DML - Corrección
-- TIPO: UPDATE
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-22
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Cancela una línea específica de distribución.
-- Pone OPENQTY en 0 y marca status como cancelada.
--
-- CASOS DE USO:
-- - Línea duplicada
-- - Distribución errónea a tienda incorrecta
-- - SKU descontinuado
--
-- PARÁMETROS:
-- {{orderkey}} - Número de distribución
-- {{linea}} - Número de línea a cancelar
-- {{usuario}} - Usuario que cancela
-- {{motivo}} - Motivo de cancelación

UPDATE WMWHSE1.ORDERDETAIL
SET
    STATUS = '95',
    OPENQTY = 0,
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = '{{usuario}}',
    NOTES = COALESCE(NOTES, '') || ' | Cancelada: {{motivo}}'
WHERE
    ORDERKEY = '{{orderkey}}'
    AND ORDERLINENUMBER = '{{linea}}'
    AND STATUS NOT IN ('95');  -- No re-cancelar

-- QUERY DE VERIFICACIÓN:
-- SELECT ORDERKEY, ORDERLINENUMBER, SKU, STATUS, OPENQTY
-- FROM WMWHSE1.ORDERDETAIL
-- WHERE ORDERKEY = '{{orderkey}}' AND ORDERLINENUMBER = '{{linea}}';
