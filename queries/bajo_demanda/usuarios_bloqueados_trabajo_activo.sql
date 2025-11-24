-- ═══════════════════════════════════════════════════════════════
-- QUERY: USUARIOS BLOQUEADOS CON TRABAJO ACTIVO
-- Sistema SAC - CEDIS Cancún 427
-- ═══════════════════════════════════════════════════════════════
--
-- Propósito:
--   Detecta usuarios que se han desconectado de manera abrupta
--   mientras realizaban un trabajo visible en el sistema.
--   Estos usuarios necesitan ser habilitados automáticamente
--   para no bloquear operaciones en curso.
--
-- Criterios de detección:
--   1. Usuario con estado bloqueado (STATUS = '9')
--   2. Usuario sin sesión activa pero con tarea asignada
--   3. Usuario con sesión cerrada pero con tarea en progreso
--
-- Tablas involucradas:
--   - WMWHSE1.USERPROFILE: Perfiles de usuario
--   - WMWHSE1.TASKDETAIL: Detalle de tareas asignadas
--   - WMWHSE1.USERSESSION: Sesiones de usuario activas
--
-- Autor: Julián Alexander Juárez Alvarado (ADMJAJA)
-- Fecha: Noviembre 2025
-- ═══════════════════════════════════════════════════════════════

SELECT
    -- Información del usuario
    UP.USERKEY AS USUARIO_ID,
    UP.USERNAME AS NOMBRE_USUARIO,
    COALESCE(TRIM(UP.FIRSTNAME) || ' ' || TRIM(UP.LASTNAME), UP.USERNAME) AS NOMBRE_COMPLETO,
    UP.USERGROUP AS GRUPO_USUARIO,
    UP.STATUS AS ESTADO_ACTUAL,
    UP.ADDDATE AS FECHA_CREACION,
    UP.EDITDATE AS ULTIMA_MODIFICACION,

    -- Información de tarea activa
    TD.TASKDETAILKEY AS TAREA_ID,
    TD.TASKTYPE AS TIPO_TAREA,
    CASE TD.TASKTYPE
        WHEN 'PK' THEN 'Picking'
        WHEN 'PT' THEN 'Putaway'
        WHEN 'RP' THEN 'Replenishment'
        WHEN 'MV' THEN 'Move'
        WHEN 'CC' THEN 'Cycle Count'
        WHEN 'PA' THEN 'Pack'
        WHEN 'SH' THEN 'Ship'
        WHEN 'RC' THEN 'Receive'
        ELSE TD.TASKTYPE
    END AS TIPO_TAREA_DESC,
    TD.STATUS AS ESTADO_TAREA,
    CASE TD.STATUS
        WHEN '0' THEN 'Released'
        WHEN '1' THEN 'Assigned'
        WHEN '2' THEN 'In Progress'
        WHEN '3' THEN 'Interrupted'
        WHEN '9' THEN 'Completed'
        ELSE TD.STATUS
    END AS ESTADO_TAREA_DESC,
    TD.FROMLOC AS UBICACION_ORIGEN,
    TD.TOLOC AS UBICACION_DESTINO,
    TD.SKU AS SKU,
    TD.QTY AS CANTIDAD,
    TD.STARTTIME AS INICIO_TAREA,
    TD.ADDDATE AS FECHA_ASIGNACION,

    -- Calcular tiempo desde última actividad
    TIMESTAMPDIFF(MINUTE, TD.STARTTIME, CURRENT_TIMESTAMP) AS MINUTOS_DESDE_INICIO,
    TIMESTAMPDIFF(MINUTE, COALESCE(US.LASTACTIVITY, TD.STARTTIME), CURRENT_TIMESTAMP) AS MINUTOS_INACTIVO,

    -- Información de sesión
    COALESCE(US.LASTACTIVITY, TD.STARTTIME) AS ULTIMA_ACTIVIDAD,
    US.SESSIONID AS SESION_ID,
    US.TERMINALID AS TERMINAL_ID,
    US.STATUS AS ESTADO_SESION,

    -- Motivo de bloqueo detectado
    CASE
        WHEN UP.STATUS = '9' THEN 'Usuario bloqueado por sistema'
        WHEN US.SESSIONID IS NULL AND TD.TASKDETAILKEY IS NOT NULL THEN 'Sin sesion con tarea activa'
        WHEN US.STATUS = '0' AND TD.TASKDETAILKEY IS NOT NULL THEN 'Sesion cerrada con tarea pendiente'
        ELSE 'Desconexion abrupta'
    END AS MOTIVO_BLOQUEO,

    -- Información adicional del pedido/orden
    TD.ORDERKEY AS ORDEN_ID,
    TD.WAVEKEY AS WAVE_ID,
    TD.CASEID AS CARTON_ID,
    TD.LPNID AS LPN_ID

