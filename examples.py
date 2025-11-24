#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
EJEMPLOS DE USO - SISTEMA DE AUTOMATIZACIÓN DE PLANNING
Chedraui CEDIS Cancún
═══════════════════════════════════════════════════════════════

Este archivo contiene ejemplos prácticos de cómo usar cada módulo
del sistema de automatización.

Puedes copiar y adaptar estos ejemplos a tus necesidades específicas.

Desarrollado por: Julián Alexander Juárez Alvarado (ADM)
═══════════════════════════════════════════════════════════════
"""

import pandas as pd
from datetime import datetime, timedelta

# Importar módulos del sistema
from monitor import MonitorTiempoReal, ValidadorProactivo, ErrorSeverity
from modules.reportes_excel import GeneradorReportesExcel, generar_reporte_rapido
from gestor_correos import GestorCorreos


print("""
═══════════════════════════════════════════════════════════════
        EJEMPLOS DE USO - SISTEMA DE PLANNING
═══════════════════════════════════════════════════════════════
""")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 1: USO BÁSICO DEL MONITOR
# ═══════════════════════════════════════════════════════════════

def ejemplo_1_monitor_basico():
    """
    Ejemplo básico de uso del sistema de monitoreo
    """
    print("\n📊 EJEMPLO 1: Monitor Básico\n")
    
    # Crear monitor
    monitor = MonitorTiempoReal()
    
    # Datos de ejemplo de una OC
    df_oc = pd.DataFrame({
        'OC': ['OC12345'],
        'TOTAL_OC': [1000],
        'VIGENCIA': [datetime.now() + timedelta(days=30)],
        'ID_CODE': ['C123']
    })
    
    # Datos de distribuciones
    df_distro = pd.DataFrame({
        'OC': ['OC12345', 'OC12345', 'OC12345'],
        'TIENDA': ['001', '002', '003'],
        'SKU': ['SKU1', 'SKU2', 'SKU3'],
        'TOTAL_DISTRO': [300, 400, 300],
        'DISTR_QTY': [300, 400, 300],
        'IP': [10, 10, 10]
    })
    
    # Validar OC
    print("🔍 Validando OC...")
    errores_oc = monitor.validar_oc_existente(df_oc, 'OC12345')
    
    # Validar Distribuciones
    print("🔍 Validando distribuciones...")
    errores_distro = monitor.validar_distribuciones(df_oc, df_distro, 'OC12345')
    
    # Mostrar resultados
    total_errores = len(errores_oc) + len(errores_distro)
    
    if total_errores == 0:
        print("✅ No se detectaron errores - Todo OK!")
    else:
        print(f"⚠️  Se detectaron {total_errores} problemas:")
        for error in errores_oc + errores_distro:
            print(f"  • {error.severidad.value}: {error.mensaje}")
    
    # Generar reporte de errores
    df_errores = monitor.generar_reporte_errores()
    if not df_errores.empty:
        print("\n📄 Reporte de errores generado:")
        print(df_errores[['Severidad', 'Mensaje']].to_string(index=False))


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 2: DETECCIÓN DE ERROR CRÍTICO
# ═══════════════════════════════════════════════════════════════

def ejemplo_2_error_critico():
    """
    Ejemplo de detección de error crítico (distribución excedente)
    """
    print("\n\n🚨 EJEMPLO 2: Detección de Error Crítico\n")
    
    monitor = MonitorTiempoReal()
    
    # OC con 1000 unidades
    df_oc = pd.DataFrame({
        'OC': ['OC99999'],
        'TOTAL_OC': [1000],
        'VIGENCIA': [datetime.now() + timedelta(days=10)]
    })
    
    # Distribuciones con 1100 unidades (¡100 de más!)
    df_distro = pd.DataFrame({
        'OC': ['OC99999'] * 3,
        'TOTAL_DISTRO': [1100] * 3,
        'TIENDA': ['001', '002', '003'],
        'DISTR_QTY': [400, 400, 300]  # Total: 1100
    })
    
    print("⚠️  CASO: OC con 1000 unidades, pero distribuciones de 1100")
    print("      (100 unidades de EXCEDENTE)\n")
    
    # Validar
    errores = monitor.validar_distribuciones(df_oc, df_distro, 'OC99999')
    
    # Mostrar errores críticos
    criticos = [e for e in errores if e.severidad == ErrorSeverity.CRITICO]
    
    if criticos:
        print("🔴 ERROR CRÍTICO DETECTADO:")
        for error in criticos:
            print(f"\n  Tipo: {error.tipo}")
            print(f"  Mensaje: {error.mensaje}")
            print(f"  Detalles: {error.detalles}")
            print(f"  Solución:")
            print(f"  {error.solucion}")
    
    # Alertas críticas
    if monitor.alertas_criticas:
        print(f"\n🚨 Se generaron {len(monitor.alertas_criticas)} alertas críticas")
        print("   Estas se enviarían automáticamente por correo al equipo")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 3: GENERACIÓN DE REPORTES EXCEL
# ═══════════════════════════════════════════════════════════════

def ejemplo_3_reportes_excel():
    """
    Ejemplo de generación de reportes en Excel
    """
    print("\n\n📊 EJEMPLO 3: Generación de Reportes Excel\n")
    
    # Crear generador
    generador = GeneradorReportesExcel(cedis="CANCÚN")
    
    # Datos de validación
    df_validacion = pd.DataFrame({
        'ALM': ['427'] * 3,
        'OC': ['OC001', 'OC002', 'OC003'],
        'Proveedor': ['PROVEEDOR A', 'PROVEEDOR B', 'PROVEEDOR C'],
        'Total_OC': [1000, 2000, 1500],
        'Total_Distro': [1000, 1950, 1500],
        'Diferencia': [0, 50, 0],
        'STATUS': ['OK', 'Distro incompleta', 'OK']
    })
    
    print("📄 Generando reporte de validación...")
    archivo = generador.crear_reporte_validacion_oc(
        df_validacion=df_validacion,
        nombre_archivo="Ejemplo_Validacion.xlsx"
    )
    print(f"✅ Reporte generado: {archivo}")
    
    # Reporte de distribuciones
    df_distros = pd.DataFrame({
        'OC': ['OC001'] * 5,
        'N_Distrib': ['D001', 'D002', 'D003', 'D004', 'D005'],
        'TIENDA': ['001', '002', '003', '004', '005'],
        'SKU': ['SKU1', 'SKU2', 'SKU3', 'SKU4', 'SKU5'],
        'Descripcion': ['PRODUCTO A', 'PRODUCTO B', 'PRODUCTO C', 'PRODUCTO D', 'PRODUCTO E'],
        'REQ_QTY': [100, 200, 150, 250, 300],
        'DISTR_QTY': [100, 200, 150, 250, 300],
        'IP': [10, 20, 15, 25, 30]
    })
    
    print("\n📄 Generando reporte de distribuciones...")
    archivo = generador.crear_reporte_distribuciones(
        df_distribuciones=df_distros,
        oc_numero="OC001",
        nombre_archivo="Ejemplo_Distribuciones.xlsx"
    )
    print(f"✅ Reporte generado: {archivo}")
    
    # Reporte rápido (función de utilidad)
    print("\n📄 Generando reporte rápido...")
    datos_rapidos = pd.DataFrame({
        'Columna1': [1, 2, 3],
        'Columna2': ['A', 'B', 'C'],
        'Columna3': [100, 200, 300]
    })
    archivo = generar_reporte_rapido(
        df=datos_rapidos,
        nombre="Ejemplo_Rapido",
        titulo="REPORTE DE PRUEBA"
    )
    print(f"✅ Reporte rápido generado: {archivo}")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 4: ENVÍO DE CORREOS
# ═══════════════════════════════════════════════════════════════

def ejemplo_4_correos():
    """
    Ejemplo de envío de correos (modo DEMO - no envía realmente)
    """
    print("\n\n📧 EJEMPLO 4: Envío de Correos (DEMO)\n")
    
    # NOTA: Este ejemplo NO enviará correos reales
    # Para enviar correos, debes configurar las credenciales en .env
    
    print("⚠️  NOTA: Este es un ejemplo de demostración")
    print("   Para enviar correos reales, configura .env con tus credenciales\n")
    
    # Configuración de ejemplo
    config_demo = {
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'user': 'tu_correo@chedraui.com.mx',
        'password': 'tu_password',
        'from_name': 'Sistema Planning CEDIS'
    }
    
    # Crear gestor
    # gestor = GestorCorreos(config_demo)  # Comentado para no intentar enviar
    
    print("📋 Tipos de correos que puedes enviar:\n")
    
    print("1️⃣  Reporte Diario de Planning:")
    print("   gestor.enviar_reporte_planning_diario(")
    print("       destinatarios=['planning@chedraui.com.mx'],")
    print("       df_oc=df_oc,")
    print("       df_asn=df_asn,")
    print("       archivos_adjuntos=['reporte.xlsx']")
    print("   )")
    
    print("\n2️⃣  Alerta Crítica:")
    print("   gestor.enviar_alerta_critica(")
    print("       destinatarios=['jefe@chedraui.com.mx'],")
    print("       tipo_error='DISTRIBUCIÓN EXCEDENTE',")
    print("       descripcion='100 unidades de más',")
    print("       oc_numero='OC12345'")
    print("   )")
    
    print("\n3️⃣  Validación de OC:")
    print("   gestor.enviar_validacion_oc(")
    print("       destinatarios=['analista@chedraui.com.mx'],")
    print("       oc_numero='OC12345',")
    print("       status_validacion='OK',")
    print("       detalles={'Total OC': 1000},")
    print("       archivo_excel='validacion.xlsx'")
    print("   )")
    
    print("\n4️⃣  Programa de Recibo:")
    print("   gestor.enviar_programa_recibo(")
    print("       destinatarios=['recibo@chedraui.com.mx'],")
    print("       fecha_recibo='08/01/2025',")
    print("       lista_asn=[{'asn': 'ASN001', ...}],")
    print("       archivo_excel='programa.xlsx'")
    print("   )")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 5: FLUJO COMPLETO DE VALIDACIÓN
# ═══════════════════════════════════════════════════════════════

def ejemplo_5_flujo_completo():
    """
    Ejemplo de un flujo completo de validación y reporte
    """
    print("\n\n🔄 EJEMPLO 5: Flujo Completo de Validación\n")
    
    oc_numero = "OC12345"
    
    print(f"📋 FLUJO COMPLETO para OC: {oc_numero}\n")
    
    # PASO 1: Preparar datos (normalmente vendrían de DB2)
    print("1️⃣  Obteniendo datos...")
    
    df_oc = pd.DataFrame({
        'OC': [oc_numero],
        'Proveedor': ['PROVEEDOR EJEMPLO'],
        'TOTAL_OC': [1000],
        'VIGENCIA': [datetime.now() + timedelta(days=15)],
        'ID_CODE': ['C123']
    })
    
    df_distro = pd.DataFrame({
        'OC': [oc_numero] * 3,
        'TIENDA': ['001', '002', '003'],
        'SKU': ['SKU1', 'SKU2', 'SKU3'],
        'TOTAL_DISTRO': [1000, 1000, 1000],
        'DISTR_QTY': [300, 400, 300],
        'IP': [10, 10, 10]
    })
    
    # PASO 2: Validar
    print("2️⃣  Validando OC y distribuciones...")
    
    monitor = MonitorTiempoReal()
    errores_oc = monitor.validar_oc_existente(df_oc, oc_numero)
    errores_distro = monitor.validar_distribuciones(df_oc, df_distro, oc_numero)
    
    todos_errores = errores_oc + errores_distro
    
    print(f"   • Errores detectados: {len(todos_errores)}")
    
    # PASO 3: Determinar status
    print("3️⃣  Determinando status...")
    
    tiene_criticos = any(e.severidad == ErrorSeverity.CRITICO for e in todos_errores)
    tiene_alertas = any(e.severidad == ErrorSeverity.ALTO for e in todos_errores)
    
    if tiene_criticos:
        status = "🔴 CRÍTICO"
    elif tiene_alertas:
        status = "🟡 ALERTA"
    else:
        status = "✅ OK"
    
    print(f"   • Status final: {status}")
    
    # PASO 4: Generar reporte
    print("4️⃣  Generando reporte Excel...")
    
    generador = GeneradorReportesExcel(cedis="CANCÚN")
    
    df_validacion = pd.DataFrame({
        'OC': [oc_numero],
        'Proveedor': df_oc['Proveedor'].values,
        'Total_OC': df_oc['TOTAL_OC'].values,
        'Total_Distro': [df_distro['DISTR_QTY'].sum()],
        'Diferencia': [df_oc['TOTAL_OC'].sum() - df_distro['DISTR_QTY'].sum()],
        'STATUS': ['OK' if df_oc['TOTAL_OC'].sum() == df_distro['DISTR_QTY'].sum() else 'Revisar']
    })
    
    archivo = generador.crear_reporte_validacion_oc(
        df_validacion,
        nombre_archivo=f"Validacion_{oc_numero}_Ejemplo.xlsx"
    )
    
    print(f"   • Archivo: {archivo}")
    
    # PASO 5: Acción según resultado
    print("5️⃣  Acciones recomendadas...")
    
    if tiene_criticos:
        print("   🚨 ACCIÓN INMEDIATA:")
        print("      • Enviar alerta crítica a jefatura")
        print("      • Detener proceso de recibo")
        print("      • Corregir problemas detectados")
    elif tiene_alertas:
        print("   ⚠️  ACCIÓN NECESARIA:")
        print("      • Notificar a Planning")
        print("      • Completar distribuciones pendientes")
        print("      • Validar antes de continuar")
    else:
        print("   ✅ TODO OK:")
        print("      • Continuar con proceso normal")
        print("      • Enviar reporte informativo")
    
    print("\n✅ Flujo completo finalizado")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO 6: VALIDACIÓN PROACTIVA
# ═══════════════════════════════════════════════════════════════

def ejemplo_6_validacion_proactiva():
    """
    Ejemplo del validador proactivo que previene errores
    """
    print("\n\n🛡️  EJEMPLO 6: Validación Proactiva\n")
    
    print("El validador proactivo detecta errores ANTES de que ocurran:\n")
    
    validador = ValidadorProactivo()
    
    oc_numero = "OC67890"
    
    print(f"🔍 Validando OC {oc_numero} de forma proactiva...")
    print("   (sin conexión DB2 - modo demo)\n")
    
    # Simular validación
    print("   ✓ Verificando conexión DB2...")
    print("   ✓ Consultando datos de OC...")
    print("   ✓ Consultando distribuciones...")
    print("   ✓ Validando integridad de datos...")
    print("   ✓ Verificando vigencias...")
    print("   ✓ Comparando cantidades...")
    
    print("\n✅ Validación proactiva completada")
    print("   Permite detectar y corregir problemas anticipadamente")


# ═══════════════════════════════════════════════════════════════
# MENÚ DE EJEMPLOS
# ═══════════════════════════════════════════════════════════════

def menu_ejemplos():
    """Muestra menú interactivo de ejemplos"""
    
    while True:
        print("\n" + "="*70)
        print("         MENÚ DE EJEMPLOS")
        print("="*70)
        print("\n1. Monitor Básico")
        print("2. Detección de Error Crítico")
        print("3. Generación de Reportes Excel")
        print("4. Envío de Correos (Demo)")
        print("5. Flujo Completo de Validación")
        print("6. Validación Proactiva")
        print("\n0. Salir")
        print("\n" + "-"*70)
        
        opcion = input("\nSelecciona un ejemplo (0-6): ").strip()
        
        if opcion == '1':
            ejemplo_1_monitor_basico()
        elif opcion == '2':
            ejemplo_2_error_critico()
        elif opcion == '3':
            ejemplo_3_reportes_excel()
        elif opcion == '4':
            ejemplo_4_correos()
        elif opcion == '5':
            ejemplo_5_flujo_completo()
        elif opcion == '6':
            ejemplo_6_validacion_proactiva()
        elif opcion == '0':
            print("\n👋 ¡Hasta luego!\n")
            break
        else:
            print("\n❌ Opción no válida")
        
        input("\nPresiona ENTER para continuar...")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        menu_ejemplos()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")


print("""
═══════════════════════════════════════════════════════════════

💡 CONSEJOS PARA USAR LOS EJEMPLOS:

1. Ejecuta este archivo para ver demos interactivos:
   python examples.py

2. Copia y adapta el código de los ejemplos a tus scripts

3. Los ejemplos usan datos simulados - reemplázalos con
   consultas reales a DB2 en tu implementación

4. Revisa los comentarios en el código para entender
   cada paso

═══════════════════════════════════════════════════════════════

Desarrollado con ❤️  por: Julián Alexander Juárez Alvarado (ADM)
Analista de Sistemas - CEDIS Chedraui Logística Cancún

"Las máquinas y los sistemas al servicio de los analistas"

═══════════════════════════════════════════════════════════════
""")
