# Resumen Ejecutivo: Análisis de Queries - SAC

## Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| **Archivos SQL analizados** | 31 |
| **Total de líneas de código** | 2,101 |
| **Problemas identificados** | 20+ |
| **Severidad máxima** | CRÍTICO |

### Distribución de Archivos
- Obligatorias: 8 queries
- Preventivas: 7 queries  
- Bajo Demanda: 8 queries
- DDL (Views): 3 queries
- DDL (Procedures): 2 queries
- Soporte: 1 Python (query_loader.py)

---

## Problemas por Severidad

### 🔴 CRÍTICO (4 problemas)

1. **NULLS LAST - Sintaxis incompatible con DB2**
   - Archivos: 4
   - Líneas: 90, 104-105, 126, 104
   - Solución: Reemplazar con CASE WHEN NULL

2. **Campo SUSR1 potencialmente no existente**
   - Archivo: recibo_programado.sql (línea 65)
   - Acción: Validar en DB2 inmediatamente

3. **Nombres de tablas sin verificar**
   - USERPROFILE, TASKDETAIL, PUTAWAYZONE, etc.
   - Acción: Ejecutar SELECT TABNAME FROM SYSCAT.TABLES

4. **Mismatch de tipos: usuario (string) vs USERKEY (int)**
   - Archivo: auditoria_usuario.sql (líneas 69, 95)
   - Acción: Cambiar a ADDWHO = '{{usuario}}'

---

### 🟠 ALTO (3-4 problemas)

1. **SQL INJECTION con LIKE** - Bajo riesgo (mitigado)
   - Archivos: buscar_asn.sql, buscar_lpn.sql, buscar_oc.sql
   - Mitigation: Validar en aplicación, usar ESCAPE

2. **Variables no inicializadas en procedures**
   - Archivo: sp_validate_oc.sql
   - Solución: Agregar DEFAULT NULL

3. **Inserción ciega sin validación**
   - Archivo: sp_get_daily_report.sql
   - Solución: Agregar HAVING COUNT(*) > 0

4. **SESSION temporary tables con concurrencia**
   - Archivos: sp_get_daily_report.sql, sp_validate_oc.sql
   - Solución: Usar PRIVATE TEMPORARY o refactorizar

---

### 🟡 MEDIO (4-5 problemas)

1. **GROUP BY incompleto** - Riesgo condicional DB2
   - Archivos: auditoria_usuario.sql, historial_oc.sql
   
2. **Parámetro con lógica confusa**
   - Archivo: detalle_distribucion.sql ({{tienda_destino}} = '%')
   
3. **Repetición de parámetros**
   - Archivo: ubicaciones_llenas.sql ({{umbral_capacidad}} x4)
   
4. **Vista referencia a sí misma en mismo script**
   - Archivo: v_distribution_totals.sql
   
5. **Hardcoded status codes en 20+ lugares**
   - Solución: Crear tabla de referencia

---

### 🟢 BAJO (5-6 problemas)

1. Metadata extraction imprecisa (query_loader.py)
2. Validación de placeholders incompleta
3. Inconsistencia ORDERKEY vs EXTERNORDERKEY
4. Documentación incompleta de parámetros
5. Falta de ejemplos de ejecución
6. Sin manejo explícito de timezones

---

## Matriz de Archivos Problemáticos

| Archivo | Problemas | Severidad | Acción |
|---------|-----------|-----------|--------|
| ubicaciones_llenas.sql | 2 | CRÍTICO | Reemplazar NULLS LAST |
| recibo_programado.sql | 2 | CRÍTICO | Verificar SUSR1, NULLS LAST |
| auditoria_usuario.sql | 4 | ALTO/MEDIO | Cambiar USERKEY, GROUP BY, NULLS LAST |
| buscar_asn.sql | 1 | ALTO | SQL INJECTION risk (mitigado) |
| buscar_lpn.sql | 1 | ALTO | SQL INJECTION risk (mitigado) |
| buscar_oc.sql | 2 | ALTO | SQL INJECTION, ORDERKEY logic |
| detalle_distribucion.sql | 1 | MEDIO | Parámetro tienda_destino |
| movimientos_lpn.sql | 1 | CRÍTICO | NULLS LAST |
| sp_validate_oc.sql | 2 | ALTO | Variables sin init, SESSION tables |
| sp_get_daily_report.sql | 3 | ALTO/MEDIO | INSERT ciego, SESSION tables |
| v_distribution_totals.sql | 1 | MEDIO | Vista auto-ref |
| query_loader.py | 2 | BAJO | Validación, metadata |
| 6 archivos más | 1-2 | BAJO/MEDIO | Hardcoded status codes |

---

## Plan de Acción Recomendado