FROM WMWHSE1.USERPROFILE UP

-- Join con tareas activas
LEFT JOIN WMWHSE1.TASKDETAIL TD
    ON UP.USERKEY = TD.USERKEY
    AND TD.STATUS IN ('1', '2', '3')  -- Assigned, In Progress, Interrupted

-- Join con sesiones
LEFT JOIN WMWHSE1.USERSESSION US
    ON UP.USERKEY = US.USERKEY

WHERE
    -- Condiciones de bloqueo
    (
        UP.STATUS = '9'  -- Usuario explícitamente bloqueado
        OR (US.SESSIONID IS NULL AND TD.TASKDETAILKEY IS NOT NULL)  -- Sin sesión pero con tarea
        OR (US.STATUS = '0' AND TD.TASKDETAILKEY IS NOT NULL)  -- Sesión cerrada con tarea activa
    )

    -- Con trabajo visible/activo
    AND TD.TASKDETAILKEY IS NOT NULL

    -- En las últimas 24 horas (evitar usuarios antiguos)
    AND TD.STARTTIME >= CURRENT_TIMESTAMP - 24 HOURS

    -- Excluir usuarios de sistema
    AND UP.USERNAME NOT IN ('SYSTEM', 'ADMIN', 'BATCH', 'INTERFACE', 'SAC_AUTO_ENABLE')

ORDER BY MINUTOS_DESDE_INICIO DESC;


-- ═══════════════════════════════════════════════════════════════
-- QUERY AUXILIAR: HABILITAR USUARIO
-- ═══════════════════════════════════════════════════════════════
-- Para ejecutar después de detectar un usuario bloqueado
--
-- UPDATE WMWHSE1.USERPROFILE
-- SET
--     STATUS = '1',
--     EDITDATE = CURRENT_TIMESTAMP,
--     EDITWHO = 'SAC_AUTO_ENABLE'
-- WHERE
--     USERKEY = ?
--     AND STATUS = '9';


-- ═══════════════════════════════════════════════════════════════
-- QUERY AUXILIAR: LIBERAR SESIÓN
-- ═══════════════════════════════════════════════════════════════
-- Para liberar una sesión bloqueada
--
-- UPDATE WMWHSE1.USERSESSION
-- SET
--     STATUS = '0',
--     ENDTIME = CURRENT_TIMESTAMP,
--     EDITDATE = CURRENT_TIMESTAMP
-- WHERE
--     USERKEY = ?
--     AND STATUS != '0';


-- ═══════════════════════════════════════════════════════════════
-- ESTADÍSTICAS DE USUARIOS BLOQUEADOS (RESUMEN)
-- ═══════════════════════════════════════════════════════════════
-- SELECT
--     COUNT(*) AS TOTAL_BLOQUEADOS,
--     COUNT(DISTINCT UP.USERGROUP) AS GRUPOS_AFECTADOS,
--     AVG(TIMESTAMPDIFF(MINUTE, TD.STARTTIME, CURRENT_TIMESTAMP)) AS PROMEDIO_MINUTOS_BLOQUEADO,
--     MAX(TIMESTAMPDIFF(MINUTE, TD.STARTTIME, CURRENT_TIMESTAMP)) AS MAX_MINUTOS_BLOQUEADO
-- FROM WMWHSE1.USERPROFILE UP
-- LEFT JOIN WMWHSE1.TASKDETAIL TD ON UP.USERKEY = TD.USERKEY
-- WHERE UP.STATUS = '9' AND TD.STATUS IN ('1', '2', '3');
