-- ============================================
-- NOMBRE: Actualizar Status de ASN
-- CATEGORÍA: DML - Corrección
-- TIPO: UPDATE
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-22
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Actualiza el status de un ASN (Advance Shipping Notice).
-- Usado para corregir ASN estancados o actualizar estados.
--
-- CASOS DE USO:
-- - ASN sin actualizar por más de 24h
-- - Corrección de status incorrecto
-- - Forzar cierre de ASN completados
--
-- PARÁMETROS:
-- {{receiptkey}} - Número de ASN/Recibo
-- {{nuevo_status}} - Nuevo status a establecer
-- {{usuario}} - Usuario que modifica
--
-- STATUS DE RECEIPT EN MANHATTAN:
-- '0' = Abierto
-- '5' = En Verificación
-- '9' = Cerrado
-- '11' = Recibido
-- '95' = Cancelado

UPDATE WMWHSE1.RECEIPT
SET
    STATUS = '{{nuevo_status}}',
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = '{{usuario}}'
WHERE
    RECEIPTKEY = '{{receiptkey}}'
    AND STATUS NOT IN ('95');  -- No modificar cancelados

-- QUERY DE VERIFICACIÓN:
-- SELECT RECEIPTKEY, STATUS, EDITDATE, EDITWHO
-- FROM WMWHSE1.RECEIPT WHERE RECEIPTKEY = '{{receiptkey}}';
