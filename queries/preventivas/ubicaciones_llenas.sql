-- ============================================
-- NOMBRE: Ubicaciones al límite de capacidad
-- CATEGORÍA: preventiva
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica ubicaciones que están cerca o al límite de
-- su capacidad máxima. Permite planificar movimientos
-- preventivos antes de que se bloquee el putaway.

-- TABLAS INVOLUCRADAS:
-- - LOC (Ubicaciones)
-- - LOTXLOCXID (Inventario por ubicación)
-- - PUTAWAYZONE (Zonas de almacenamiento)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{umbral_capacidad}} - Porcentaje de capacidad para alertar (default: 80)

WITH Ubicacion_Ocupacion AS (
    SELECT
        l.LOC AS ubicacion,
        l.PUTAWAYZONE AS zona,
        l.LOCATIONTYPE AS tipo,
        l.LOCATIONSIZECLASS AS clase_tamano,
        l.CUBICCAPACITY AS capacidad_cubica,
        l.WEIGHTCAPACITY AS capacidad_peso,
        l.STATUS AS status_ubicacion,
        COUNT(DISTINCT inv.ID) AS lpn_count,
        COUNT(DISTINCT inv.SKU) AS sku_count,
        SUM(inv.QTY) AS qty_total,
        SUM(inv.QTY * COALESCE(sk.STDCUBE, 0.001)) AS cubicaje_ocupado,
        SUM(inv.QTY * COALESCE(sk.STDGROSSWGT, 0)) AS peso_ocupado
    FROM
        WMWHSE1.LOC l
        LEFT JOIN WMWHSE1.LOTXLOCXID inv ON l.LOC = inv.LOC
        LEFT JOIN WMWHSE1.SKU sk ON inv.SKU = sk.SKU AND inv.STORERKEY = sk.STORERKEY
    WHERE
        l.STATUS = 'OK'  -- Solo ubicaciones activas
        AND l.LOCATIONTYPE NOT IN ('STAGE', 'DOCK', 'RECV')  -- Excluir áreas de tránsito
    GROUP BY
        l.LOC,
        l.PUTAWAYZONE,
        l.LOCATIONTYPE,
        l.LOCATIONSIZECLASS,
        l.CUBICCAPACITY,
        l.WEIGHTCAPACITY,
        l.STATUS
)
SELECT
    uo.ubicacion,
    uo.zona,
    pz.DESCR AS descripcion_zona,
    uo.tipo AS tipo_ubicacion,
    uo.clase_tamano,
    uo.lpn_count AS lpns_en_ubicacion,
    uo.sku_count AS skus_distintos,
    uo.qty_total AS piezas_totales,
    -- Cálculo de ocupación por cubicaje
    uo.capacidad_cubica AS capacidad_cubica_max,
    ROUND(uo.cubicaje_ocupado, 2) AS cubicaje_actual,
    CASE
        WHEN uo.capacidad_cubica > 0 THEN
            ROUND((uo.cubicaje_ocupado / uo.capacidad_cubica) * 100, 2)
        ELSE NULL
    END AS porcentaje_cubicaje,
    -- Cálculo de ocupación por peso
    uo.capacidad_peso AS capacidad_peso_max,
    ROUND(uo.peso_ocupado, 2) AS peso_actual,
    CASE
        WHEN uo.capacidad_peso > 0 THEN
            ROUND((uo.peso_ocupado / uo.capacidad_peso) * 100, 2)
        ELSE NULL
    END AS porcentaje_peso,
    -- Nivel de alerta
    CASE
        WHEN (uo.capacidad_cubica > 0 AND (uo.cubicaje_ocupado / uo.capacidad_cubica) * 100 >= 95)
             OR (uo.capacidad_peso > 0 AND (uo.peso_ocupado / uo.capacidad_peso) * 100 >= 95) THEN 'CRITICO'
        WHEN (uo.capacidad_cubica > 0 AND (uo.cubicaje_ocupado / uo.capacidad_cubica) * 100 >= 90)
             OR (uo.capacidad_peso > 0 AND (uo.peso_ocupado / uo.capacidad_peso) * 100 >= 90) THEN 'ALTO'
        WHEN (uo.capacidad_cubica > 0 AND (uo.cubicaje_ocupado / uo.capacidad_cubica) * 100 >= {{umbral_capacidad}})
             OR (uo.capacidad_peso > 0 AND (uo.peso_ocupado / uo.capacidad_peso) * 100 >= {{umbral_capacidad}}) THEN 'MEDIO'
        ELSE 'BAJO'
    END AS nivel_alerta,
    'Considerar mover inventario a ubicaciones con más espacio' AS accion_sugerida
FROM
    Ubicacion_Ocupacion uo
    LEFT JOIN WMWHSE1.PUTAWAYZONE pz ON uo.zona = pz.PUTAWAYZONE
WHERE
    uo.qty_total > 0  -- Solo ubicaciones con inventario
    AND (
        -- Ubicaciones que exceden el umbral de capacidad cúbica
        (uo.capacidad_cubica > 0 AND (uo.cubicaje_ocupado / uo.capacidad_cubica) * 100 >= {{umbral_capacidad}})
        OR
        -- Ubicaciones que exceden el umbral de capacidad de peso
        (uo.capacidad_peso > 0 AND (uo.peso_ocupado / uo.capacidad_peso) * 100 >= {{umbral_capacidad}})
    )
ORDER BY
    nivel_alerta,
    porcentaje_cubicaje DESC NULLS LAST,
    porcentaje_peso DESC NULLS LAST;
