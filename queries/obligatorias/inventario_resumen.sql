-- ============================================
-- NOMBRE: Resumen de inventario del CEDIS
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Genera un resumen del inventario disponible en el CEDIS.
-- Incluye totales por área, tipo de producto y status.
-- Útil para validar niveles de inventario y planificación.

-- TABLAS INVOLUCRADAS:
-- - LOTXLOCXID (Inventario por ubicación)
-- - LOC (Ubicaciones)
-- - SKU (Información de productos)
-- - PUTAWAYZONE (Zonas de almacenamiento)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)

SELECT
    l.PUTAWAYZONE AS zona_almacen,
    pz.DESCR AS descripcion_zona,
    l.LOCATIONTYPE AS tipo_ubicacion,
    CASE l.LOCATIONTYPE
        WHEN 'PICK' THEN 'Picking'
        WHEN 'BULK' THEN 'Bulk/Reserva'
        WHEN 'STAGE' THEN 'Staging'
        WHEN 'DOCK' THEN 'Andén'
        WHEN 'RECV' THEN 'Recibo'
        WHEN 'SHIP' THEN 'Embarque'
        ELSE 'Otro'
    END AS tipo_descripcion,
    COUNT(DISTINCT inv.LOC) AS ubicaciones_ocupadas,
    COUNT(DISTINCT inv.SKU) AS skus_distintos,
    SUM(inv.QTY) AS qty_total_piezas,
    COUNT(DISTINCT inv.ID) AS total_lpn,
    ROUND(AVG(inv.QTY), 2) AS promedio_qty_por_lpn,
    SUM(CASE WHEN inv.STATUS = 'OK' THEN inv.QTY ELSE 0 END) AS qty_disponible,
    SUM(CASE WHEN inv.STATUS = 'HOLD' THEN inv.QTY ELSE 0 END) AS qty_retenida,
    SUM(CASE WHEN inv.STATUS = 'DAMAGE' THEN inv.QTY ELSE 0 END) AS qty_danada
FROM
    WMWHSE1.LOTXLOCXID inv
    INNER JOIN WMWHSE1.LOC l ON inv.LOC = l.LOC
    LEFT JOIN WMWHSE1.PUTAWAYZONE pz ON l.PUTAWAYZONE = pz.PUTAWAYZONE
WHERE
    inv.STORERKEY = '{{storerkey}}'
    AND inv.QTY > 0  -- Solo ubicaciones con inventario
GROUP BY
    l.PUTAWAYZONE,
    pz.DESCR,
    l.LOCATIONTYPE
ORDER BY
    l.PUTAWAYZONE,
    l.LOCATIONTYPE;
