-- ============================================
-- VISTA: V_DISTRIBUTION_TOTALS
-- Totales de Distribuciones por OC y Tienda
-- CATEGORÍA: DDL - Vista
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Vista que consolida los totales de distribuciones
-- agrupados por OC original, SKU y tienda destino.
-- Permite comparación rápida OC vs Distribuciones.

-- PERMISOS REQUERIDOS:
-- CREATE VIEW en schema WMWHSE1

-- DEPENDENCIAS:
-- - WMWHSE1.ORDERS
-- - WMWHSE1.ORDERDETAIL
-- - WMWHSE1.SKU
-- - WMWHSE1.STORER

-- ============================================
-- SCRIPT DE CREACIÓN
-- ============================================

-- Eliminar vista si existe
DROP VIEW WMWHSE1.V_DISTRIBUTION_TOTALS;

-- Crear vista
CREATE VIEW WMWHSE1.V_DISTRIBUTION_TOTALS AS
SELECT
    -- Referencia a OC original
    o.EXTERNALORDERKEY2 AS OC_REFERENCIA,

    -- Información de distribución
    o.ORDERKEY AS DISTRO_NUMERO,
    o.EXTERNORDERKEY AS DISTRO_EXTERNA,
    o.STORERKEY AS ALMACEN_ORIGEN,

    -- Tienda destino
    o.CONSIGNEEKEY AS TIENDA_DESTINO,
    st.COMPANY AS NOMBRE_TIENDA,
    st.CITY AS CIUDAD_TIENDA,
    st.STATE AS ESTADO_TIENDA,

    -- SKU
    od.SKU AS SKU,
    sk.DESCR AS DESCRIPCION_SKU,
    sk.INNERPACK AS INNER_PACK,

    -- Cantidades
    od.ORIGINALQTY AS QTY_DISTRIBUIDA,
    od.OPENQTY AS QTY_PENDIENTE,
    od.SHIPPEDQTY AS QTY_ENVIADA,

    -- Cajas calculadas
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(od.ORIGINALQTY / sk.INNERPACK, 2)
        ELSE od.ORIGINALQTY
    END AS CAJAS_DISTRIBUIDAS,

    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND(od.SHIPPEDQTY / sk.INNERPACK, 2)
        ELSE od.SHIPPEDQTY
    END AS CAJAS_ENVIADAS,

    -- Estado
    o.STATUS AS STATUS_CODE,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS STATUS_DESCRIPCION,

    -- Porcentaje completado
    CASE
        WHEN od.ORIGINALQTY > 0 THEN
            ROUND((od.SHIPPEDQTY / od.ORIGINALQTY) * 100, 2)
        ELSE 0
    END AS PORCENTAJE_COMPLETADO,

    -- Fechas
    o.ORDERDATE AS FECHA_DISTRO,
    o.DELIVERYDATE AS FECHA_ENTREGA,
    o.ADDDATE AS FECHA_CREACION

FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU sk ON od.SKU = sk.SKU AND o.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.STORER st ON o.CONSIGNEEKEY = st.STORERKEY
WHERE
    o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')  -- Solo distribuciones
    AND o.STATUS != '95';  -- Excluir canceladas

-- ============================================
-- VISTA AGREGADA: Totales por OC y SKU
-- ============================================

DROP VIEW WMWHSE1.V_DISTRIBUTION_SUMMARY;

CREATE VIEW WMWHSE1.V_DISTRIBUTION_SUMMARY AS
SELECT
    OC_REFERENCIA,
    SKU,
    DESCRIPCION_SKU,
    INNER_PACK,
    COUNT(DISTINCT DISTRO_NUMERO) AS TOTAL_DISTRIBUCIONES,
    COUNT(DISTINCT TIENDA_DESTINO) AS TOTAL_TIENDAS,
    SUM(QTY_DISTRIBUIDA) AS QTY_TOTAL_DISTRIBUIDA,
    SUM(QTY_ENVIADA) AS QTY_TOTAL_ENVIADA,
    SUM(QTY_PENDIENTE) AS QTY_TOTAL_PENDIENTE,
    SUM(CAJAS_DISTRIBUIDAS) AS CAJAS_TOTAL_DISTRIBUIDAS,
    SUM(CAJAS_ENVIADAS) AS CAJAS_TOTAL_ENVIADAS,
    ROUND(AVG(PORCENTAJE_COMPLETADO), 2) AS PROMEDIO_COMPLETADO
FROM
    WMWHSE1.V_DISTRIBUTION_TOTALS
GROUP BY
    OC_REFERENCIA,
    SKU,
    DESCRIPCION_SKU,
    INNER_PACK;

-- ============================================
-- GRANT DE PERMISOS
-- ============================================

GRANT SELECT ON WMWHSE1.V_DISTRIBUTION_TOTALS TO PUBLIC;
GRANT SELECT ON WMWHSE1.V_DISTRIBUTION_SUMMARY TO PUBLIC;

-- ============================================
-- COMENTARIOS
-- ============================================

COMMENT ON TABLE WMWHSE1.V_DISTRIBUTION_TOTALS IS 'Vista de detalle de distribuciones - Sistema SAC';
COMMENT ON TABLE WMWHSE1.V_DISTRIBUTION_SUMMARY IS 'Vista de resumen de distribuciones por OC y SKU - Sistema SAC';
