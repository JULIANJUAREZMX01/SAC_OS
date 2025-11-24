-- ============================================
-- NOMBRE: Órdenes de Compra del día actual
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria (ejecutar cada mañana)
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene todas las órdenes de compra (OC) ingresadas o actualizadas
-- en el día actual. Incluye información de cabecera y totales.
-- Filtra por CEDIS Cancún (C22/427) y excluye OCs canceladas.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)
-- - STORER (Información de proveedor/tienda)

-- PARAMETROS:
-- {{fecha_inicio}} - Fecha inicio del día (YYYY-MM-DD)
-- {{fecha_fin}} - Fecha fin del día (YYYY-MM-DD)
-- {{storerkey}} - Código de almacén (default: C22)

SELECT
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.STORERKEY AS almacen,
    o.ORDERDATE AS fecha_orden,
    o.ADDDATE AS fecha_creacion,
    o.EDITDATE AS fecha_modificacion,
    o.STATUS AS status_oc,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS status_descripcion,
    o.ORDERTYPE AS tipo_orden,
    o.EXTERNALORDERKEY2 AS referencia_externa,
    o.NOTES AS notas,
    COUNT(od.ORDERLINENUMBER) AS total_lineas,
    SUM(od.ORIGINALQTY) AS qty_original_total,
    SUM(od.OPENQTY) AS qty_pendiente_total,
    SUM(od.SHIPPEDQTY) AS qty_enviada_total,
    SUM(od.QTYALLOCATED) AS qty_asignada_total
FROM
    WMWHSE1.ORDERS o
    LEFT JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.STATUS NOT IN ('95')  -- Excluir canceladas
    AND (
        DATE(o.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
        OR DATE(o.EDITDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    )
GROUP BY
    o.ORDERKEY,
    o.EXTERNORDERKEY,
    o.STORERKEY,
    o.ORDERDATE,
    o.ADDDATE,
    o.EDITDATE,
    o.STATUS,
    o.ORDERTYPE,
    o.EXTERNALORDERKEY2,
    o.NOTES
ORDER BY
    o.ADDDATE DESC,
    o.ORDERKEY;
