-- ============================================
-- NOMBRE: Búsqueda de Orden de Compra por número
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Búsqueda completa de una OC específica por número.
-- Retorna cabecera, detalle, status y métricas asociadas.
-- Soporta búsqueda por ORDERKEY o EXTERNORDERKEY.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)
-- - SKU (Información de productos)
-- - RECEIPT (ASN relacionados)

-- PARAMETROS:
-- {{oc_numero}} - Número de OC a buscar (con o sin prefijo C)
-- {{storerkey}} - Código de almacén (default: C22)

SELECT
    -- Información de cabecera
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.EXTERNALORDERKEY2 AS referencia_adicional,
    o.STORERKEY AS almacen,
    o.CONSIGNEEKEY AS destinatario,
    o.ORDERTYPE AS tipo_orden,
    o.ORDERDATE AS fecha_orden,
    o.DELIVERYDATE AS fecha_entrega,
    o.ADDDATE AS fecha_creacion,
    o.EDITDATE AS fecha_modificacion,
    o.STATUS AS status_cabecera,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS status_descripcion,
    o.ADDWHO AS creado_por,
    o.EDITWHO AS modificado_por,
    -- Información de línea
    od.ORDERLINENUMBER AS linea,
    od.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    od.ORIGINALQTY AS qty_original,
    od.OPENQTY AS qty_pendiente,
    od.SHIPPEDQTY AS qty_enviada,
    od.QTYALLOCATED AS qty_asignada,
    od.QTYPICKED AS qty_pickeada,
    od.STATUS AS status_linea,
    od.PACKKEY AS empaque,
    od.UOM AS unidad,
    sk.INNERPACK AS inner_pack,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(od.ORIGINALQTY / sk.INNERPACK, 2)
        ELSE od.ORIGINALQTY
    END AS cajas_originales,
    -- Cálculos
    ROUND((od.SHIPPEDQTY / NULLIF(od.ORIGINALQTY, 0)) * 100, 2) AS porcentaje_completado,
    o.NOTES AS notas
FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU sk ON od.SKU = sk.SKU AND o.STORERKEY = sk.STORERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND (
        o.ORDERKEY = '{{oc_numero}}'
        OR o.EXTERNORDERKEY = '{{oc_numero}}'
        OR o.ORDERKEY = 'C{{oc_numero}}'  -- Agregar prefijo C si no lo tiene
        OR o.EXTERNORDERKEY LIKE '%{{oc_numero}}%'
    )
ORDER BY
    od.ORDERLINENUMBER;
