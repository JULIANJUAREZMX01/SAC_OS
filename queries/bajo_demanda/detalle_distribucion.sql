-- ============================================
-- NOMBRE: Detalle de distribución por tienda
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene el detalle completo de distribuciones para una
-- OC específica, agrupado por tienda destino. Útil para
-- validar asignaciones y preparar embarques.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de distribuciones)
-- - ORDERDETAIL (Detalle)
-- - SKU (Información de productos)
-- - STORER (Información de tiendas)

-- PARAMETROS:
-- {{oc_referencia}} - Número de OC original (referencia)
-- {{storerkey}} - Código de almacén (default: C22)
-- {{tienda_destino}} - Filtrar por tienda específica (opcional, usar % para todas)

SELECT
    -- Información de tienda
    o.CONSIGNEEKEY AS codigo_tienda,
    st.COMPANY AS nombre_tienda,
    st.ADDRESS1 AS direccion,
    st.CITY AS ciudad,
    st.STATE AS estado,
    -- Información de distribución
    o.ORDERKEY AS numero_distro,
    o.EXTERNORDERKEY AS distro_externa,
    o.EXTERNALORDERKEY2 AS oc_referencia,
    o.ORDERDATE AS fecha_distro,
    o.DELIVERYDATE AS fecha_entrega,
    o.STATUS AS status_distro,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS status_descripcion,
    -- Detalle de SKU
    od.ORDERLINENUMBER AS linea,
    od.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    sk.INNERPACK AS inner_pack,
    od.ORIGINALQTY AS qty_asignada,
    od.OPENQTY AS qty_pendiente,
    od.SHIPPEDQTY AS qty_enviada,
    od.QTYPICKED AS qty_pickeada,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(od.ORIGINALQTY / sk.INNERPACK, 2)
        ELSE od.ORIGINALQTY
    END AS cajas_asignadas,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(od.SHIPPEDQTY / sk.INNERPACK, 2)
        ELSE od.SHIPPEDQTY
    END AS cajas_enviadas,
    -- Cálculos
    ROUND((od.SHIPPEDQTY / NULLIF(od.ORIGINALQTY, 0)) * 100, 2) AS porcentaje_enviado,
    od.STATUS AS status_linea,
    od.PACKKEY AS empaque,
    od.UOM AS unidad
FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU sk ON od.SKU = sk.SKU AND o.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.STORER st ON o.CONSIGNEEKEY = st.STORERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
    AND o.EXTERNALORDERKEY2 = '{{oc_referencia}}'
    AND (
        '{{tienda_destino}}' = '%'
        OR o.CONSIGNEEKEY = '{{tienda_destino}}'
        OR o.CONSIGNEEKEY LIKE '{{tienda_destino}}'
    )
ORDER BY
    o.CONSIGNEEKEY,
    o.ORDERKEY,
    od.ORDERLINENUMBER;
