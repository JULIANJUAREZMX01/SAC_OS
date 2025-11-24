-- ============================================
-- STORED PROCEDURE: SP_GET_DAILY_REPORT
-- Generación de Reporte Diario de Planning
-- CATEGORÍA: DDL - Stored Procedure
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Procedimiento almacenado que genera datos para el
-- reporte diario de Planning. Consolida información
-- de OCs, distribuciones, ASNs y alertas.

-- PERMISOS REQUERIDOS:
-- CREATE PROCEDURE en schema WMWHSE1

-- PARÁMETROS:
-- p_storerkey: Código de almacén
-- p_fecha_reporte: Fecha del reporte (default: hoy)
-- p_tipo_reporte: 'RESUMEN' o 'DETALLE'

-- RETORNA:
-- Múltiples result sets con información del reporte

-- ============================================
-- SCRIPT DE CREACIÓN
-- ============================================

-- Eliminar procedimiento si existe
DROP PROCEDURE WMWHSE1.SP_GET_DAILY_REPORT;

-- Crear procedimiento
CREATE PROCEDURE WMWHSE1.SP_GET_DAILY_REPORT (
    IN p_storerkey VARCHAR(20),
    IN p_fecha_reporte DATE DEFAULT CURRENT_DATE,
    IN p_tipo_reporte VARCHAR(20) DEFAULT 'RESUMEN'
)
LANGUAGE SQL
DYNAMIC RESULT SETS 5
BEGIN
    -- Cursores para cada sección del reporte
    DECLARE cursor_resumen CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.REPORT_SUMMARY;

    DECLARE cursor_ocs CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.REPORT_OCS;

    DECLARE cursor_distros CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.REPORT_DISTROS;

    DECLARE cursor_asns CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.REPORT_ASNS;

    DECLARE cursor_alertas CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.REPORT_ALERTAS;

    -- ============================================
    -- SECCIÓN 1: RESUMEN EJECUTIVO
    -- ============================================

    DECLARE GLOBAL TEMPORARY TABLE SESSION.REPORT_SUMMARY (
        METRICA VARCHAR(100),
        VALOR INTEGER,
        PORCENTAJE DECIMAL(5,2),
        TENDENCIA VARCHAR(20)
    ) ON COMMIT DROP TABLE;

    INSERT INTO SESSION.REPORT_SUMMARY
    -- OCs del día
    SELECT 'OCs Creadas Hoy', COUNT(*), NULL, NULL
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND DATE(ADDDATE) = p_fecha_reporte
    AND ORDERTYPE IN ('PO', 'PURCHASE')

    UNION ALL

    -- OCs Pendientes
    SELECT 'OCs Pendientes Total', COUNT(*), NULL, NULL
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND STATUS IN ('0', '1', '2')
    AND ORDERTYPE IN ('PO', 'PURCHASE')

    UNION ALL

    -- OCs Vencidas
    SELECT 'OCs Vencidas', COUNT(*), NULL, 'ALERTA'
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND STATUS IN ('0', '1', '2')
    AND DELIVERYDATE < CURRENT_DATE
    AND ORDERTYPE IN ('PO', 'PURCHASE')

    UNION ALL

    -- ASNs Pendientes
    SELECT 'ASNs Pendientes de Recibo', COUNT(*), NULL, NULL
    FROM WMWHSE1.RECEIPT
    WHERE STORERKEY = p_storerkey
    AND STATUS NOT IN ('10', '80', '95')

    UNION ALL

    -- Distribuciones del día
    SELECT 'Distribuciones Creadas Hoy', COUNT(*), NULL, NULL
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND DATE(ADDDATE) = p_fecha_reporte
    AND ORDERTYPE IN ('DISTRO', 'SO', 'XD');

    -- ============================================
    -- SECCIÓN 2: ÓRDENES DE COMPRA
    -- ============================================

    DECLARE GLOBAL TEMPORARY TABLE SESSION.REPORT_OCS (
        OC_NUMERO VARCHAR(50),
        OC_EXTERNA VARCHAR(50),
        FECHA_ORDEN DATE,
        FECHA_ENTREGA DATE,
        STATUS VARCHAR(20),
        TOTAL_LINEAS INTEGER,
        QTY_PENDIENTE DECIMAL(15,2),
        ALERTA VARCHAR(50)
    ) ON COMMIT DROP TABLE;

    INSERT INTO SESSION.REPORT_OCS
    SELECT
        o.ORDERKEY,
        o.EXTERNORDERKEY,
        o.ORDERDATE,
        o.DELIVERYDATE,
        CASE o.STATUS
            WHEN '0' THEN 'Abierta'
            WHEN '1' THEN 'En Proceso'
            WHEN '2' THEN 'Parcial'
            ELSE o.STATUS
        END,
        COUNT(od.ORDERLINENUMBER),
        SUM(od.OPENQTY),
        CASE
            WHEN o.DELIVERYDATE < CURRENT_DATE THEN 'VENCIDA'
            WHEN o.DELIVERYDATE <= CURRENT_DATE + 3 DAYS THEN 'POR_VENCER'
            ELSE 'OK'
        END
    FROM WMWHSE1.ORDERS o
    LEFT JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE o.STORERKEY = p_storerkey
    AND o.STATUS IN ('0', '1', '2')
    AND o.ORDERTYPE IN ('PO', 'PURCHASE')
    GROUP BY o.ORDERKEY, o.EXTERNORDERKEY, o.ORDERDATE, o.DELIVERYDATE, o.STATUS
    ORDER BY o.DELIVERYDATE;

    -- ============================================
    -- SECCIÓN 3: DISTRIBUCIONES
    -- ============================================

    DECLARE GLOBAL TEMPORARY TABLE SESSION.REPORT_DISTROS (
        OC_REFERENCIA VARCHAR(50),
        TOTAL_TIENDAS INTEGER,
        TOTAL_DISTROS INTEGER,
        QTY_TOTAL DECIMAL(15,2),
        QTY_ENVIADA DECIMAL(15,2),
        PORCENTAJE_COMPLETADO DECIMAL(5,2)
    ) ON COMMIT DROP TABLE;

    INSERT INTO SESSION.REPORT_DISTROS
    SELECT
        o.EXTERNALORDERKEY2,
        COUNT(DISTINCT o.CONSIGNEEKEY),
        COUNT(DISTINCT o.ORDERKEY),
        SUM(od.ORIGINALQTY),
        SUM(od.SHIPPEDQTY),
        CASE
            WHEN SUM(od.ORIGINALQTY) > 0 THEN
                ROUND((SUM(od.SHIPPEDQTY) / SUM(od.ORIGINALQTY)) * 100, 2)
            ELSE 0
        END
    FROM WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    WHERE o.STORERKEY = p_storerkey
    AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
    AND o.STATUS NOT IN ('95')
    AND DATE(o.ADDDATE) >= p_fecha_reporte - 7 DAYS
    GROUP BY o.EXTERNALORDERKEY2
    ORDER BY o.EXTERNALORDERKEY2;

    -- ============================================
    -- SECCIÓN 4: ASN/RECIBOS
    -- ============================================

    DECLARE GLOBAL TEMPORARY TABLE SESSION.REPORT_ASNS (
        ASN_NUMERO VARCHAR(50),
        OC_RELACIONADA VARCHAR(50),
        FECHA_ESPERADA DATE,
        STATUS VARCHAR(20),
        QTY_ESPERADA DECIMAL(15,2),
        QTY_RECIBIDA DECIMAL(15,2),
        DIAS_EN_PROCESO INTEGER
    ) ON COMMIT DROP TABLE;

    INSERT INTO SESSION.REPORT_ASNS
    SELECT
        r.RECEIPTKEY,
        r.POKEY,
        r.EXPECTEDRECEIPTDATE,
        CASE r.STATUS
            WHEN '0' THEN 'Creado'
            WHEN '5' THEN 'En Tránsito'
            WHEN '9' THEN 'Parcial'
            ELSE r.STATUS
        END,
        SUM(rd.QTYEXPECTED),
        SUM(COALESCE(rd.QTYRECEIVED, 0)),
        DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE)
    FROM WMWHSE1.RECEIPT r
    LEFT JOIN WMWHSE1.RECEIPTDETAIL rd ON r.RECEIPTKEY = rd.RECEIPTKEY
    WHERE r.STORERKEY = p_storerkey
    AND r.STATUS NOT IN ('10', '80', '95')
    GROUP BY r.RECEIPTKEY, r.POKEY, r.EXPECTEDRECEIPTDATE, r.STATUS, r.ADDDATE
    ORDER BY r.EXPECTEDRECEIPTDATE;

    -- ============================================
    -- SECCIÓN 5: ALERTAS Y ERRORES
    -- ============================================

    DECLARE GLOBAL TEMPORARY TABLE SESSION.REPORT_ALERTAS (
        TIPO_ALERTA VARCHAR(50),
        SEVERIDAD VARCHAR(20),
        CANTIDAD INTEGER,
        DESCRIPCION VARCHAR(200)
    ) ON COMMIT DROP TABLE;

    INSERT INTO SESSION.REPORT_ALERTAS
    -- OCs vencidas
    SELECT 'OC_VENCIDA', 'CRITICO', COUNT(*),
           'Órdenes de compra con fecha de entrega vencida'
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND STATUS IN ('0', '1', '2')
    AND DELIVERYDATE < CURRENT_DATE
    AND ORDERTYPE IN ('PO', 'PURCHASE')
    HAVING COUNT(*) > 0

    UNION ALL

    -- OCs por vencer
    SELECT 'OC_POR_VENCER', 'ALTO', COUNT(*),
           'Órdenes próximas a vencer en los próximos 3 días'
    FROM WMWHSE1.ORDERS
    WHERE STORERKEY = p_storerkey
    AND STATUS IN ('0', '1', '2')
    AND DELIVERYDATE BETWEEN CURRENT_DATE AND CURRENT_DATE + 3 DAYS
    AND ORDERTYPE IN ('PO', 'PURCHASE')
    HAVING COUNT(*) > 0

    UNION ALL

    -- ASNs estancados
    SELECT 'ASN_ESTANCADO', 'MEDIO', COUNT(*),
           'ASN sin movimiento por más de 3 días'
    FROM WMWHSE1.RECEIPT
    WHERE STORERKEY = p_storerkey
    AND STATUS NOT IN ('10', '80', '95')
    AND DATEDIFF(DAY, COALESCE(EDITDATE, ADDDATE), CURRENT_DATE) > 3
    HAVING COUNT(*) > 0;

    -- ============================================
    -- ABRIR CURSORES
    -- ============================================

    OPEN cursor_resumen;
    OPEN cursor_ocs;
    OPEN cursor_distros;
    OPEN cursor_asns;
    OPEN cursor_alertas;

END;

-- ============================================
-- GRANT DE PERMISOS
-- ============================================

GRANT EXECUTE ON PROCEDURE WMWHSE1.SP_GET_DAILY_REPORT TO PUBLIC;

-- ============================================
-- EJEMPLO DE USO
-- ============================================

-- Reporte del día actual
-- CALL WMWHSE1.SP_GET_DAILY_REPORT('C22', CURRENT_DATE, 'RESUMEN');

-- Reporte de fecha específica
-- CALL WMWHSE1.SP_GET_DAILY_REPORT('C22', '2025-11-21', 'DETALLE');
