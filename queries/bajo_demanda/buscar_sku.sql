-- ============================================
-- NOMBRE: Búsqueda completa por SKU
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Búsqueda completa de información de un SKU específico.
-- Incluye maestro, inventario, órdenes activas y recepciones.
-- Útil para troubleshooting y análisis de productos.

-- TABLAS INVOLUCRADAS:
-- - SKU (Maestro de productos)
-- - LOTXLOCXID (Inventario)
-- - ORDERDETAIL (Órdenes activas)
-- - RECEIPTDETAIL (Recepciones)

-- PARAMETROS:
-- {{sku_numero}} - SKU a buscar
-- {{storerkey}} - Código de almacén (default: C22)

-- PARTE 1: Información del maestro de SKU
SELECT
    'MAESTRO' AS tipo_registro,
    s.SKU AS sku,
    s.DESCR AS descripcion,
    s.STORERKEY AS almacen,
    s.INNERPACK AS inner_pack,
    s.STDCUBE AS cubo_estandar,
    s.STDGROSSWGT AS peso_bruto,
    s.STDNETWGT AS peso_neto,
    s.PACKKEY AS pack_key,
    s.PUTAWAYZONE AS zona_putaway,
    s.HAZMATCODE AS codigo_hazmat,
    s.STATUS AS status,
    s.ADDDATE AS fecha_creacion,
    s.EDITDATE AS fecha_modificacion,
    NULL AS ubicacion,
    NULL AS cantidad,
    NULL AS documento_ref
FROM
    WMWHSE1.SKU s
WHERE
    s.STORERKEY = '{{storerkey}}'
    AND s.SKU = '{{sku_numero}}'

UNION ALL

-- PARTE 2: Inventario actual por ubicación
SELECT
    'INVENTARIO' AS tipo_registro,
    inv.SKU AS sku,
    sk.DESCR AS descripcion,
    inv.STORERKEY AS almacen,
    sk.INNERPACK AS inner_pack,
    NULL AS cubo_estandar,
    NULL AS peso_bruto,
    NULL AS peso_neto,
    NULL AS pack_key,
    l.PUTAWAYZONE AS zona_putaway,
    NULL AS codigo_hazmat,
    inv.STATUS AS status,
    inv.ADDDATE AS fecha_creacion,
    inv.EDITDATE AS fecha_modificacion,
    inv.LOC AS ubicacion,
    inv.QTY AS cantidad,
    inv.ID AS documento_ref  -- LPN
FROM
    WMWHSE1.LOTXLOCXID inv
    INNER JOIN WMWHSE1.SKU sk ON inv.SKU = sk.SKU AND inv.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.LOC l ON inv.LOC = l.LOC
WHERE
    inv.STORERKEY = '{{storerkey}}'
    AND inv.SKU = '{{sku_numero}}'
    AND inv.QTY > 0

UNION ALL

-- PARTE 3: Órdenes activas con este SKU
SELECT
    'ORDEN_ACTIVA' AS tipo_registro,
    od.SKU AS sku,
    sk.DESCR AS descripcion,
    o.STORERKEY AS almacen,
    sk.INNERPACK AS inner_pack,
    NULL AS cubo_estandar,
    NULL AS peso_bruto,
    NULL AS peso_neto,
    NULL AS pack_key,
    NULL AS zona_putaway,
    NULL AS codigo_hazmat,
    o.STATUS AS status,
    o.ADDDATE AS fecha_creacion,
    o.EDITDATE AS fecha_modificacion,
    NULL AS ubicacion,
    od.OPENQTY AS cantidad,
    o.ORDERKEY AS documento_ref  -- OC número
FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU sk ON od.SKU = sk.SKU AND o.STORERKEY = sk.STORERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND od.SKU = '{{sku_numero}}'
    AND o.STATUS IN ('0', '1', '2')  -- Activas
    AND od.OPENQTY > 0

UNION ALL

-- PARTE 4: Recepciones pendientes
SELECT
    'RECIBO_PENDIENTE' AS tipo_registro,
    rd.SKU AS sku,
    sk.DESCR AS descripcion,
    r.STORERKEY AS almacen,
    sk.INNERPACK AS inner_pack,
    NULL AS cubo_estandar,
    NULL AS peso_bruto,
    NULL AS peso_neto,
    NULL AS pack_key,
    NULL AS zona_putaway,
    NULL AS codigo_hazmat,
    r.STATUS AS status,
    r.ADDDATE AS fecha_creacion,
    r.EDITDATE AS fecha_modificacion,
    NULL AS ubicacion,
    rd.QTYEXPECTED - COALESCE(rd.QTYRECEIVED, 0) AS cantidad,
    r.RECEIPTKEY AS documento_ref  -- ASN número
FROM
    WMWHSE1.RECEIPT r
    INNER JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
    LEFT JOIN WMWHSE1.SKU sk ON rd.SKU = sk.SKU AND r.STORERKEY = sk.STORERKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND rd.SKU = '{{sku_numero}}'
    AND r.STATUS NOT IN ('10', '80', '95')  -- Pendientes
    AND rd.QTYEXPECTED > COALESCE(rd.QTYRECEIVED, 0)

ORDER BY
    tipo_registro,
    ubicacion;
