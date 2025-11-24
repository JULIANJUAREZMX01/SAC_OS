-- ═══════════════════════════════════════════════════════════════════════════════
-- QUERY: Mapeo de Tiendas por Circuito
-- Módulo: Control de Tráfico - CEDIS 427
-- ═══════════════════════════════════════════════════════════════════════════════
-- Descripción: Obtiene el mapeo de tiendas a circuitos para la asignación
-- automática de rutas de distribución.
--
-- Circuito 200: Zona Centro/Norte de Quintana Roo (Cancún, Playa del Carmen)
-- Circuito 201: Zona Sur de Quintana Roo (Chetumal, Bacalar)
-- Circuito 202: Zona Yucatán/Campeche (Mérida, Campeche)
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT
    s.STORERKEY AS codigo_tienda,
    s.COMPANY AS nombre_tienda,
    s.ADDRESS1 AS direccion,
    s.CITY AS ciudad,
    s.STATE AS estado,
    s.ZIP AS codigo_postal,
    CASE
        -- Circuito 200: Cancún y zona norte QRoo
        WHEN s.CITY IN ('CANCUN', 'CANCÚN', 'PLAYA DEL CARMEN', 'TULUM', 'PUERTO MORELOS', 'ISLA MUJERES', 'COZUMEL')
            THEN '200'
        -- Circuito 201: Zona sur QRoo
        WHEN s.CITY IN ('CHETUMAL', 'BACALAR', 'FELIPE CARRILLO PUERTO', 'JOSE MARIA MORELOS')
            THEN '201'
        -- Circuito 202: Yucatán y Campeche
        WHEN s.STATE IN ('YUCATAN', 'YUC', 'CAMPECHE', 'CAM')
            THEN '202'
        ELSE '200'  -- Default al circuito principal
    END AS circuito_asignado,
    s.SUSR1 AS zona_especial,
    s.SUSR2 AS ventana_entrega_inicio,
    s.SUSR3 AS ventana_entrega_fin
FROM
    WMWHSE1.STORER s
WHERE
    s.TYPE = 'CONSIGNEE'  -- Solo tiendas/consignatarios
    AND s.STORERKEY LIKE 'C%'  -- Formato de tiendas Chedraui
    AND s.STATUS = 'Y'  -- Solo activas
ORDER BY
    circuito_asignado,
    s.CITY,
    s.STORERKEY;
