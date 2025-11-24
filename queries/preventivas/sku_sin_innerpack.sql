-- ============================================
-- NOMBRE: SKUs sin Inner Pack configurado
-- CATEGORÍA: preventiva
-- FRECUENCIA: Semanal
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica SKUs que no tienen configurado el Inner Pack (IP)
-- o tienen valores inválidos. El Inner Pack es crítico para
-- cálculos de distribución y generación de reportes.

-- TABLAS INVOLUCRADAS:
-- - SKU (Maestro de productos)
-- - ORDERDETAIL (Para identificar SKUs activos)
-- - RECEIPTDETAIL (Para identificar SKUs con recibo reciente)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_actividad}} - Días de actividad reciente para considerar (default: 90)

WITH SKU_Activos AS (
    -- SKUs con actividad en órdenes recientes
    SELECT DISTINCT od.SKU
    FROM WMWHSE1.ORDERDETAIL od
    INNER JOIN WMWHSE1.ORDERS o ON od.ORDERKEY = o.ORDERKEY
    WHERE o.STORERKEY = '{{storerkey}}'
    AND DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) <= {{dias_actividad}}

    UNION

    -- SKUs con recibo reciente
    SELECT DISTINCT rd.SKU
    FROM WMWHSE1.RECEIPTDETAIL rd
    INNER JOIN WMWHSE1.RECEIPT r ON rd.RECEIPTKEY = r.RECEIPTKEY
    WHERE r.STORERKEY = '{{storerkey}}'
    AND DATEDIFF(DAY, r.ADDDATE, CURRENT_DATE) <= {{dias_actividad}}
)
SELECT
    s.SKU AS sku,
    s.DESCR AS descripcion,
    s.STORERKEY AS almacen,
    s.INNERPACK AS inner_pack_actual,
    s.STDCUBE AS cubo_estandar,
    s.STDGROSSWGT AS peso_bruto,
    s.STDNETWGT AS peso_neto,
    s.PACKKEY AS pack_key,
    s.ADDDATE AS fecha_creacion,
    s.EDITDATE AS fecha_modificacion,
    CASE
        WHEN s.INNERPACK IS NULL THEN 'Sin configurar'
        WHEN s.INNERPACK <= 0 THEN 'Valor inválido (<=0)'
        WHEN s.INNERPACK = 1 THEN 'IP=1 (verificar)'
        ELSE 'OK'
    END AS estado_innerpack,
    CASE
        WHEN s.INNERPACK IS NULL OR s.INNERPACK <= 0 THEN 'ALTO'
        WHEN s.INNERPACK = 1 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS prioridad_correccion,
    'Configurar Inner Pack correcto en maestro de SKU' AS accion_sugerida
FROM
    WMWHSE1.SKU s
    INNER JOIN SKU_Activos sa ON s.SKU = sa.SKU
WHERE
    s.STORERKEY = '{{storerkey}}'
    AND (
        s.INNERPACK IS NULL
        OR s.INNERPACK <= 0
        OR s.INNERPACK = 1  -- IP=1 puede ser error de configuración
    )
ORDER BY
    prioridad_correccion ASC,
    s.DESCR;
