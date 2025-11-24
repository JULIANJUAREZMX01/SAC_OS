-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Expediciones por Circuito
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene las expediciones agrupadas por circuito (200, 201, 202)
-- para el día actual, con resumen de tiendas y cantidades.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Resumen por circuito
SELECT
    COALESCE(o.SUSR1, '200') AS circuito,
    COUNT(DISTINCT o.ORDERKEY) AS total_ordenes,
    COUNT(DISTINCT o.CONSIGNEEKEY) AS total_tiendas,
    SUM(o.TOTALQTY) AS cantidad_total_items,
    COUNT(DISTINCT o.ROUTE) AS rutas,
    MIN(o.SUSR4) AS primera_salida,
    MAX(o.SUSR4) AS ultima_salida
FROM
    WMWHSE1.ORDERS o
WHERE
    o.STORERKEY = 'C427'
    AND DATE(o.DELIVERYDATE) = CURRENT DATE
    AND o.STATUS NOT IN ('99', '100')  -- Excluir canceladas/completadas
GROUP BY
    COALESCE(o.SUSR1, '200')
ORDER BY
    circuito;
