-- ============================================
-- NOMBRE: Trazabilidad completa de LPN
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene la trazabilidad completa de un LPN, incluyendo
-- todos los movimientos, transacciones y cambios de ubicación.
-- Útil para investigar ubicación y estado de mercancía.

-- TABLAS INVOLUCRADAS:
-- - LPN (Información de LPN)
-- - LOTXLOCXID (Inventario actual)
-- - ITRN (Transacciones de inventario)
-- - TASKDETAIL (Tareas ejecutadas)

-- PARAMETROS:
-- {{lpn_numero}} - LPN a rastrear
-- {{storerkey}} - Código de almacén (default: C22)

-- PARTE 1: Estado actual del LPN
SELECT
    '01_ESTADO_ACTUAL' AS seccion,
    inv.ID AS lpn,
    inv.LOC AS ubicacion,
    l.PUTAWAYZONE AS zona,
    inv.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    inv.QTY AS cantidad,
    inv.STATUS AS status,
    inv.ADDDATE AS fecha_ingreso,
    inv.EDITDATE AS ultima_modificacion,
    NULL AS fecha_movimiento,
    NULL AS tipo_transaccion,
    NULL AS usuario,
    'Ubicación actual' AS detalle
FROM
    WMWHSE1.LOTXLOCXID inv
    LEFT JOIN WMWHSE1.SKU sk ON inv.SKU = sk.SKU AND inv.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.LOC l ON inv.LOC = l.LOC
WHERE
    inv.STORERKEY = '{{storerkey}}'
    AND inv.ID = '{{lpn_numero}}'

UNION ALL

-- PARTE 2: Transacciones de inventario
SELECT
    '02_TRANSACCIONES' AS seccion,
    i.ID AS lpn,
    i.LOC AS ubicacion,
    NULL AS zona,
    i.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    i.QTY AS cantidad,
    i.STATUS AS status,
    NULL AS fecha_ingreso,
    NULL AS ultima_modificacion,
    i.ADDDATE AS fecha_movimiento,
    i.TRANTYPE AS tipo_transaccion,
    i.ADDWHO AS usuario,
    CONCAT('De: ', COALESCE(i.FROMLOC, 'N/A'), ' -> A: ', COALESCE(i.TOLOC, 'N/A')) AS detalle
FROM
    WMWHSE1.ITRN i
    LEFT JOIN WMWHSE1.SKU sk ON i.SKU = sk.SKU AND i.STORERKEY = sk.STORERKEY
WHERE
    i.STORERKEY = '{{storerkey}}'
    AND i.ID = '{{lpn_numero}}'

UNION ALL

-- PARTE 3: Tareas asociadas al LPN
SELECT
    '03_TAREAS' AS seccion,
    td.FROMLPN AS lpn,
    td.FROMLOC AS ubicacion,
    NULL AS zona,
    td.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    td.QTY AS cantidad,
    td.STATUS AS status,
    td.STARTTIME AS fecha_ingreso,
    td.ENDTIME AS ultima_modificacion,
    td.ADDDATE AS fecha_movimiento,
    td.TASKTYPE AS tipo_transaccion,
    td.USERKEY AS usuario,
    CONCAT('Tarea: ', td.TASKDETAILKEY, ' | Hacia: ', COALESCE(td.TOLOC, 'N/A')) AS detalle
FROM
    WMWHSE1.TASKDETAIL td
    LEFT JOIN WMWHSE1.SKU sk ON td.SKU = sk.SKU AND td.STORERKEY = sk.STORERKEY
WHERE
    td.STORERKEY = '{{storerkey}}'
    AND (
        td.FROMLPN = '{{lpn_numero}}'
        OR td.TOLPN = '{{lpn_numero}}'
    )

ORDER BY
    seccion,
    fecha_movimiento DESC NULLS LAST;
