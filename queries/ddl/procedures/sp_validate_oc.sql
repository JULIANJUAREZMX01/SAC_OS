-- ============================================
-- STORED PROCEDURE: SP_VALIDATE_OC
-- Validación de Orden de Compra vs Distribuciones
-- CATEGORÍA: DDL - Stored Procedure
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Procedimiento almacenado que valida una OC contra sus
-- distribuciones. Retorna errores y advertencias encontradas.

-- PERMISOS REQUERIDOS:
-- CREATE PROCEDURE en schema WMWHSE1

-- PARÁMETROS:
-- p_oc_numero: Número de la OC a validar
-- p_storerkey: Código de almacén

-- RETORNA:
-- Tabla de resultados con errores y advertencias

-- ============================================
-- SCRIPT DE CREACIÓN
-- ============================================

-- Eliminar procedimiento si existe
DROP PROCEDURE WMWHSE1.SP_VALIDATE_OC;

-- Crear procedimiento
CREATE PROCEDURE WMWHSE1.SP_VALIDATE_OC (
    IN p_oc_numero VARCHAR(50),
    IN p_storerkey VARCHAR(20)
)
LANGUAGE SQL
DYNAMIC RESULT SETS 1
BEGIN
    -- Variables locales
    DECLARE v_oc_exists INTEGER DEFAULT 0;
    DECLARE v_oc_status VARCHAR(10);
    DECLARE v_total_oc_qty DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_distro_qty DECIMAL(15,2) DEFAULT 0;

    -- Cursor para resultados
    DECLARE result_cursor CURSOR WITH RETURN FOR
        SELECT * FROM SESSION.VALIDATION_RESULTS;

    -- Crear tabla temporal para resultados
    DECLARE GLOBAL TEMPORARY TABLE SESSION.VALIDATION_RESULTS (
        TIPO_ERROR VARCHAR(50),
        SEVERIDAD VARCHAR(20),
        SKU VARCHAR(50),
        MENSAJE VARCHAR(500),
        DETALLE VARCHAR(1000),
        QTY_OC DECIMAL(15,2),
        QTY_DISTRO DECIMAL(15,2),
        DIFERENCIA DECIMAL(15,2)
    ) ON COMMIT DROP TABLE;

    -- Verificar si la OC existe
    SELECT COUNT(*) INTO v_oc_exists
    FROM WMWHSE1.ORDERS
    WHERE (ORDERKEY = p_oc_numero OR EXTERNORDERKEY = p_oc_numero)
    AND STORERKEY = p_storerkey;

    IF v_oc_exists = 0 THEN
        INSERT INTO SESSION.VALIDATION_RESULTS
        VALUES (
            'OC_NO_EXISTE',
            'CRITICO',
            NULL,
            'La orden de compra no existe en el sistema',
            CONCAT('OC buscada: ', p_oc_numero, ' en almacén ', p_storerkey),
            0, 0, 0
        );
    ELSE
        -- Obtener status de la OC
        SELECT STATUS INTO v_oc_status
        FROM WMWHSE1.ORDERS
        WHERE (ORDERKEY = p_oc_numero OR EXTERNORDERKEY = p_oc_numero)
        AND STORERKEY = p_storerkey
        FETCH FIRST 1 ROW ONLY;

        -- Validar status
        IF v_oc_status = '95' THEN
            INSERT INTO SESSION.VALIDATION_RESULTS
            VALUES (
                'OC_CANCELADA',
                'ALTO',
                NULL,
                'La orden de compra está cancelada',
                'Las distribuciones relacionadas deben verificarse',
                0, 0, 0
            );
        END IF;

        -- Validar excedentes por SKU (distribución > OC)
        INSERT INTO SESSION.VALIDATION_RESULTS
        SELECT
            'EXCEDENTE' AS TIPO_ERROR,
            'CRITICO' AS SEVERIDAD,
            oc.SKU,
            CONCAT('SKU ', oc.SKU, ' tiene distribución excedente') AS MENSAJE,
            CONCAT('Distribuido ', ds.qty_distro, ' vs OC ', oc.qty_oc) AS DETALLE,
            oc.qty_oc AS QTY_OC,
            ds.qty_distro AS QTY_DISTRO,
            ds.qty_distro - oc.qty_oc AS DIFERENCIA
        FROM (
            SELECT od.SKU, SUM(od.ORIGINALQTY) AS qty_oc
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE (o.ORDERKEY = p_oc_numero OR o.EXTERNORDERKEY = p_oc_numero)
            AND o.STORERKEY = p_storerkey
            GROUP BY od.SKU
        ) oc
        LEFT JOIN (
            SELECT od.SKU, SUM(od.ORIGINALQTY) AS qty_distro
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE o.EXTERNALORDERKEY2 = p_oc_numero
            AND o.STORERKEY = p_storerkey
            AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
            AND o.STATUS != '95'
            GROUP BY od.SKU
        ) ds ON oc.SKU = ds.SKU
        WHERE ds.qty_distro > oc.qty_oc;

        -- Validar incompletas por SKU (distribución < OC significativamente)
        INSERT INTO SESSION.VALIDATION_RESULTS
        SELECT
            'INCOMPLETA' AS TIPO_ERROR,
            CASE
                WHEN ((oc.qty_oc - COALESCE(ds.qty_distro, 0)) / oc.qty_oc) > 0.5 THEN 'ALTO'
                ELSE 'MEDIO'
            END AS SEVERIDAD,
            oc.SKU,
            CONCAT('SKU ', oc.SKU, ' tiene distribución incompleta') AS MENSAJE,
            CONCAT('Distribuido ', COALESCE(ds.qty_distro, 0), ' de ', oc.qty_oc,
                   ' (', ROUND(((oc.qty_oc - COALESCE(ds.qty_distro, 0)) / oc.qty_oc) * 100, 2), '% pendiente)') AS DETALLE,
            oc.qty_oc AS QTY_OC,
            COALESCE(ds.qty_distro, 0) AS QTY_DISTRO,
            oc.qty_oc - COALESCE(ds.qty_distro, 0) AS DIFERENCIA
        FROM (
            SELECT od.SKU, SUM(od.ORIGINALQTY) AS qty_oc
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE (o.ORDERKEY = p_oc_numero OR o.EXTERNORDERKEY = p_oc_numero)
            AND o.STORERKEY = p_storerkey
            GROUP BY od.SKU
        ) oc
        LEFT JOIN (
            SELECT od.SKU, SUM(od.ORIGINALQTY) AS qty_distro
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE o.EXTERNALORDERKEY2 = p_oc_numero
            AND o.STORERKEY = p_storerkey
            AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
            AND o.STATUS != '95'
            GROUP BY od.SKU
        ) ds ON oc.SKU = ds.SKU
        WHERE COALESCE(ds.qty_distro, 0) < oc.qty_oc
        AND ((oc.qty_oc - COALESCE(ds.qty_distro, 0)) / oc.qty_oc) >= 0.05;  -- 5% o más

        -- Validar SKUs sin distribución
        INSERT INTO SESSION.VALIDATION_RESULTS
        SELECT
            'SIN_DISTRIBUCION' AS TIPO_ERROR,
            'ALTO' AS SEVERIDAD,
            oc.SKU,
            CONCAT('SKU ', oc.SKU, ' no tiene distribuciones asignadas') AS MENSAJE,
            CONCAT('Cantidad en OC: ', oc.qty_oc, ' sin asignar a tiendas') AS DETALLE,
            oc.qty_oc AS QTY_OC,
            0 AS QTY_DISTRO,
            oc.qty_oc AS DIFERENCIA
        FROM (
            SELECT od.SKU, SUM(od.ORIGINALQTY) AS qty_oc
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE (o.ORDERKEY = p_oc_numero OR o.EXTERNORDERKEY = p_oc_numero)
            AND o.STORERKEY = p_storerkey
            GROUP BY od.SKU
        ) oc
        LEFT JOIN (
            SELECT DISTINCT od.SKU
            FROM WMWHSE1.ORDERS o
            INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
            WHERE o.EXTERNALORDERKEY2 = p_oc_numero
            AND o.STORERKEY = p_storerkey
            AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')
            AND o.STATUS != '95'
        ) ds ON oc.SKU = ds.SKU
        WHERE ds.SKU IS NULL;

    END IF;

    -- Abrir cursor con resultados
    OPEN result_cursor;

END;

-- ============================================
-- GRANT DE PERMISOS
-- ============================================

GRANT EXECUTE ON PROCEDURE WMWHSE1.SP_VALIDATE_OC TO PUBLIC;

-- ============================================
-- EJEMPLO DE USO
-- ============================================

-- CALL WMWHSE1.SP_VALIDATE_OC('C750384123456', 'C22');
