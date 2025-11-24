-- ============================================
-- NOMBRE: Órdenes de Compra vencidas o expiradas
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica OCs que han superado su fecha de entrega esperada
-- o que llevan demasiado tiempo sin procesarse.
-- Genera alertas para seguimiento inmediato.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)
-- - SKU (Información de productos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_vencimiento}} - Días para considerar vencida (default: 7)

SELECT
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.STORERKEY AS almacen,
    o.ORDERDATE AS fecha_orden,
    o.DELIVERYDATE AS fecha_entrega_esperada,
    o.ADDDATE AS fecha_creacion,
    DATEDIFF(DAY, o.DELIVERYDATE, CURRENT_DATE) AS dias_vencida,
    DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) AS dias_desde_creacion,
    o.STATUS AS status,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        ELSE 'Otro'
    END AS status_descripcion,
    CASE
        WHEN DATEDIFF(DAY, o.DELIVERYDATE, CURRENT_DATE) > 7 THEN 'CRITICO'
        WHEN DATEDIFF(DAY, o.DELIVERYDATE, CURRENT_DATE) > 3 THEN 'ALTO'
        WHEN DATEDIFF(DAY, o.DELIVERYDATE, CURRENT_DATE) > 0 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS nivel_urgencia,
    COUNT(od.ORDERLINENUMBER) AS total_lineas,
    SUM(od.ORIGINALQTY) AS qty_total,
    SUM(od.OPENQTY) AS qty_pendiente,
    ROUND((SUM(od.OPENQTY) / NULLIF(SUM(od.ORIGINALQTY), 0)) * 100, 2) AS porcentaje_pendiente,
    o.NOTES AS notas
FROM
    WMWHSE1.ORDERS o
    LEFT JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.STATUS IN ('0', '1', '2')  -- No completadas ni canceladas
    AND (
        -- OCs con fecha de entrega vencida
        (o.DELIVERYDATE IS NOT NULL AND o.DELIVERYDATE < CURRENT_DATE)
        OR
        -- OCs muy antiguas sin fecha de entrega
        (o.DELIVERYDATE IS NULL AND DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) > {{dias_vencimiento}})
    )
GROUP BY
    o.ORDERKEY,
    o.EXTERNORDERKEY,
    o.STORERKEY,
    o.ORDERDATE,
    o.DELIVERYDATE,
    o.ADDDATE,
    o.STATUS,
    o.NOTES
ORDER BY
    dias_vencida DESC,
    nivel_urgencia,
    o.ORDERKEY;
