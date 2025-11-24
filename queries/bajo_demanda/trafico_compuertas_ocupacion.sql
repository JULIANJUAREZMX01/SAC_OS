-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Ocupación de Compuertas
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene el estado actual de ocupación de las compuertas
-- incluyendo qué ASN/Expedición está en cada compuerta
-- ═══════════════════════════════════════════════════════════════════════════════

-- Compuertas de RECIBO (1-20)
SELECT
    d.DOOR AS compuerta,
    'RECIBO' AS tipo,
    COALESCE(r.EXTERNRECEIPTKEY, 'DISPONIBLE') AS asn_actual,
    r.STATUS AS estado_asn,
    r.SUSR1 AS transportista,
    r.SUSR2 AS placas,
    r.OPENQTY AS cantidad_pendiente,
    r.ADDDATE AS hora_inicio
FROM
    WMWHSE1.DOOR d
LEFT JOIN
    WMWHSE1.RECEIPT r ON d.DOOR = r.SUSR4
    AND r.STATUS IN ('5', '9')  -- En proceso o recibiendo
WHERE
    d.DOORTYPE = 'R'  -- Tipo Recibo
    AND d.WHSEID = 'WM260BASD'

UNION ALL

-- Compuertas de EXPEDICIÓN (21-40)
SELECT
    d.DOOR AS compuerta,
    'EXPEDICION' AS tipo,
    COALESCE(o.EXTERNORDERKEY, 'DISPONIBLE') AS orden_actual,
    o.STATUS AS estado_orden,
    o.SUSR3 AS transportista,
    '' AS placas,
    o.TOTALQTY AS cantidad,
    o.ACTUALSHIPDATE AS hora_inicio
FROM
    WMWHSE1.DOOR d
LEFT JOIN
    WMWHSE1.ORDERS o ON d.DOOR = o.DOOR
    AND o.STATUS IN ('25', '55')  -- En carga o listo para embarque
WHERE
    d.DOORTYPE = 'S'  -- Tipo Shipping
    AND d.WHSEID = 'WM260BASD'

ORDER BY
    compuerta;
