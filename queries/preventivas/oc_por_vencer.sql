-- ============================================
-- NOMBRE: OCs próximas a vencer (3 días)
-- CATEGORÍA: preventiva
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica órdenes de compra que están próximas a vencer
-- en los próximos 3 días. Permite acciones preventivas
-- antes de que las OCs expiren.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_alerta}} - Días antes de vencimiento para alertar (default: 3)

SELECT
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.STORERKEY AS almacen,
    o.ORDERDATE AS fecha_orden,
    o.DELIVERYDATE AS fecha_entrega,
    DATEDIFF(DAY, CURRENT_DATE, o.DELIVERYDATE) AS dias_para_vencer,
    CASE
        WHEN DATEDIFF(DAY, CURRENT_DATE, o.DELIVERYDATE) <= 1 THEN 'CRITICO'
        WHEN DATEDIFF(DAY, CURRENT_DATE, o.DELIVERYDATE) <= 2 THEN 'ALTO'
        WHEN DATEDIFF(DAY, CURRENT_DATE, o.DELIVERYDATE) <= 3 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS nivel_urgencia,
    o.STATUS AS status,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        ELSE 'Otro'
    END AS status_descripcion,
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
    AND o.STATUS IN ('0', '1', '2')  -- No completadas
    AND o.DELIVERYDATE IS NOT NULL
    AND o.DELIVERYDATE > CURRENT_DATE  -- Aún no vencidas
    AND DATEDIFF(DAY, CURRENT_DATE, o.DELIVERYDATE) <= {{dias_alerta}}
GROUP BY
    o.ORDERKEY,
    o.EXTERNORDERKEY,
    o.STORERKEY,
    o.ORDERDATE,
    o.DELIVERYDATE,
    o.STATUS,
    o.NOTES
ORDER BY
    dias_para_vencer ASC,
    qty_pendiente DESC;
