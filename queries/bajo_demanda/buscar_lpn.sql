-- ============================================
-- NOMBRE: Búsqueda de LPN (License Plate Number)
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Búsqueda completa de información de un LPN específico.
-- Incluye ubicación actual, contenido, historial y status.
-- Útil para localización y trazabilidad de mercancía.

-- TABLAS INVOLUCRADAS:
-- - LPN (Cabecera de LPN)
-- - LPNDETAIL (Detalle de contenido)
-- - LOTXLOCXID (Inventario)
-- - SKU (Información de productos)
-- - LOC (Ubicaciones)

-- PARAMETROS:
-- {{lpn_numero}} - LPN a buscar (puede ser parcial)
-- {{storerkey}} - Código de almacén (default: C22)

-- PARTE 1: Información del LPN
SELECT
    'CABECERA_LPN' AS tipo_registro,
    lp.LPN AS lpn_numero,
    lp.PARENTLPN AS lpn_padre,
    lp.CHILDLPN AS lpn_hijo,
    lp.STORERKEY AS almacen,
    lp.LOC AS ubicacion_actual,
    l.PUTAWAYZONE AS zona,
    l.LOCATIONTYPE AS tipo_ubicacion,
    lp.STATUS AS status,
    CASE lp.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '10' THEN 'Ubicado'
        WHEN '18' THEN 'En Picking'
        WHEN '19' THEN 'Pickeado'
        WHEN '21' THEN 'En Packing'
        WHEN '22' THEN 'Empacado'
        WHEN '95' THEN 'Enviado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    lp.ADDDATE AS fecha_creacion,
    lp.EDITDATE AS fecha_modificacion,
    lp.ADDWHO AS creado_por,
    lp.EDITWHO AS modificado_por,
    NULL AS sku,
    NULL AS descripcion_sku,
    NULL AS cantidad
FROM
    WMWHSE1.LPN lp
    LEFT JOIN WMWHSE1.LOC l ON lp.LOC = l.LOC
WHERE
    lp.STORERKEY = '{{storerkey}}'
    AND (
        lp.LPN = '{{lpn_numero}}'
        OR lp.LPN LIKE '%{{lpn_numero}}%'
    )

UNION ALL

-- PARTE 2: Contenido del LPN (desde inventario)
SELECT
    'CONTENIDO' AS tipo_registro,
    inv.ID AS lpn_numero,
    NULL AS lpn_padre,
    NULL AS lpn_hijo,
    inv.STORERKEY AS almacen,
    inv.LOC AS ubicacion_actual,
    l.PUTAWAYZONE AS zona,
    l.LOCATIONTYPE AS tipo_ubicacion,
    inv.STATUS AS status,
    CASE inv.STATUS
        WHEN 'OK' THEN 'Disponible'
        WHEN 'HOLD' THEN 'Retenido'
        WHEN 'DAMAGE' THEN 'Dañado'
        WHEN 'EXPIRED' THEN 'Expirado'
        ELSE inv.STATUS
    END AS status_descripcion,
    inv.ADDDATE AS fecha_creacion,
    inv.EDITDATE AS fecha_modificacion,
    inv.ADDWHO AS creado_por,
    inv.EDITWHO AS modificado_por,
    inv.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    inv.QTY AS cantidad
FROM
    WMWHSE1.LOTXLOCXID inv
    LEFT JOIN WMWHSE1.SKU sk ON inv.SKU = sk.SKU AND inv.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.LOC l ON inv.LOC = l.LOC
WHERE
    inv.STORERKEY = '{{storerkey}}'
    AND (
        inv.ID = '{{lpn_numero}}'
        OR inv.ID LIKE '%{{lpn_numero}}%'
    )
    AND inv.QTY > 0

ORDER BY
    tipo_registro,
    lpn_numero,
    sku;
