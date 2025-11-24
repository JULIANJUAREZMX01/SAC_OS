-- ============================================
-- NOMBRE: Usuarios sin actividad reciente
-- CATEGORÍA: preventiva
-- FRECUENCIA: Semanal
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Identifica usuarios del sistema que no han tenido actividad
-- en un período determinado. Útil para auditoría de seguridad
-- y limpieza de cuentas inactivas.

-- TABLAS INVOLUCRADAS:
-- - USERPROFILE (Perfiles de usuario)
-- - TASKDETAIL (Registro de tareas/actividades)

-- PARAMETROS:
-- {{dias_inactividad}} - Días sin actividad para considerar inactivo (default: 30)
-- {{incluir_deshabilitados}} - Incluir usuarios deshabilitados (default: 0)

WITH Ultima_Actividad AS (
    -- Obtener última actividad de cada usuario
    SELECT
        td.ADDWHO AS usuario,
        MAX(td.ADDDATE) AS ultima_actividad,
        COUNT(*) AS total_tareas_historico
    FROM
        WMWHSE1.TASKDETAIL td
    GROUP BY
        td.ADDWHO
)
SELECT
    u.USERKEY AS usuario_id,
    u.USERNAME AS nombre_usuario,
    u.FIRSTNAME AS nombre,
    u.LASTNAME AS apellido,
    u.EMAIL AS correo,
    u.USERGROUP AS grupo,
    u.ADDDATE AS fecha_creacion,
    u.EDITDATE AS ultima_modificacion,
    u.STATUS AS status,
    CASE u.STATUS
        WHEN '0' THEN 'Activo'
        WHEN '1' THEN 'Inactivo'
        WHEN '9' THEN 'Bloqueado'
        ELSE 'Desconocido'
    END AS status_descripcion,
    ua.ultima_actividad,
    COALESCE(ua.total_tareas_historico, 0) AS tareas_historico,
    DATEDIFF(DAY, COALESCE(ua.ultima_actividad, u.ADDDATE), CURRENT_DATE) AS dias_sin_actividad,
    CASE
        WHEN DATEDIFF(DAY, COALESCE(ua.ultima_actividad, u.ADDDATE), CURRENT_DATE) > 90 THEN 'CRITICO'
        WHEN DATEDIFF(DAY, COALESCE(ua.ultima_actividad, u.ADDDATE), CURRENT_DATE) > 60 THEN 'ALTO'
        WHEN DATEDIFF(DAY, COALESCE(ua.ultima_actividad, u.ADDDATE), CURRENT_DATE) > 30 THEN 'MEDIO'
        ELSE 'BAJO'
    END AS nivel_inactividad,
    CASE
        WHEN ua.ultima_actividad IS NULL THEN 'Usuario nunca ha operado'
        WHEN DATEDIFF(DAY, ua.ultima_actividad, CURRENT_DATE) > 90 THEN 'Considerar deshabilitar cuenta'
        WHEN DATEDIFF(DAY, ua.ultima_actividad, CURRENT_DATE) > 60 THEN 'Contactar al usuario'
        ELSE 'Monitorear'
    END AS accion_sugerida
FROM
    WMWHSE1.USERPROFILE u
    LEFT JOIN Ultima_Actividad ua ON u.USERNAME = ua.usuario
WHERE
    -- Filtrar por usuarios sin actividad reciente
    (
        ua.ultima_actividad IS NULL  -- Nunca han operado
        OR DATEDIFF(DAY, ua.ultima_actividad, CURRENT_DATE) >= {{dias_inactividad}}
    )
    -- Filtrar usuarios deshabilitados según parámetro
    AND (
        {{incluir_deshabilitados}} = 1
        OR u.STATUS = '0'  -- Solo activos si no se incluyen deshabilitados
    )
ORDER BY
    dias_sin_actividad DESC,
    u.USERNAME;
