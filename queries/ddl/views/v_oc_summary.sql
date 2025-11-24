-- ============================================
-- VISTA: V_OC_SUMMARY
-- Resumen de Órdenes de Compra
-- CATEGORÍA: DDL - Vista
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Vista que proporciona un resumen consolidado de todas
-- las órdenes de compra con métricas calculadas.
-- Optimiza consultas frecuentes del sistema SAC.

-- PERMISOS REQUERIDOS:
-- CREATE VIEW en schema WMWHSE1

-- DEPENDENCIAS:
-- - WMWHSE1.ORDERS
-- - WMWHSE1.ORDERDETAIL
-- - WMWHSE1.SKU

-- ============================================
-- SCRIPT DE CREACIÓN
-- ============================================

-- Eliminar vista si existe
DROP VIEW WMWHSE1.V_OC_SUMMARY;

-- Crear vista
CREATE VIEW WMWHSE1.V_OC_SUMMARY AS
SELECT
    -- Identificadores
    o.ORDERKEY AS OC_NUMERO,
    o.EXTERNORDERKEY AS OC_EXTERNA,
    o.STORERKEY AS ALMACEN,

    -- Tipo y clasificación
    o.ORDERTYPE AS TIPO_ORDEN,
    CASE o.ORDERTYPE
        WHEN 'PO' THEN 'Orden de Compra'
        WHEN 'PURCHASE' THEN 'Compra'
        WHEN 'DISTRO' THEN 'Distribución'
        WHEN 'SO' THEN 'Salida'
        WHEN 'XD' THEN 'Cross-Dock'
        ELSE 'Otro'
    END AS TIPO_DESCRIPCION,

    -- Fechas
    o.ORDERDATE AS FECHA_ORDEN,
    o.DELIVERYDATE AS FECHA_ENTREGA,
    o.ADDDATE AS FECHA_CREACION,
    o.EDITDATE AS FECHA_MODIFICACION,

    -- Estado
    o.STATUS AS STATUS_CODE,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS STATUS_DESCRIPCION,

    -- Métricas agregadas
    COUNT(DISTINCT od.ORDERLINENUMBER) AS TOTAL_LINEAS,
    COUNT(DISTINCT od.SKU) AS TOTAL_SKUS,
    SUM(od.ORIGINALQTY) AS QTY_ORIGINAL_TOTAL,
    SUM(od.OPENQTY) AS QTY_PENDIENTE_TOTAL,
    SUM(od.SHIPPEDQTY) AS QTY_ENVIADA_TOTAL,
    SUM(od.QTYALLOCATED) AS QTY_ASIGNADA_TOTAL,
    SUM(od.QTYPICKED) AS QTY_PICKEADA_TOTAL,

    -- Porcentajes calculados
    CASE
        WHEN SUM(od.ORIGINALQTY) > 0 THEN
            ROUND((SUM(od.SHIPPEDQTY) / SUM(od.ORIGINALQTY)) * 100, 2)
        ELSE 0
    END AS PORCENTAJE_COMPLETADO,

    CASE
        WHEN SUM(od.ORIGINALQTY) > 0 THEN
            ROUND((SUM(od.OPENQTY) / SUM(od.ORIGINALQTY)) * 100, 2)
        ELSE 0
    END AS PORCENTAJE_PENDIENTE,

    -- Indicadores de alerta
    CASE
        WHEN o.STATUS IN ('0', '1', '2') AND o.DELIVERYDATE < CURRENT_DATE THEN 'VENCIDA'
        WHEN o.STATUS IN ('0', '1', '2') AND o.DELIVERYDATE <= CURRENT_DATE + 3 DAYS THEN 'POR_VENCER'
        WHEN o.STATUS = '95' THEN 'CANCELADA'
        WHEN o.STATUS = '9' THEN 'COMPLETADA'
        ELSE 'NORMAL'
    END AS INDICADOR_ALERTA,

    -- Días en proceso
    DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) AS DIAS_DESDE_CREACION,

    -- Auditoría
    o.ADDWHO AS CREADO_POR,
    o.EDITWHO AS MODIFICADO_POR,
    o.NOTES AS NOTAS

FROM
    WMWHSE1.ORDERS o
    LEFT JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
WHERE
    o.ORDERTYPE IN ('PO', 'PURCHASE')  -- Solo OCs, no distribuciones

GROUP BY
    o.ORDERKEY,
    o.EXTERNORDERKEY,
    o.STORERKEY,
    o.ORDERTYPE,
    o.ORDERDATE,
    o.DELIVERYDATE,
    o.ADDDATE,
    o.EDITDATE,
    o.STATUS,
    o.ADDWHO,
    o.EDITWHO,
    o.NOTES;

-- ============================================
-- GRANT DE PERMISOS
-- ============================================

-- Permisos de lectura para usuarios del sistema
GRANT SELECT ON WMWHSE1.V_OC_SUMMARY TO PUBLIC;

-- ============================================
-- COMENTARIOS
-- ============================================

COMMENT ON TABLE WMWHSE1.V_OC_SUMMARY IS 'Vista de resumen de Órdenes de Compra - Sistema SAC';
COMMENT ON COLUMN WMWHSE1.V_OC_SUMMARY.OC_NUMERO IS 'Número interno de la OC';
COMMENT ON COLUMN WMWHSE1.V_OC_SUMMARY.PORCENTAJE_COMPLETADO IS 'Porcentaje de cantidad enviada vs original';
COMMENT ON COLUMN WMWHSE1.V_OC_SUMMARY.INDICADOR_ALERTA IS 'Estado de alerta: VENCIDA, POR_VENCER, COMPLETADA, CANCELADA, NORMAL';
