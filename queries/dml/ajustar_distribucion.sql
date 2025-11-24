-- ============================================
-- NOMBRE: Ajustar Cantidad de Distribución
-- CATEGORÍA: DML - Corrección
-- TIPO: UPDATE
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-22
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Ajusta la cantidad abierta (OPENQTY) de una línea de distribución
-- cuando excede la cantidad disponible en la OC.
--
-- CASOS DE USO:
-- - Distribución excede OC (detectado por query preventiva)
-- - Ajuste manual solicitado por analista
-- - Corrección de error de carga
--
-- PARÁMETROS:
-- {{orderkey}} - Número de OC/Distribución
-- {{linea}} - Número de línea
-- {{nueva_cantidad}} - Nueva cantidad a establecer
-- {{usuario}} - Usuario que realiza el cambio (para auditoría)
--
-- TABLAS AFECTADAS:
-- - ORDERDETAIL (UPDATE)
--
-- PRE-CONDICIONES:
-- - Verificar que la OC existe y está abierta
-- - Verificar que la línea existe
-- - Verificar que nueva_cantidad <= cantidad original
--
-- POST-VALIDACIÓN:
-- - Confirmar que el UPDATE afectó exactamente 1 registro

UPDATE WMWHSE1.ORDERDETAIL
SET
    OPENQTY = {{nueva_cantidad}},
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = '{{usuario}}'
WHERE
    ORDERKEY = '{{orderkey}}'
    AND ORDERLINENUMBER = '{{linea}}'
    AND STATUS NOT IN ('95', '99');  -- No modificar canceladas/cerradas

-- QUERY DE VERIFICACIÓN POST-UPDATE:
-- SELECT ORDERKEY, ORDERLINENUMBER, OPENQTY, EDITDATE, EDITWHO
-- FROM WMWHSE1.ORDERDETAIL
-- WHERE ORDERKEY = '{{orderkey}}' AND ORDERLINENUMBER = '{{linea}}';
