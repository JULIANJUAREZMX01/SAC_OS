-- ============================================
-- NOMBRE: Programa de recibo del día
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria (ejecutar cada mañana)
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene el programa de recibo esperado para el día actual.
-- Lista todos los ASN con fecha de llegada programada,
-- ordenados por hora estimada de llegada.

-- TABLAS INVOLUCRADAS:
-- - RECEIPT (Cabecera de recibos/ASN)
-- - RECEIPTDETAIL (Detalle de recibos)
-- - SKU (Información de productos)
-- - STORER (Proveedores)

-- PARAMETROS:
-- {{fecha_recibo}} - Fecha del programa (YYYY-MM-DD)
-- {{storerkey}} - Código de almacén (default: C22)

SELECT
    r.RECEIPTKEY AS asn_numero,
    r.EXTERNRECEIPTKEY AS asn_externo,
    r.POKEY AS oc_relacionada,
    r.STORERKEY AS almacen,
    sup.COMPANY AS proveedor,
    r.CARRIERKEY AS transportista,
    r.TRAILERKEY AS trailer_placa,
    r.EXPECTEDRECEIPTDATE AS fecha_llegada_esperada,
    r.RECEIPTDATE AS fecha_recibo_programada,
    r.ADDDATE AS fecha_creacion_asn,
    r.STATUS AS status,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '9' THEN 'Recibido Parcial'
        ELSE 'Otro'
    END AS status_descripcion,
    r.DOOR AS anden_asignado,
    COUNT(DISTINCT rd.SKU) AS total_skus,
    COUNT(rd.RECEIPTLINENUMBER) AS total_lineas,
    SUM(rd.QTYEXPECTED) AS qty_esperada_total,
    SUM(COALESCE(rd.QTYRECEIVED, 0)) AS qty_recibida_actual,
    CASE
        WHEN SUM(rd.QTYEXPECTED) > 0 THEN
            ROUND((SUM(COALESCE(rd.QTYRECEIVED, 0)) / SUM(rd.QTYEXPECTED)) * 100, 2)
        ELSE 0
    END AS porcentaje_completado,
    -- Estimación de cajas basada en inner pack
    SUM(
        CASE
            WHEN sk.INNERPACK > 0 THEN ROUND(rd.QTYEXPECTED / sk.INNERPACK, 0)
            ELSE rd.QTYEXPECTED
        END
    ) AS cajas_esperadas,
    r.NOTES AS notas_asn
FROM
    WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
    LEFT JOIN WMWHSE1.SKU sk ON rd.SKU = sk.SKU AND r.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.STORER sup ON r.SUSR1 = sup.STORERKEY  -- Campo proveedor puede variar
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND r.STATUS NOT IN ('10', '80', '95')  -- No completados, cerrados o cancelados
    AND (
        DATE(r.EXPECTEDRECEIPTDATE) = '{{fecha_recibo}}'
        OR DATE(r.RECEIPTDATE) = '{{fecha_recibo}}'
        -- Incluir ASN sin fecha pero creados recientemente
        OR (r.EXPECTEDRECEIPTDATE IS NULL AND DATE(r.ADDDATE) = '{{fecha_recibo}}')
    )
GROUP BY
    r.RECEIPTKEY,
    r.EXTERNRECEIPTKEY,
    r.POKEY,
    r.STORERKEY,
    sup.COMPANY,
    r.CARRIERKEY,
    r.TRAILERKEY,
    r.EXPECTEDRECEIPTDATE,
    r.RECEIPTDATE,
    r.ADDDATE,
    r.STATUS,
    r.DOOR,
    r.NOTES
ORDER BY
    r.EXPECTEDRECEIPTDATE ASC NULLS LAST,
    r.RECEIPTKEY;
