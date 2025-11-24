-- ============================================
-- NOMBRE: Distribuciones incompletas (menores que OC)
-- CATEGORÍA: preventiva
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica OCs donde la suma de distribuciones es MENOR
-- que la cantidad total de la OC. Indica mercancía sin
-- asignar a tiendas que podría quedarse en el CEDIS.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (OCs y Distribuciones)
-- - ORDERDETAIL (Detalles)
-- - SKU (Información de productos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{fecha_inicio}} - Fecha inicio del período
-- {{fecha_fin}} - Fecha fin del período
-- {{umbral_porcentaje}} - Umbral mínimo de diferencia para alertar (default: 5)

WITH OC_Totales AS (
    -- Totales por SKU en las OCs originales
    SELECT
        o.ORDERKEY AS oc_key,
        o.EXTERNORDERKEY AS oc_externa,
        od.SKU,
        SUM(od.ORIGINALQTY) AS qty_oc_total
    FROM
        WMWHSE1.ORDERS o
        INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE
        o.STORERKEY = '{{storerkey}}'
        AND o.ORDERTYPE IN ('PO', 'PURCHASE')
        AND o.STATUS NOT IN ('95')
        AND DATE(o.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    GROUP BY
        o.ORDERKEY,
        o.EXTERNORDERKEY,
        od.SKU
),
Distro_Totales AS (
    -- Totales de distribuciones relacionadas a cada OC
    SELECT
        o.EXTERNALORDERKEY2 AS oc_referencia,
        od.SKU,
        SUM(od.ORIGINALQTY) AS qty_distro_total
    FROM
        WMWHSE1.ORDERS o
        INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE
        o.STORERKEY = '{{storerkey}}'
        AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
        AND o.STATUS NOT IN ('95')
    GROUP BY
        o.EXTERNALORDERKEY2,
        od.SKU
)
SELECT
    'INCOMPLETA' AS tipo_alerta,
    CASE
        WHEN ((oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)) / oc.qty_oc_total) * 100 > 50 THEN 'ALTO'
        WHEN ((oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)) / oc.qty_oc_total) * 100 > 20 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS severidad,
    oc.oc_key AS oc_numero,
    oc.oc_externa AS oc_externa,
    oc.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    oc.qty_oc_total AS qty_oc,
    COALESCE(dt.qty_distro_total, 0) AS qty_distribuida,
    oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0) AS qty_sin_distribuir,
    ROUND(((oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)) / oc.qty_oc_total) * 100, 2) AS porcentaje_sin_distribuir,
    CASE
        WHEN sk.INNERPACK > 0 THEN
            ROUND((oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)) / sk.INNERPACK, 2)
        ELSE oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)
    END AS cajas_sin_distribuir
FROM
    OC_Totales oc
    LEFT JOIN Distro_Totales dt ON oc.oc_key = dt.oc_referencia AND oc.SKU = dt.SKU
    LEFT JOIN WMWHSE1.SKU sk ON oc.SKU = sk.SKU AND sk.STORERKEY = '{{storerkey}}'
WHERE
    -- Distribución menor que OC o sin distribución
    COALESCE(dt.qty_distro_total, 0) < oc.qty_oc_total
    -- Solo si la diferencia es significativa
    AND ((oc.qty_oc_total - COALESCE(dt.qty_distro_total, 0)) / oc.qty_oc_total) * 100 >= {{umbral_porcentaje}}
ORDER BY
    porcentaje_sin_distribuir DESC,
    qty_sin_distribuir DESC;
