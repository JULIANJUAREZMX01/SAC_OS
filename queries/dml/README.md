# Queries DML - Operaciones de Corrección

Este directorio contiene las queries de manipulación de datos (DML) que el SAC puede ejecutar para corregir anomalías detectadas en Manhattan WMS.

## Filosofía

> "Las máquinas y los sistemas al servicio de los analistas"

Estas queries están diseñadas para:
- **Automatizar** correcciones que antes tomaban horas
- **Proteger** la integridad de los datos con validaciones
- **Auditar** cada cambio realizado
- **Prevenir** errores con condiciones WHERE estrictas

## Queries Disponibles

| Archivo | Operación | Tabla | Riesgo |
|---------|-----------|-------|--------|
| `ajustar_distribucion.sql` | Corregir cantidad de distribución | ORDERDETAIL | ALTO |
| `cerrar_oc.sql` | Cerrar OC completada | ORDERS | MEDIO |
| `cancelar_linea_distribucion.sql` | Cancelar línea específica | ORDERDETAIL | ALTO |
| `actualizar_asn_status.sql` | Actualizar status de ASN | RECEIPT | MEDIO |
| `ajustar_qty_recibo.sql` | Ajustar cantidad en recibo | RECEIPTDETAIL | ALTO |

## Uso con el Ejecutor de Correcciones

Estas queries son utilizadas por el módulo `modules/ejecutor_correcciones.py` que:

1. **Genera planes** de corrección basados en anomalías
2. **Presenta vista previa** al analista
3. **Requiere aprobación** antes de ejecutar
4. **Genera backup** de datos originales
5. **Ejecuta** las correcciones
6. **Audita** cada operación

## Estructura de Parámetros

Todas las queries usan placeholders con doble llave:
- `{{orderkey}}` - Número de OC/Distribución
- `{{linea}}` - Número de línea
- `{{usuario}}` - Usuario que ejecuta (para auditoría)
- `{{motivo}}` - Motivo del cambio
- etc.

## Seguridad

### Todas las queries incluyen:

1. **WHERE restrictivo** - Nunca UPDATE sin condición específica
2. **Exclusión de cancelados** - No modificar registros ya cancelados
3. **Auditoría integrada** - EDITDATE, EDITWHO actualizados
4. **Query de verificación** - Comentada para validar post-ejecución

### Permisos requeridos:

El usuario de conexión necesita:
```sql
GRANT SELECT, UPDATE ON WMWHSE1.ORDERS TO usuario;
GRANT SELECT, UPDATE ON WMWHSE1.ORDERDETAIL TO usuario;
GRANT SELECT, UPDATE ON WMWHSE1.RECEIPT TO usuario;
GRANT SELECT, UPDATE ON WMWHSE1.RECEIPTDETAIL TO usuario;
```

## Flujo de Ejecución

```
┌─────────────────────────────────────────────────────────────┐
│  Monitor detecta anomalía                                    │
│           │                                                  │
│           ▼                                                  │
│  Ejecutor genera Plan de Corrección                         │
│  (usa templates DML de este directorio)                     │
│           │                                                  │
│           ▼                                                  │
│  Analista revisa vista previa                               │
│  (puede exportar a Excel)                                   │
│           │                                                  │
│           ▼                                                  │
│  Analista APRUEBA o RECHAZA                                 │
│           │                                                  │
│           ▼ (si aprobado)                                   │
│  Sistema genera BACKUP automático                           │
│           │                                                  │
│           ▼                                                  │
│  Sistema ejecuta DMLs uno por uno                           │
│  (con manejo de errores y rollback)                         │
│           │                                                  │
│           ▼                                                  │
│  Sistema registra en AUDITORÍA                              │
│           │                                                  │
│           ▼                                                  │
│  Sistema reporta RESULTADO al analista                      │
└─────────────────────────────────────────────────────────────┘
```

## Agregar Nuevas Queries DML

1. Crear archivo `.sql` siguiendo la estructura existente
2. Incluir header con descripción, casos de uso, parámetros
3. Incluir query de verificación comentada
4. Documentar en este README
5. Integrar con `EjecutorCorrecciones` si es operación común

## Autor

Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logística Cancún
