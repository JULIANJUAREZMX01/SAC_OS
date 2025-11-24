-- ============================================
-- NOMBRE: Distribuciones que exceden OC (CRÍTICO)
-- CATEGORÍA: preventiva
-- FRECUENCIA: Diaria - PRIORITARIA
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- QUERY CRÍTICA: Detecta distribuciones donde la suma de
-- cantidades distribuidas EXCEDE la cantidad de la OC original.
-- Esto indica un error de asignación que debe corregirse
-- inmediatamente para evitar faltantes.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (OCs y Distribuciones)
-- - ORDERDETAIL (Detalles)
-- - SKU (Información de productos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{fecha_inicio}} - Fecha inicio del período
-- {{fecha_fin}} - Fecha fin del período

WITH OC_Totales AS (
    -- Totales por SKU en las OCs originales
    SELECT
        o.EXTERNALORDERKEY2 AS oc_referencia,
        od.SKU,
        SUM(od.ORIGINALQTY) AS qty_oc_total
    FROM
        WMWHSE1.ORDERS o
        INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE
        o.STORERKEY = '{{storerkey}}'
        AND o.ORDERTYPE IN ('PO', 'PURCHASE')  -- Tipo OC
        AND o.STATUS NOT IN ('95')
    GROUP BY
        o.EXTERNALORDERKEY2,
        od.SKU
),
Distro_Totales AS (
    -- Totales por SKU en las distribuciones
    SELECT
        o.EXTERNALORDERKEY2 AS oc_referencia,
        o.CONSIGNEEKEY AS tienda_destino,
        od.SKU,
        SUM(od.ORIGINALQTY) AS qty_distro
    FROM
        WMWHSE1.ORDERS o
        INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE
        o.STORERKEY = '{{storerkey}}'
        AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')  -- Tipo distribución
        AND o.STATUS NOT IN ('95')
        AND DATE(o.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    GROUP BY
        o.EXTERNALORDERKEY2,
        o.CONSIGNEEKEY,
        od.SKU
),
Distro_Sum AS (
    -- Suma total de distribuciones por OC y SKU
    SELECT
        oc_referencia,
        SKU,
        SUM(qty_distro) AS qty_total_distribuida,
        COUNT(DISTINCT tienda_destino) AS tiendas_asignadas
    FROM Distro_Totales
    GROUP BY oc_referencia, SKU
)
SELECT
    'EXCEDENTE' AS tipo_alerta,
    'CRITICO' AS severidad,
    oc.oc_referencia AS oc_numero,
    oc.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    oc.qty_oc_total AS qty_oc,
    ds.qty_total_distribuida AS qty_distribuida,
    ds.qty_total_distribuida - oc.qty_oc_total AS excedente,
    ROUND(((ds.qty_total_distribuida - oc.qty_oc_total) / oc.qty_oc_total) * 100, 2) AS porcentaje_excedente,
    ds.tiendas_asignadas AS num_tiendas,
    CASE
        WHEN sk.INNERPACK > 0 THEN ROUND((ds.qty_total_distribuida - oc.qty_oc_total) / sk.INNERPACK, 2)
        ELSE ds.qty_total_distribuida - oc.qty_oc_total
    END AS cajas_excedentes
FROM
    OC_Totales oc
    INNER JOIN Distro_Sum ds ON oc.oc_referencia = ds.oc_referencia AND oc.SKU = ds.SKU
    LEFT JOIN WMWHSE1.SKU sk ON oc.SKU = sk.SKU AND sk.STORERKEY = '{{storerkey}}'
WHERE
    ds.qty_total_distribuida > oc.qty_oc_total  -- Solo excedentes
ORDER BY
    excedente DESC,
    oc.oc_referencia,
    oc.SKU;
