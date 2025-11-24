-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Expediciones Programadas del Día
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene todas las expediciones programadas para una fecha específica
-- por circuito, incluyendo tiendas destino y cantidad de tarimas
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
    o.ORDERKEY AS orden_key,
    o.EXTERNORDERKEY AS orden_externa,
    o.STORERKEY AS almacen_origen,
    o.CONSIGNEEKEY AS tienda_destino,
    o.TYPE AS tipo_orden,
    o.STATUS AS estado,
    o.SUSR1 AS circuito,
    o.SUSR2 AS compuerta_asignada,
    o.SUSR3 AS transportista,
    o.SUSR4 AS hora_programada,
    o.DOOR AS puerta_expedicion,
    o.ROUTE AS ruta,
    o.STOP_ AS secuencia_parada,
    o.TOTALQTY AS cantidad_total,
    o.ORDERDATE AS fecha_orden,
    o.DELIVERYDATE AS fecha_entrega_esperada,
    o.ACTUALSHIPDATE AS fecha_embarque_real,
    o.NOTES AS notas
FROM
    WMWHSE1.ORDERS o
WHERE
    o.STORERKEY = 'C427'
    AND DATE(o.DELIVERYDATE) = CURRENT DATE
    AND o.STATUS IN ('00', '04', '25', '55', '95')  -- En proceso, Picking, Embarque
ORDER BY
    o.SUSR1,  -- Por circuito
    o.ROUTE,
    o.STOP_;
