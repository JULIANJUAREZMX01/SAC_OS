-- ============================================
-- NOMBRE: Ajustar Cantidad Esperada en Recibo
-- CATEGORÍA: DML - Corrección
-- TIPO: UPDATE
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-22
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Ajusta la cantidad esperada (EXPECTEDQTY) en líneas de recibo.
-- Usado para corregir discrepancias entre ASN y recepción física.
--
-- CASOS DE USO:
-- - ASN llegó con cantidad diferente a la notificada
-- - Corrección post-conteo físico
-- - Ajuste por mercancía dañada
--
-- PARÁMETROS:
-- {{receiptkey}} - Número de ASN/Recibo
-- {{linea}} - Número de línea
-- {{nueva_cantidad}} - Nueva cantidad esperada
-- {{usuario}} - Usuario que ajusta
-- {{motivo}} - Motivo del ajuste

UPDATE WMWHSE1.RECEIPTDETAIL
SET
    EXPECTEDQTY = {{nueva_cantidad}},
    EDITDATE = CURRENT_TIMESTAMP,
    EDITWHO = '{{usuario}}',
    NOTES = COALESCE(NOTES, '') || ' | Ajuste: {{motivo}}'
WHERE
    RECEIPTKEY = '{{receiptkey}}'
    AND RECEIPTLINENUMBER = '{{linea}}'
    AND STATUS NOT IN ('95');

-- QUERY DE VERIFICACIÓN:
-- SELECT RECEIPTKEY, RECEIPTLINENUMBER, SKU, EXPECTEDQTY, RECEIVEDQTY
-- FROM WMWHSE1.RECEIPTDETAIL
-- WHERE RECEIPTKEY = '{{receiptkey}}' AND RECEIPTLINENUMBER = '{{linea}}';
