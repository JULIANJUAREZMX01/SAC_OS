-- ============================================
-- NOMBRE: Auditoría de actividad de usuario
-- CATEGORÍA: bajo_demanda
-- FRECUENCIA: Bajo demanda
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Genera un reporte detallado de la actividad de un usuario
-- específico. Incluye tareas, transacciones, órdenes
-- procesadas y métricas de productividad.

-- TABLAS INVOLUCRADAS:
-- - USERPROFILE (Información de usuario)
-- - TASKDETAIL (Tareas ejecutadas)
-- - ITRN (Transacciones)
-- - ORDERS (Órdenes creadas/modificadas)

-- PARAMETROS:
-- {{usuario}} - Username del usuario
-- {{fecha_inicio}} - Fecha inicio del período
-- {{fecha_fin}} - Fecha fin del período

-- PARTE 1: Información del usuario
SELECT
    '01_PERFIL' AS seccion,
    u.USERKEY AS usuario_id,
    u.USERNAME AS username,
    u.FIRSTNAME AS nombre,
    u.LASTNAME AS apellido,
    u.USERGROUP AS grupo,
    u.STATUS AS status,
    CASE u.STATUS
        WHEN '0' THEN 'Activo'
        WHEN '1' THEN 'Inactivo'
        WHEN '9' THEN 'Bloqueado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    NULL AS fecha,
    NULL AS tipo_actividad,
    NULL AS cantidad,
    NULL AS detalle
FROM
    WMWHSE1.USERPROFILE u
WHERE
    u.USERNAME = '{{usuario}}'

UNION ALL

-- PARTE 2: Resumen de tareas por tipo
SELECT
    '02_RESUMEN_TAREAS' AS seccion,
    NULL AS usuario_id,
    '{{usuario}}' AS username,
    td.TASKTYPE AS nombre,
    NULL AS apellido,
    NULL AS grupo,
    NULL AS status,
    NULL AS status_descripcion,
    NULL AS fecha,
    td.TASKTYPE AS tipo_actividad,
    COUNT(*) AS cantidad,
    CONCAT('Total piezas: ', CAST(SUM(td.QTY) AS VARCHAR(20))) AS detalle
FROM
    WMWHSE1.TASKDETAIL td
WHERE
    td.USERKEY = '{{usuario}}'
    AND td.STATUS = '9'  -- Completadas
    AND DATE(td.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
GROUP BY
    td.TASKTYPE

UNION ALL

-- PARTE 3: Productividad diaria
SELECT
    '03_PRODUCTIVIDAD_DIARIA' AS seccion,
    NULL AS usuario_id,
    '{{usuario}}' AS username,
    CAST(DATE(td.ENDTIME) AS VARCHAR(10)) AS nombre,
    NULL AS apellido,
    NULL AS grupo,
    NULL AS status,
    NULL AS status_descripcion,
    DATE(td.ENDTIME) AS fecha,
    'TAREAS_DIA' AS tipo_actividad,
    COUNT(*) AS cantidad,
    CONCAT('Piezas: ', CAST(SUM(td.QTY) AS VARCHAR(20)), ' | Horas trabajo: ',
           CAST(ROUND(SUM(TIMESTAMPDIFF(MINUTE, td.STARTTIME, td.ENDTIME)) / 60.0, 2) AS VARCHAR(10))) AS detalle
FROM
    WMWHSE1.TASKDETAIL td
WHERE
    td.USERKEY = '{{usuario}}'
    AND td.STATUS = '9'
    AND DATE(td.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    AND td.STARTTIME IS NOT NULL
    AND td.ENDTIME IS NOT NULL
GROUP BY
    DATE(td.ENDTIME)

UNION ALL

-- PARTE 4: Últimas tareas ejecutadas
SELECT
    '04_ULTIMAS_TAREAS' AS seccion,
    NULL AS usuario_id,
    '{{usuario}}' AS username,
    td.TASKDETAILKEY AS nombre,
    td.TASKTYPE AS apellido,
    td.SKU AS grupo,
    td.STATUS AS status,
    td.FROMLOC AS status_descripcion,
    td.ENDTIME AS fecha,
    td.TASKTYPE AS tipo_actividad,
    td.QTY AS cantidad,
    CONCAT('OC: ', COALESCE(td.ORDERKEY, 'N/A'), ' | LPN: ', COALESCE(td.FROMLPN, 'N/A')) AS detalle
FROM
    WMWHSE1.TASKDETAIL td
WHERE
    td.USERKEY = '{{usuario}}'
    AND DATE(td.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
ORDER BY
    seccion,
    fecha DESC NULLS LAST
FETCH FIRST 100 ROWS ONLY;
