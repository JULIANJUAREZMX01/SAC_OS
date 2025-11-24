-- ============================================
-- NOMBRE: ASN (Avisos de Embarque) pendientes de recibir
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Lista todos los ASN (Advanced Shipping Notices) que están
-- pendientes de recibo en el CEDIS. Identifica embarques
-- en tránsito que deben ser procesados.

-- TABLAS INVOLUCRADAS:
-- - RECEIPT (Cabecera de recibos/ASN)
-- - RECEIPTDETAIL (Detalle de recibos)
-- - SKU (Información de productos)
-- - STORER (Información de proveedor)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_antiguedad}} - Días máximos de antigüedad (default: 30)

SELECT
    r.RECEIPTKEY AS asn_numero,
    r.EXTERNRECEIPTKEY AS asn_externo,
    r.STORERKEY AS almacen,
    r.POKEY AS oc_relacionada,
    r.CARRIERKEY AS transportista,
    r.ADDDATE AS fecha_creacion,
    r.RECEIPTDATE AS fecha_recibo_esperada,
    r.EXPECTEDRECEIPTDATE AS fecha_llegada_esperada,
    DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) AS dias_en_transito,
    r.STATUS AS status,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '9' THEN 'Recibido Parcial'
        WHEN '10' THEN 'Recibido'
        WHEN '80' THEN 'Cerrado'
        WHEN '95' THEN 'Cancelado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    COUNT(rd.RECEIPTLINENUMBER) AS total_lineas,
    SUM(rd.QTYEXPECTED) AS qty_esperada_total,
    SUM(rd.QTYRECEIVED) AS qty_recibida_total,
    SUM(rd.QTYEXPECTED) - SUM(COALESCE(rd.QTYRECEIVED, 0)) AS qty_pendiente_total,
    CASE
        WHEN SUM(rd.QTYEXPECTED) > 0 THEN
            ROUND((SUM(COALESCE(rd.QTYRECEIVED, 0)) / SUM(rd.QTYEXPECTED)) * 100, 2)
        ELSE 0
    END AS porcentaje_recibido,
    r.TRAILERKEY AS trailer,
    r.NOTES AS notas
FROM
    WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND r.STATUS NOT IN ('10', '80', '95')  -- No recibidos, cerrados o cancelados
    AND DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) <= {{dias_antiguedad}}
GROUP BY
    r.RECEIPTKEY,
    r.EXTERNRECEIPTKEY,
    r.STORERKEY,
    r.POKEY,
    r.CARRIERKEY,
    r.ADDDATE,
    r.RECEIPTDATE,
    r.EXPECTEDRECEIPTDATE,
    r.STATUS,
    r.TRAILERKEY,
    r.NOTES
ORDER BY
    dias_en_transito DESC,
    r.RECEIPTKEY;
