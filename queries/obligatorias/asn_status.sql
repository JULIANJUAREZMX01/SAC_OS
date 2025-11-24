-- ============================================
-- NOMBRE: Estado general de todos los ASN
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Resumen del estado de todos los ASN activos en el sistema.
-- Proporciona visibilidad completa del pipeline de recibo
-- agrupado por status para análisis gerencial.

-- TABLAS INVOLUCRADAS:
-- - RECEIPT (Cabecera de recibos/ASN)
-- - RECEIPTDETAIL (Detalle de recibos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{fecha_inicio}} - Fecha inicio del período
-- {{fecha_fin}} - Fecha fin del período

-- PARTE 1: Resumen por status
SELECT
    'RESUMEN' AS tipo_registro,
    r.STATUS AS status_code,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '9' THEN 'Recibido Parcial'
        WHEN '10' THEN 'Recibido'
        WHEN '80' THEN 'Cerrado'
        WHEN '95' THEN 'Cancelado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    COUNT(DISTINCT r.RECEIPTKEY) AS total_asn,
    SUM(rd.QTYEXPECTED) AS qty_total_esperada,
    SUM(rd.QTYRECEIVED) AS qty_total_recibida,
    ROUND(AVG(DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE)), 1) AS promedio_dias_antiguedad
FROM
    WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND DATE(r.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
GROUP BY
    r.STATUS

UNION ALL

-- PARTE 2: Detalle de ASN críticos (status 80 sin cerrar correctamente)
SELECT
    'CRITICO_80' AS tipo_registro,
    r.STATUS AS status_code,
    r.RECEIPTKEY AS status_descripcion,  -- Usamos este campo para el número ASN
    1 AS total_asn,
    SUM(rd.QTYEXPECTED) AS qty_total_esperada,
    SUM(rd.QTYRECEIVED) AS qty_total_recibida,
    DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) AS promedio_dias_antiguedad
FROM
    WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND r.STATUS = '80'  -- Status cerrado
    AND DATE(r.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    AND EXISTS (
        SELECT 1 FROM WMWHSE1.RECEIPTDETAIL rd2
        WHERE rd2.RECEIPTKEY = r.RECEIPTKEY
        AND rd2.QTYEXPECTED > COALESCE(rd2.QTYRECEIVED, 0)
    )
GROUP BY
    r.RECEIPTKEY,
    r.STATUS,
    r.ADDDATE

ORDER BY
    tipo_registro,
    status_code;
