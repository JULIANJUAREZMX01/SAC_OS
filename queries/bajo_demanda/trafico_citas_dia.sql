-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Citas de Tráfico del Día
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene todas las citas programadas para una fecha específica
-- incluyendo información del ASN, transportista y estado actual
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
    a.EXTERNRECEIPTKEY AS numero_asn,
    a.RECEIPTKEY AS receipt_key,
    a.WHSEID AS almacen,
    a.TYPE AS tipo_recibo,
    a.STATUS AS estado,
    a.SUSR1 AS transportista_nombre,
    a.SUSR2 AS transportista_placas,
    a.SUSR3 AS tipo_vehiculo,
    a.SUSR4 AS compuerta_asignada,
    a.SUSR5 AS circuito,
    a.EXPECTEDRECEIPTDATE AS fecha_esperada,
    a.RECEIPTDATE AS fecha_recibo_real,
    a.OPENQTY AS cantidad_pendiente,
    a.TOTALQTY AS cantidad_total,
    a.ADDDATE AS fecha_creacion,
    a.ADDWHO AS creado_por,
    a.EDITDATE AS ultima_modificacion,
    a.NOTES AS notas
FROM
    WMWHSE1.RECEIPT a
WHERE
    a.WHSEID = 'WM260BASD'
    AND DATE(a.EXPECTEDRECEIPTDATE) = CURRENT DATE
    AND a.STATUS IN ('0', '5', '9', '11')  -- Nuevo, En proceso, Recibiendo, Completado
ORDER BY
    a.EXPECTEDRECEIPTDATE,
    a.STATUS;
