-- ============================================
-- NOMBRE: Búsqueda de ASN (Advanced Shipping Notice)
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Búsqueda completa de un ASN específico por número.
-- Incluye cabecera, detalle de líneas, status de recibo
-- y comparación esperado vs recibido.

-- TABLAS INVOLUCRADAS:
-- - RECEIPT (Cabecera de recibos/ASN)
-- - RECEIPTDETAIL (Detalle de recibos)
-- - SKU (Información de productos)
-- - STORER (Proveedores)

-- PARAMETROS:
-- {{asn_numero}} - Número de ASN a buscar
-- {{storerkey}} - Código de almacén (default: C22)

SELECT
    -- Información de cabecera
    r.RECEIPTKEY AS asn_numero,
    r.EXTERNRECEIPTKEY AS asn_externo,
    r.STORERKEY AS almacen,
    r.POKEY AS oc_relacionada,
    r.CARRIERKEY AS transportista,
    r.TRAILERKEY AS trailer,
    r.DOOR AS anden,
    r.EXPECTEDRECEIPTDATE AS fecha_llegada_esperada,
    r.RECEIPTDATE AS fecha_recibo,
    r.CLOSEDDATE AS fecha_cierre,
    r.ADDDATE AS fecha_creacion,
    r.EDITDATE AS fecha_modificacion,
    r.STATUS AS status_cabecera,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '9' THEN 'Recibido Parcial'
        WHEN '10' THEN 'Recibido'
        WHEN '80' THEN 'Cerrado'
        WHEN '95' THEN 'Cancelado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    r.ADDWHO AS creado_por,
    r.EDITWHO AS modificado_por,
    -- Información de línea
    rd.RECEIPTLINENUMBER AS linea,
    rd.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    rd.QTYEXPECTED AS qty_esperada,
    rd.QTYRECEIVED AS qty_recibida,
    rd.QTYEXPECTED - COALESCE(rd.QTYRECEIVED, 0) AS qty_pendiente,
    ROUND((COALESCE(rd.QTYRECEIVED, 0) / NULLIF(rd.QTYEXPECTED, 0)) * 100, 2) AS porcentaje_recibido,
    rd.PACKKEY AS empaque,
    rd.UOM AS unidad,
    sk.INNERPACK AS inner_pack,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(rd.QTYEXPECTED / sk.INNERPACK, 2)
        ELSE rd.QTYEXPECTED
    END AS cajas_esperadas,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(COALESCE(rd.QTYRECEIVED, 0) / sk.INNERPACK, 2)
        ELSE COALESCE(rd.QTYRECEIVED, 0)
    END AS cajas_recibidas,
    rd.STATUS AS status_linea,
    -- Alertas
    CASE
        WHEN rd.QTYRECEIVED > rd.QTYEXPECTED THEN 'EXCEDENTE'
        WHEN COALESCE(rd.QTYRECEIVED, 0) < rd.QTYEXPECTED AND r.STATUS IN ('10', '80') THEN 'FALTANTE'
        WHEN rd.QTYRECEIVED IS NULL OR rd.QTYRECEIVED = 0 THEN 'SIN_RECIBIR'
        ELSE 'OK'
    END AS alerta_recibo,
    r.NOTES AS notas_asn,
    rd.NOTES AS notas_linea
FROM
    WMWHSE1.RECEIPT r
    INNER JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
    LEFT JOIN WMWHSE1.SKU sk ON rd.SKU = sk.SKU AND r.STORERKEY = sk.STORERKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND (
        r.RECEIPTKEY = '{{asn_numero}}'
        OR r.EXTERNRECEIPTKEY = '{{asn_numero}}'
        OR r.RECEIPTKEY LIKE '%{{asn_numero}}%'
        OR r.EXTERNRECEIPTKEY LIKE '%{{asn_numero}}%'
    )
ORDER BY
    rd.RECEIPTLINENUMBER;
