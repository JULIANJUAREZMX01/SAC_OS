-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Histórico de Tiempos de Operación
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene el histórico de tiempos de operación para alimentar
-- el modelo de aprendizaje automático. Incluye tiempos por transportista,
-- compuerta y tipo de operación.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Histórico de RECIBOS (últimos 30 días)
SELECT
    'RECIBO' AS tipo_operacion,
    r.EXTERNRECEIPTKEY AS referencia,
    r.SUSR1 AS transportista,
    r.SUSR4 AS compuerta,
    r.SUSR3 AS tipo_vehiculo,
    r.TOTALQTY AS cantidad_total,
    TIMESTAMPDIFF(4, CHAR(r.RECEIPTDATE - r.ADDDATE)) AS tiempo_total_minutos,
    DATE(r.ADDDATE) AS fecha,
    HOUR(r.ADDDATE) AS hora_inicio,
    DAYOFWEEK(r.ADDDATE) AS dia_semana,
    r.STATUS AS estado_final
FROM
    WMWHSE1.RECEIPT r
WHERE
    r.WHSEID = 'WM260BASD'
    AND r.STATUS = '11'  -- Completados
    AND r.RECEIPTDATE IS NOT NULL
    AND r.ADDDATE >= CURRENT DATE - 30 DAYS
ORDER BY
    r.ADDDATE DESC
FETCH FIRST 500 ROWS ONLY;
