-- ============================================
-- NOMBRE: Historial completo de una OC
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene el historial completo de una OC, incluyendo
-- todas las transacciones, cambios de estado, distribuciones
-- relacionadas, ASNs y actividad de picking/packing.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)
-- - ORDERSTATUSHISTORY (Historial de estados)
-- - ITRN (Transacciones de inventario)
-- - TASKDETAIL (Tareas ejecutadas)

-- PARAMETROS:
-- {{oc_numero}} - Número de OC
-- {{storerkey}} - Código de almacén (default: C22)

-- PARTE 1: Información actual de la OC
SELECT
    '01_CABECERA' AS seccion,
    o.ORDERKEY AS referencia,
    NULL AS linea,
    o.STATUS AS status,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS descripcion,
    o.ADDDATE AS fecha,
    o.ADDWHO AS usuario,
    'Creación de OC' AS tipo_evento,
    NULL AS qty,
    o.NOTES AS detalle
FROM
    WMWHSE1.ORDERS o
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.ORDERKEY = '{{oc_numero}}'

UNION ALL

-- PARTE 2: Líneas de detalle
SELECT
    '02_DETALLE' AS seccion,
    od.ORDERKEY AS referencia,
    CAST(od.ORDERLINENUMBER AS VARCHAR(10)) AS linea,
    od.STATUS AS status,
    od.SKU AS descripcion,
    od.ADDDATE AS fecha,
    od.ADDWHO AS usuario,
    'Línea de OC' AS tipo_evento,
    od.ORIGINALQTY AS qty,
    CONCAT('Pendiente: ', CAST(od.OPENQTY AS VARCHAR(20)), ' | Enviado: ', CAST(od.SHIPPEDQTY AS VARCHAR(20))) AS detalle
FROM
    WMWHSE1.ORDERDETAIL od
WHERE
    od.ORDERKEY = '{{oc_numero}}'

UNION ALL

-- PARTE 3: Distribuciones relacionadas
SELECT
    '03_DISTRIBUCIONES' AS seccion,
    dist.ORDERKEY AS referencia,
    dist.CONSIGNEEKEY AS linea,  -- Tienda destino
    dist.STATUS AS status,
    CASE dist.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '9' THEN 'Completada'
        ELSE dist.STATUS
    END AS descripcion,
    dist.ADDDATE AS fecha,
    dist.ADDWHO AS usuario,
    'Distribución a tienda' AS tipo_evento,
    SUM(dd.ORIGINALQTY) AS qty,
    CONCAT('Tienda: ', dist.CONSIGNEEKEY) AS detalle
FROM
    WMWHSE1.ORDERS dist
    INNER JOIN WMWHSE1.ORDERDETAIL dd ON dist.ORDERKEY = dd.ORDERKEY
WHERE
    dist.STORERKEY = '{{storerkey}}'
    AND dist.EXTERNALORDERKEY2 = '{{oc_numero}}'  -- Referencia a OC original
    AND dist.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
GROUP BY
    dist.ORDERKEY,
    dist.CONSIGNEEKEY,
    dist.STATUS,
    dist.ADDDATE,
    dist.ADDWHO

UNION ALL

-- PARTE 4: ASNs relacionados
SELECT
    '04_ASN' AS seccion,
    r.RECEIPTKEY AS referencia,
    r.EXTERNRECEIPTKEY AS linea,
    r.STATUS AS status,
    CASE r.STATUS
        WHEN '0' THEN 'Creado'
        WHEN '5' THEN 'En Tránsito'
        WHEN '10' THEN 'Recibido'
        WHEN '80' THEN 'Cerrado'
        ELSE r.STATUS
    END AS descripcion,
    r.ADDDATE AS fecha,
    r.ADDWHO AS usuario,
    'ASN/Recibo' AS tipo_evento,
    SUM(rd.QTYRECEIVED) AS qty,
    CONCAT('Esperado: ', CAST(SUM(rd.QTYEXPECTED) AS VARCHAR(20))) AS detalle
FROM
    WMWHSE1.RECEIPT r
    INNER JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
WHERE
    r.STORERKEY = '{{storerkey}}'
    AND r.POKEY = '{{oc_numero}}'
GROUP BY
    r.RECEIPTKEY,
    r.EXTERNRECEIPTKEY,
    r.STATUS,
    r.ADDDATE,
    r.ADDWHO

UNION ALL

-- PARTE 5: Tareas ejecutadas (picking/packing)
SELECT
    '05_TAREAS' AS seccion,
    td.ORDERKEY AS referencia,
    td.TASKDETAILKEY AS linea,
    td.STATUS AS status,
    td.TASKTYPE AS descripcion,
    td.ENDTIME AS fecha,
    td.USERKEY AS usuario,
    CONCAT('Tarea: ', td.TASKTYPE) AS tipo_evento,
    td.QTY AS qty,
    CONCAT('Desde: ', td.FROMLOC, ' | Hacia: ', td.TOLOC) AS detalle
FROM
    WMWHSE1.TASKDETAIL td
WHERE
    td.ORDERKEY = '{{oc_numero}}'
    AND td.STATUS = '9'  -- Completadas

ORDER BY
    seccion,
    fecha DESC;
