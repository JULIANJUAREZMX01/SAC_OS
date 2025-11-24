-- ============================================
-- NOMBRE: ASNs estancados sin movimiento
-- CATEGORÍA: preventiva
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Detecta ASNs que llevan tiempo sin actualizaciones o movimiento.
-- Estos pueden indicar problemas de recibo, mercancía olvidada
-- o errores en el proceso de recepción.

-- TABLAS INVOLUCRADAS:
-- - RECEIPT (Cabecera de recibos/ASN)
-- - RECEIPTDETAIL (Detalle de recibos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_sin_movimiento}} - Días sin actualización para alertar (default: 3)
-- {{max_dias_antiguedad}} - Máxima antigüedad a considerar (default: 60)

SELECT
    r.RECEIPTKEY AS asn_numero,
    r.EXTERNRECEIPTKEY AS asn_externo,
    r.STORERKEY AS almacen,
    r.POKEY AS oc_relacionada,
    r.ADDDATE AS fecha_creacion,
    r.EDITDATE AS ultima_actualizacion,
    DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) AS dias_desde_creacion,
    DATEDIFF(DAY, COALESCE(r.EDITDATE, r.ADDDATE), CURRENT_DATE) AS dias_sin_movimiento,
    r.STATUS AS status,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '9' THEN 'Recibido Parcial'
        ELSE 'Otro'
    END AS status_descripcion,
    CASE
        WHEN DATEDIFF(DAY, COALESCE(r.EDITDATE, r.ADDDATE), CURRENT_DATE) > 7 THEN 'CRITICO'
        WHEN DATEDIFF(DAY, COALESCE(r.EDITDATE, r.ADDDATE), CURRENT_DATE) > 5 THEN 'ALTO'
        WHEN DATEDIFF(DAY, COALESCE(r.EDITDATE, r.ADDDATE), CURRENT_DATE) > 3 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS nivel_urgencia,
    COUNT(rd.RECEIPTLINENUMBER) AS total_lineas,
    SUM(rd.QTYEXPECTED) AS qty_esperada,
    SUM(COALESCE(rd.QTYRECEIVED, 0)) AS qty_recibida,
    SUM(rd.QTYEXPECTED) - SUM(COALESCE(rd.QTYRECEIVED, 0)) AS qty_pendiente,
    CASE
        WHEN SUM(rd.QTYEXPECTED) > 0 THEN
            ROUND((SUM(COALESCE(rd.QTYRECEIVED, 0)) / SUM(rd.QTYEXPECTED)) * 100, 2)
        ELSE 0
    END AS porcentaje_completado,
    r.CARRIERKEY AS transportista,
    r.TRAILERKEY AS trailer,
    r.NOTES AS notas,
    CASE
        WHEN r.STATUS = '0' THEN 'Verificar si ASN fue enviado por proveedor'
        WHEN r.STATUS = '5' THEN 'Contactar transportista para estatus de entrega'
        WHEN r.STATUS = '9' THEN 'Completar proceso de recibo pendiente'
        ELSE 'Revisar manualmente el ASN'
    END AS accion_sugerida
FROM
    WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND r.STATUS NOT IN ('10', '80', '95')  -- No completados, cerrados o cancelados
    AND DATEDIFF(DAY, COALESCE(r.EDITDATE, r.ADDDATE), CURRENT_DATE) >= {{dias_sin_movimiento}}
    AND DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) <= {{max_dias_antiguedad}}
GROUP BY
    r.RECEIPTKEY,
    r.EXTERNRECEIPTKEY,
    r.STORERKEY,
    r.POKEY,
    r.ADDDATE,
    r.EDITDATE,
    r.STATUS,
    r.CARRIERKEY,
    r.TRAILERKEY,
    r.NOTES
ORDER BY
    dias_sin_movimiento DESC,
    nivel_urgencia,
    r.RECEIPTKEY;
