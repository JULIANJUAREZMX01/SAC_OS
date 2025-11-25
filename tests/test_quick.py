#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba rápida para verificar todos los componentes SACITY
"""

from __future__ import print_function
import sys

def test_imports():
    """Prueba que todos los módulos se importan correctamente"""
    print("Probando importaciones...")

    try:
        from sacity_ui import Colores, ArteASCII, Animador
        print("  ✓ sacity_ui importado correctamente")
    except Exception as e:
        print(f"  ✗ Error importando sacity_ui: {e}")
        return False

    try:
        from sacity_shell import SacityShell, BufferPantalla, GestorSesionTelnet
        print("  ✓ sacity_shell importado correctamente")
    except Exception as e:
        print(f"  ✗ Error importando sacity_shell: {e}")
        return False

    try:
        from sacity_main import AplicacionSacity
        print("  ✓ sacity_main importado correctamente")
    except Exception as e:
        print(f"  ✗ Error importando sacity_main: {e}")
        return False

    return True


def test_colores():
    """Prueba sistema de colores"""
    print("\nProbando sistema de colores...")

    try:
        from sacity_ui import Colores

        print(Colores.ROJO + "  ✓ Color ROJO (#E31837)" + Colores.RESET)
        print(Colores.VERDE + "  ✓ Color VERDE (#00FF88)" + Colores.RESET)
        print(Colores.CYAN + "  ✓ Color CYAN (#00C8FF)" + Colores.RESET)
        print(Colores.GRIS_CLARO + "  ✓ Color GRIS" + Colores.RESET)

        return True

    except Exception as e:
        print(f"  ✗ Error probando colores: {e}")
        return False


def test_arte_ascii():
    """Prueba arte ASCII"""
    print("\nProbando arte ASCII...")

    try:
        from sacity_ui import ArteASCII, Colores

        print(Colores.ROJO)
        for linea in ArteASCII.LOGO_PEQUENO:
            print("  " + linea)
        print(Colores.RESET)

        print("  ✓ Arte ASCII renderizado correctamente")
        return True

    except Exception as e:
        print(f"  ✗ Error probando arte ASCII: {e}")
        return False


def test_buffer_pantalla():
    """Prueba buffer de pantalla VT100"""
    print("\nProbando buffer de pantalla VT100...")

    try:
        from sacity_shell import BufferPantalla

        buffer = BufferPantalla(filas=24, columnas=80)

        # Escribir texto
        buffer.escribir("Hola SACITY\r\n")
        buffer.escribir("Prueba de emulación VT100")

        # Obtener contenido
        contenido = buffer.obtener_pantalla()

        if "Hola SACITY" in contenido and "Prueba" in contenido:
            print("  ✓ Buffer de pantalla funcionando correctamente")
            return True
        else:
            print("  ✗ Buffer de pantalla no contiene el texto esperado")
            return False

    except Exception as e:
        print(f"  ✗ Error probando buffer: {e}")
        return False


def test_config():
    """Prueba gestor de configuración"""
    print("\nProbando gestor de configuración...")

    try:
        from sacity_main import GestorConfiguracion

        gestor = GestorConfiguracion()

        # Verificar valores por defecto
        host = gestor.obtener('servidor.host')
        puerto = gestor.obtener('servidor.puerto')

        print(f"  ✓ Host: {host}")
        print(f"  ✓ Puerto: {puerto}")

        return True

    except Exception as e:
        print(f"  ✗ Error probando configuración: {e}")
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("PRUEBAS RÁPIDAS - SACITY v1.0.0")
    print("=" * 60)

    resultados = []

    resultados.append(("Importaciones", test_imports()))
    resultados.append(("Colores", test_colores()))
    resultados.append(("Arte ASCII", test_arte_ascii()))
    resultados.append(("Buffer VT100", test_buffer_pantalla()))
    resultados.append(("Configuración", test_config()))

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    total = len(resultados)
    exitosas = sum(1 for _, resultado in resultados if resultado)

    for nombre, resultado in resultados:
        estado = "✓ OK" if resultado else "✗ FALLO"
        print(f"  {nombre.ljust(20)} {estado}")

    print()
    print(f"  Total: {exitosas}/{total} pruebas exitosas")
    print("=" * 60)

    return exitosas == total


if __name__ == '__main__':
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError inesperado: {e}")
        sys.exit(1)