### Fase 1: MÁXIMA PRIORIDAD (Hoy/Mañana)
```
[ ] Ejecutar auditoría de tablas en DB2:
    SELECT TABNAME FROM SYSCAT.TABLES 
    WHERE TABSCHEMA='WMWHSE1' ORDER BY TABNAME

[ ] Verificar campo SUSR1 en RECEIPT:
    SELECT COLNAME FROM SYSCAT.COLUMNS 
    WHERE TABNAME='RECEIPT' AND COLNAME LIKE '%USR%'
```

### Fase 2: ALTA PRIORIDAD (Esta semana)
```
[ ] Reemplazar NULLS LAST en 4 archivos
    - ubicaciones_llenas.sql
    - recibo_programado.sql
    - auditoria_usuario.sql
    - movimientos_lpn.sql

[ ] Corregir parámetro usuario en auditoria_usuario.sql
    - Cambiar: td.USERKEY = '{{usuario}}'
    - Por: td.ADDWHO = '{{usuario}}'

[ ] Inicializar variables en procedures
    - DECLARE v_oc_status VARCHAR(10) DEFAULT NULL

[ ] Refactorizar SESSION tables a PRIVATE TEMPORARY
```

### Fase 3: MEDIA PRIORIDAD (Próximas 2 semanas)
```
[ ] Arreglar GROUP BY incompleto en UNION ALL
[ ] Documentar todos los parámetros (ranges, valores por defecto)
[ ] Crear tabla REFERENCE_CODES para status
[ ] Separar scripts DDL con dependencias
```

### Fase 4: BAJA PRIORIDAD (Mejora técnica)
```
[ ] Mejorar validación en query_loader.py
[ ] Estandarizar formato de comentarios
[ ] Agregar ejemplos de ejecución
[ ] Implementar versionamiento real
```

---

## Archivos con Problemas Críticos (Actuar primero)

### 1️⃣ ubicaciones_llenas.sql
```sql
-- PROBLEMA: NULLS LAST (líneas 104-105)
ORDER BY nivel_alerta, porcentaje_cubicaje DESC NULLS LAST, ...

-- SOLUCIÓN:
ORDER BY nivel_alerta, 
         CASE WHEN porcentaje_cubicaje IS NULL THEN 1 ELSE 0 END,
         porcentaje_cubicaje DESC, ...
```

### 2️⃣ recibo_programado.sql  
```sql
-- PROBLEMA 1: NULLS LAST (línea 90)
-- SOLUCIÓN: Ver ejemplo anterior

-- PROBLEMA 2: SUSR1 podría no existir (línea 65)
LEFT JOIN WMWHSE1.STORER sup ON r.SUSR1 = sup.STORERKEY
-- VERIFICAR: ¿Es el campo correcto para proveedor?
```

### 3️⃣ auditoria_usuario.sql
```sql
-- PROBLEMA 1: NULLS LAST (línea 126)
-- SOLUCIÓN: Ver ejemplo anterior

-- PROBLEMA 2: Usuario como INT (líneas 69, 95)
WHERE td.USERKEY = '{{usuario}}'  -- ❌ USERKEY es INT, {{usuario}} es VARCHAR
-- SOLUCIÓN:
WHERE td.ADDWHO = '{{usuario}}'  -- ✅ ADDWHO probablemente sea VARCHAR
```

---

## Comandos de Verificación Quick

```bash
# Ver nombre exacto de tablas en DB2
db2 "SELECT TABNAME FROM SYSCAT.TABLES WHERE TABSCHEMA='WMWHSE1' ORDER BY TABNAME"

# Ver columnas de una tabla
db2 "SELECT COLNAME FROM SYSCAT.COLUMNS WHERE TABNAME='RECEIPT'"

# Ver índices
db2 "SELECT INDNAME FROM SYSCAT.INDEXES WHERE TABNAME='ORDERS'"

# Validar sintaxis de query
db2 "EXPLAIN SELECT ... FROM ..."
```

---

## Recursos Generados

- **Análisis completo**: `/home/user/SAC_V01_427_ADMJAJA/ANALISIS_QUERIES_DETALLADO.txt`
- **Este resumen**: `/home/user/SAC_V01_427_ADMJAJA/RESUMEN_PROBLEMAS_QUERIES.md`

---

## Conclusiones

✅ **Fortalezas:**
- Buen uso de parametrización {{param}}
- Excelente documentación de headers
- Queries bien organizadas en categorías
- Buena cobertura de casos de uso

⚠️ **Áreas de riesgo:**
- Nombres de tablas sin verificación
- Sintaxis específica de otros DBs en código DB2
- Variables sin inicialización explícita
- Magic numbers hardcoded (status codes)
- Falta de manejo de NULL en algunos cálculos

🎯 **Próximos pasos:**
1. Validar nombres de tablas en DB2
2. Corregir sintaxis NULLS LAST
3. Inicializar todas las variables
4. Documentar parámetros completamente

---

**Análisis completado**: 2025-11-21  
**Archivos revisados**: 32 (31 SQL + 1 Python)  
**Total de problemas encontrados**: 20+  
**Estimación de correcciones**: 2-3 semanas (completo)
