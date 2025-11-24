"""
===============================================================================
MODULO DE FUNCIONES BASICAS CEDIS - SAC
Sistema de Automatizacion de Consultas - CEDIS Cancun 427
===============================================================================

Este modulo proporciona funciones basicas y utilitarias para el personal de
sistemas del CEDIS Cancun, basadas en el Manual de Sistemas del CEDIS.

Funcionalidades incluidas:
- Directorio telefonico de extensiones
- Consulta de IPs de equipos
- Contactos importantes del area
- Atajos de teclado para WM
- Informacion de Hand Helds (RF)
- Guia de navegacion de menus WM
- Estado de impresoras
- Rutas de navegacion comunes

Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
===============================================================================
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# ===============================================================================
# CONSTANTES DEL MODULO
# ===============================================================================

CEDIS_CODE = '427'
CEDIS_NAME = 'CEDIS Cancun'
VERSION_MODULO = '1.0.0'

# ===============================================================================
# ENUMERACIONES
# ===============================================================================

class TipoContacto(Enum):
    """Tipos de contacto disponibles"""
    INTERNO = "Interno"
    EXTERNO = "Externo"
    MESA_AYUDA = "Mesa de Ayuda"
    PROVEEDOR = "Proveedor"

class TipoEquipo(Enum):
    """Tipos de equipos de computo"""
    COMPUTADORA = "Computadora"
    IMPRESORA = "Impresora"
    ETIQUETADORA = "Etiquetadora"
    HAND_HELD = "Hand Held / RF"
    SERVIDOR = "Servidor"

class EstadoDispositivo(Enum):
    """Estados posibles de un dispositivo"""
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    EN_MANTENIMIENTO = "En Mantenimiento"
    DANADO = "Danado"

# ===============================================================================
# DATACLASSES
# ===============================================================================

@dataclass
class ExtensionTelefonica:
    """Representa una extension telefonica del CEDIS"""
    extension: str
    departamento: str
    colaborador: Optional[str] = None
    notas: Optional[str] = None

@dataclass
class ContactoImportante:
    """Representa un contacto importante"""
    nombre: str
    telefono: str
    departamento: str
    tipo: TipoContacto
    razon_contacto: str
    correo: Optional[str] = None

@dataclass
class EquipoIP:
    """Representa la configuracion IP de un equipo"""
    nombre: str
    ip: str
    tipo: TipoEquipo
    ubicacion: str
    notas: Optional[str] = None

@dataclass
class AtajoTeclado:
    """Representa un atajo de teclado para WM"""
    combinacion: str
    accion: str
    contexto: str
    notas: Optional[str] = None

@dataclass
class MenuWM:
    """Representa una ruta de navegacion en WM"""
    nombre: str
    ruta: str
    descripcion: str
    opciones_principales: List[str] = field(default_factory=list)

# ===============================================================================
# DIRECTORIO TELEFONICO
# ===============================================================================

DIRECTORIO_TELEFONICO: Dict[str, ExtensionTelefonica] = {
    '4500': ExtensionTelefonica('4500', 'Entrada', notas='Extension general'),
    '4501': ExtensionTelefonica('4501', 'Jefe Prevencion'),
    '4502': ExtensionTelefonica('4502', 'CCTV'),
    '4503': ExtensionTelefonica('4503', 'Calidad'),
    '4504': ExtensionTelefonica('4504', 'Auxiliar Prevencion'),
    '4506': ExtensionTelefonica('4506', 'Oficina', colaborador='Nayeli'),
    '4507': ExtensionTelefonica('4507', 'Nomina', colaborador='Anna'),
    '4508': ExtensionTelefonica('4508', 'Capacitacion'),
    '4509': ExtensionTelefonica('4509', 'Supervision de Gestion'),
    '4511': ExtensionTelefonica('4511', 'Administracion', colaborador='Dani Luz'),
    '4512': ExtensionTelefonica('4512', 'Trafico'),
    '4513': ExtensionTelefonica('4513', 'RH', colaborador='Raul'),
    '4514': ExtensionTelefonica('4514', 'Subgerente', colaborador='Jovani'),
    '4515': ExtensionTelefonica('4515', 'Expedicion'),
    '4516': ExtensionTelefonica('4516', 'Recibo'),
    '4517': ExtensionTelefonica('4517', 'Preparacion'),
    '4518': ExtensionTelefonica('4518', 'Jefe Reparacion'),
    '4521': ExtensionTelefonica('4521', 'Gestion'),
    '4522': ExtensionTelefonica('4522', 'Servicio Medico'),
    '4550': ExtensionTelefonica('4550', 'Sistemas'),
}

# ===============================================================================
# CONTACTOS IMPORTANTES
# ===============================================================================

CONTACTOS_IMPORTANTES: List[ContactoImportante] = [
    ContactoImportante(
        nombre='Carlos Mar',
        telefono='228 839 9186',
        departamento='Infraestructura',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Productividad, pendientes por repartir, OC DOM'
    ),
    ContactoImportante(
        nombre='Hector Reyes',
        telefono='555 416 0501',
        departamento='Telefonia',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Todo sobre telefonos'
    ),
    ContactoImportante(
        nombre='Gabriela Segura',
        telefono='558 791 0515',
        departamento='Soporte Sistemas',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Todo de WM, creacion de usuarios'
    ),
    ContactoImportante(
        nombre='Ivan',
        telefono='5543 181600',
        departamento='Trabajo',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Contacto de trabajo'
    ),
    ContactoImportante(
        nombre='Israel Suarez',
        telefono='557 248 8452',
        departamento='Infraestructura',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Soporte de infraestructura'
    ),
    ContactoImportante(
        nombre='Nextel Sistemas',
        telefono='557 248 6293',
        departamento='Sistemas',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Comunicacion de sistemas'
    ),
    ContactoImportante(
        nombre='Mesa de Ayuda',
        telefono='6901 1911',
        departamento='Soporte',
        tipo=TipoContacto.MESA_AYUDA,
        razon_contacto='Soporte tecnico general'
    ),
    ContactoImportante(
        nombre='Analistas Mexico',
        telefono='55 32 67 01 71',
        departamento='Sistemas',
        tipo=TipoContacto.EXTERNO,
        razon_contacto='Soporte de analistas centrales'
    ),
]

# ===============================================================================
# IPS DE IMPRESORAS/ETIQUETADORAS
# ===============================================================================

IPS_ETIQUETADORAS: Dict[str, EquipoIP] = {
    'PRTECAN51': EquipoIP('PRTECAN51', '172.19.69.51', TipoEquipo.ETIQUETADORA, 'Plataforma'),
    'PRTECAN52': EquipoIP('PRTECAN52', '172.19.69.36', TipoEquipo.ETIQUETADORA, 'Plataforma'),
    'PRTECAN53': EquipoIP('PRTECAN53', '172.19.69.53', TipoEquipo.ETIQUETADORA, 'Plataforma'),
    'PRTECAN54': EquipoIP('PRTECAN54', '172.19.69.54', TipoEquipo.ETIQUETADORA, 'Plataforma'),
}

# ===============================================================================
# ATAJOS DE TECLADO WM
# ===============================================================================

ATAJOS_TECLADO_WM: List[AtajoTeclado] = [
    AtajoTeclado('Shift + Supr', 'Copiar', 'General'),
    AtajoTeclado('Shift + Av Pag', 'Pegar', 'General'),
    AtajoTeclado('Av Pag', 'Avanzar pagina', 'Navegacion'),
    AtajoTeclado('Re Pag', 'Retroceder pagina', 'Navegacion'),
    AtajoTeclado('Enter', 'Confirmar/Ejecutar', 'General'),
    AtajoTeclado('ESC', 'Menu administrador', 'Menu'),
    AtajoTeclado('F2', 'Crear usuario (Menu Admin)', 'Usuarios'),
    AtajoTeclado('F3', 'Cambiar contrasena (Menu Admin)', 'Usuarios'),
    AtajoTeclado('F5', 'Habilitar usuario (Menu Admin)', 'Usuarios'),
    AtajoTeclado('F7', 'Habilitar (Menu Habilita)', 'Usuarios'),
    AtajoTeclado('F12', 'Volver pantalla anterior', 'Navegacion'),
    AtajoTeclado('Shift + F4 (F16)', 'Guardar usuario', 'Usuarios'),
    AtajoTeclado('Shift + F10 (F22)', 'Ver impresoras', 'Impresoras'),
    AtajoTeclado('Control', 'Desbloquear teclado', 'General',
                 'Presionar cuando aparezca mensaje de teclado bloqueado'),
]

# Para teclas F13 en adelante
TECLAS_F_EXTENDIDAS: Dict[str, str] = {
    'F13': 'Shift + F1',
    'F14': 'Shift + F2',
    'F15': 'Shift + F3',
    'F16': 'Shift + F4',
    'F17': 'Shift + F5',
    'F18': 'Shift + F6',
    'F19': 'Shift + F7',
    'F20': 'Shift + F8',
    'F21': 'Shift + F9',
    'F22': 'Shift + F10',
    'F23': 'Shift + F11',
    'F24': 'Shift + F12',
}

# ===============================================================================
# MENUS Y NAVEGACION WM
# ===============================================================================

MENUS_WM: Dict[str, MenuWM] = {
    'usuarios': MenuWM(
        nombre='Maestro de Usuarios',
        ruta='20 -> 7',
        descripcion='Gestion de usuarios del sistema',
        opciones_principales=['3-Copiar', '4-Eliminar', '5-Mostrar']
    ),
    'errores': MenuWM(
        nombre='Info Errores Trabajo',
        ruta='20 -> 106',
        descripcion='Ver errores del sistema por fecha/hora'
    ),
    'errores_detalle': MenuWM(
        nombre='Info Errores Detalle',
        ruta='20 -> 111',
        descripcion='Ver errores detallados del sistema'
    ),
    'recepcion_asn': MenuWM(
        nombre='Trabajar con ASN',
        ruta='1 -> 13',
        descripcion='Gestion de ASN y Ordenes de Compra'
    ),
    'stock_lpn': MenuWM(
        nombre='Trabajar con LPN',
        ruta='5 -> 1 -> 2',
        descripcion='Localizacion y gestion de LPN'
    ),
    'distribuciones': MenuWM(
        nombre='Trabajar con Distribuciones',
        ruta='16 -> 50',
        descripcion='Administracion de distribuciones'
    ),
    'servidores': MenuWM(
        nombre='Supervision de Servidores',
        ruta='22 -> 1',
        descripcion='Monitoreo de estado de servidores'
    ),
    'transferencias': MenuWM(
        nombre='Control de Transferencias',
        ruta='22 -> (opcion)',
        descripcion='Mantenimiento control de transferencias'
    ),
    'configuracion': MenuWM(
        nombre='Configuracion Sistema',
        ruta='21',
        descripcion='Configuracion del sistema WM'
    ),
    'conf_mercaderia': MenuWM(
        nombre='Ubicacion Embarque Tiendas',
        ruta='21 -> 14 -> 2',
        descripcion='Configuracion de tipo y grupo de mercaderia'
    ),
    'fletes': MenuWM(
        nombre='Administracion de Fletes',
        ruta='16',
        descripcion='Menu de administracion de fletes'
    ),
    'impresion_cartones': MenuWM(
        nombre='Impresion de Cartones',
        ruta='11 -> 67 -> 2',
        descripcion='Imprimir cartones de prueba'
    ),
    'rutas': MenuWM(
        nombre='Rutas y Cortinas',
        ruta='16 -> 51',
        descripcion='Corroborar informacion de cortinas y asignaciones'
    ),
}

# ===============================================================================
# USUARIOS ESPECIALES WM
# ===============================================================================

USUARIOS_ESPECIALES: Dict[str, Dict] = {
    'HABILITA': {
        'descripcion': 'Usuario para habilitar usuarios e impresoras',
        'password': 'habilita',
        'uso': 'Habilitar usuarios con F7, impresoras con nombre'
    },
    'MODREPORT': {
        'descripcion': 'Usuario para generar reportes',
        'uso': 'Generar reportes como Pendientes por Repartir (0013)',
        'menu_especial': 'ESC para acceder, opcion 5 habilita usuario Habilita'
    },
}

# ===============================================================================
# OPCIONES DE USUARIO EN WM
# ===============================================================================

OPCIONES_USUARIO_WM: Dict[int, str] = {
    3: 'Copiar usuario',
    4: 'Eliminar usuario',
    5: 'Mostrar usuario',
}

# ===============================================================================
# INFORMACION DE HAND HELDS
# ===============================================================================

HAND_HELD_INFO: Dict[str, str] = {
    'modelo_actual': 'MC93',
    'reinicio': 'Quitar bateria + presionar boton azul y encendido + gatillo 2 veces',
    'conexion_pc': 'Conectar al lector de pines, esperar icono de conexion',
    'salir_wm': 'CTRL + A, esperar, escribir 9, confirmar con ENTER',
    'bluetooth': 'Mantener presionado documento -> Beam file',
    'carpeta_config': 'Application/AppCenter.cfg',
}

ATAJOS_RF: Dict[str, str] = {
    'CTRL + A': 'Salir del sistema WM (luego escribir 9)',
}

# ===============================================================================
# FUNCIONES PRINCIPALES
# ===============================================================================

def buscar_extension(termino: str) -> List[ExtensionTelefonica]:
    """
    Busca extensiones telefonicas por numero, departamento o colaborador.

    Args:
        termino: Termino de busqueda (numero, departamento o nombre)

    Returns:
        Lista de extensiones que coinciden con la busqueda
    """
    termino = termino.lower()
    resultados = []

    for ext_num, ext in DIRECTORIO_TELEFONICO.items():
        if (termino in ext_num.lower() or
            termino in ext.departamento.lower() or
            (ext.colaborador and termino in ext.colaborador.lower())):
            resultados.append(ext)

    return resultados


def obtener_extension(departamento: str) -> Optional[ExtensionTelefonica]:
    """
    Obtiene la extension de un departamento especifico.

    Args:
        departamento: Nombre del departamento

    Returns:
        ExtensionTelefonica si existe, None si no
    """
    departamento = departamento.lower()
    for ext in DIRECTORIO_TELEFONICO.values():
        if departamento in ext.departamento.lower():
            return ext
    return None


def listar_directorio_telefonico() -> str:
    """
    Genera un listado formateado del directorio telefonico completo.

    Returns:
        String formateado con el directorio completo
    """
    lineas = []
    lineas.append("\n" + "=" * 60)
    lineas.append("       DIRECTORIO TELEFONICO - CEDIS CANCUN 427")
    lineas.append("=" * 60)
    lineas.append(f"{'Ext.':<8} {'Departamento':<25} {'Colaborador':<20}")
    lineas.append("-" * 60)

    for ext in DIRECTORIO_TELEFONICO.values():
        colaborador = ext.colaborador if ext.colaborador else ""
        lineas.append(f"{ext.extension:<8} {ext.departamento:<25} {colaborador:<20}")

    lineas.append("=" * 60)
    return "\n".join(lineas)


def buscar_contacto(termino: str) -> List[ContactoImportante]:
    """
    Busca contactos importantes por nombre, departamento o razon.

    Args:
        termino: Termino de busqueda

    Returns:
        Lista de contactos que coinciden
    """
    termino = termino.lower()
    resultados = []

    for contacto in CONTACTOS_IMPORTANTES:
        if (termino in contacto.nombre.lower() or
            termino in contacto.departamento.lower() or
            termino in contacto.razon_contacto.lower()):
            resultados.append(contacto)

    return resultados


def listar_contactos_importantes() -> str:
    """
    Genera un listado formateado de contactos importantes.

    Returns:
        String formateado con los contactos
    """
    lineas = []
    lineas.append("\n" + "=" * 80)
    lineas.append("          CONTACTOS IMPORTANTES - CEDIS CANCUN 427")
    lineas.append("=" * 80)

    for contacto in CONTACTOS_IMPORTANTES:
        lineas.append(f"\n{contacto.nombre}")
        lineas.append(f"  Tel: {contacto.telefono}")
        lineas.append(f"  Depto: {contacto.departamento}")
        lineas.append(f"  Para: {contacto.razon_contacto}")

    lineas.append("\n" + "=" * 80)
    return "\n".join(lineas)


def obtener_ip_etiquetadora(nombre: str) -> Optional[EquipoIP]:
    """
    Obtiene la configuracion IP de una etiquetadora.

    Args:
        nombre: Nombre de la etiquetadora (ej: PRTECAN51)

    Returns:
        EquipoIP si existe, None si no
    """
    nombre = nombre.upper()
    return IPS_ETIQUETADORAS.get(nombre)


def listar_etiquetadoras() -> str:
    """
    Genera un listado de etiquetadoras con sus IPs.

    Returns:
        String formateado con las etiquetadoras
    """
    lineas = []
    lineas.append("\n" + "=" * 50)
    lineas.append("    ETIQUETADORAS - CEDIS CANCUN 427")
    lineas.append("=" * 50)
    lineas.append(f"{'Nombre':<15} {'IP':<18} {'Ubicacion':<15}")
    lineas.append("-" * 50)

    for equipo in IPS_ETIQUETADORAS.values():
        lineas.append(f"{equipo.nombre:<15} {equipo.ip:<18} {equipo.ubicacion:<15}")

    lineas.append("=" * 50)
    return "\n".join(lineas)


def obtener_atajo_tecla_f(numero: int) -> str:
    """
    Obtiene la combinacion de teclas para F13-F24.

    Args:
        numero: Numero de tecla F (13-24)

    Returns:
        Combinacion de teclas equivalente
    """
    if 13 <= numero <= 24:
        return TECLAS_F_EXTENDIDAS.get(f'F{numero}', 'No disponible')
    return f'F{numero} (tecla directa)'


def listar_atajos_teclado() -> str:
    """
    Genera un listado de atajos de teclado para WM.

    Returns:
        String formateado con los atajos
    """
    lineas = []
    lineas.append("\n" + "=" * 70)
    lineas.append("         ATAJOS DE TECLADO WM - CEDIS CANCUN 427")
    lineas.append("=" * 70)
    lineas.append(f"{'Combinacion':<20} {'Accion':<30} {'Contexto':<15}")
    lineas.append("-" * 70)

    for atajo in ATAJOS_TECLADO_WM:
        lineas.append(f"{atajo.combinacion:<20} {atajo.accion:<30} {atajo.contexto:<15}")
        if atajo.notas:
            lineas.append(f"   Nota: {atajo.notas}")

    lineas.append("\n" + "-" * 70)
    lineas.append("TECLAS F EXTENDIDAS (F13-F24):")
    lineas.append("-" * 70)
    for tecla, combo in TECLAS_F_EXTENDIDAS.items():
        lineas.append(f"  {tecla} = {combo}")

    lineas.append("=" * 70)
    return "\n".join(lineas)


def obtener_ruta_menu(nombre_menu: str) -> Optional[MenuWM]:
    """
    Obtiene la ruta de navegacion de un menu WM.

    Args:
        nombre_menu: Nombre o clave del menu

    Returns:
        MenuWM si existe, None si no
    """
    nombre = nombre_menu.lower()

    # Buscar por clave
    if nombre in MENUS_WM:
        return MENUS_WM[nombre]

    # Buscar por nombre o descripcion
    for menu in MENUS_WM.values():
        if nombre in menu.nombre.lower() or nombre in menu.descripcion.lower():
            return menu

    return None


def listar_menus_wm() -> str:
    """
    Genera un listado de menus y rutas de navegacion WM.

    Returns:
        String formateado con los menus
    """
    lineas = []
    lineas.append("\n" + "=" * 70)
    lineas.append("         MENUS Y NAVEGACION WM - CEDIS CANCUN 427")
    lineas.append("=" * 70)

    for clave, menu in MENUS_WM.items():
        lineas.append(f"\n[{clave.upper()}]")
        lineas.append(f"  Nombre: {menu.nombre}")
        lineas.append(f"  Ruta: {menu.ruta}")
        lineas.append(f"  Descripcion: {menu.descripcion}")
        if menu.opciones_principales:
            lineas.append(f"  Opciones: {', '.join(menu.opciones_principales)}")

    lineas.append("\n" + "=" * 70)
    return "\n".join(lineas)


def obtener_info_usuario_especial(usuario: str) -> Optional[Dict]:
    """
    Obtiene informacion de un usuario especial del sistema.

    Args:
        usuario: Nombre del usuario (HABILITA, MODREPORT)

    Returns:
        Diccionario con informacion del usuario
    """
    return USUARIOS_ESPECIALES.get(usuario.upper())


def listar_usuarios_especiales() -> str:
    """
    Genera un listado de usuarios especiales del sistema.

    Returns:
        String formateado con los usuarios especiales
    """
    lineas = []
    lineas.append("\n" + "=" * 60)
    lineas.append("    USUARIOS ESPECIALES WM - CEDIS CANCUN 427")
    lineas.append("=" * 60)

    for nombre, info in USUARIOS_ESPECIALES.items():
        lineas.append(f"\n[{nombre}]")
        for clave, valor in info.items():
            lineas.append(f"  {clave}: {valor}")

    lineas.append("\n" + "=" * 60)
    return "\n".join(lineas)


def obtener_info_hand_held() -> str:
    """
    Genera informacion util sobre Hand Helds/RF.

    Returns:
        String formateado con informacion de Hand Helds
    """
    lineas = []
    lineas.append("\n" + "=" * 60)
    lineas.append("       INFORMACION HAND HELDS - CEDIS CANCUN 427")
    lineas.append("=" * 60)

    lineas.append("\nINFORMACION GENERAL:")
    for clave, valor in HAND_HELD_INFO.items():
        clave_formateada = clave.replace('_', ' ').title()
        lineas.append(f"  {clave_formateada}: {valor}")

    lineas.append("\nATAJOS EN RF:")
    for combo, accion in ATAJOS_RF.items():
        lineas.append(f"  {combo}: {accion}")

    lineas.append("\n" + "=" * 60)
    return "\n".join(lineas)


def guia_habilitar_usuario() -> str:
    """
    Genera una guia paso a paso para habilitar usuarios.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: HABILITAR USUARIOS EN WM - CEDIS CANCUN 427
================================================================================

METODO 1: Con usuario HABILITA
------------------------------
1. Iniciar sesion en WM con: usuario=habilita, password=habilita
2. Colocar el usuario a habilitar (Q + kronos) en el campo "Usuario"
3. Presionar F7 para habilitar

METODO 2: Desde Menu Administrador
----------------------------------
1. Iniciar sesion con usuario normal
2. Presionar ESC para acceder al Menu Administrador
3. En "Asignacion de parametro" colocar el numero de usuario
4. Presionar F5 para habilitar

SI USUARIO HABILITA ESTA DESHABILITADO:
---------------------------------------
1. Iniciar sesion con usuario MODREPORT
2. Presionar ESC para Menu Especial
3. Seleccionar opcion 5 para habilitar usuario HABILITA

================================================================================
"""
    return guia


def guia_crear_usuario() -> str:
    """
    Genera una guia paso a paso para crear usuarios.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: CREAR USUARIOS EN WM - CEDIS CANCUN 427
================================================================================

REQUISITOS PREVIOS:
-------------------
- Correos de solicitud con VoBo (Visto Bueno)
- Maximo 70 usuarios con almacen 427
- Verificar disponibilidad con QRY "USR_WM_427"

PASOS:
------
1. Ingresar a WM y navegar: 20 -> 7 (Maestro de Usuarios)

2. Buscar usuario de referencia (copiar de ticket de Intranet)

3. Seleccionar opcion 5 (Mostrar) para verificar datos del usuario referencia

4. Seleccionar opcion 3 (Copiar) en el usuario referencia

5. Cambiar el usuario nuevo: Q + kronos del colaborador

6. Completar datos:
   - Contrasena temporal: chedrau123
   - Nombre del colaborador
   - Area y puesto

7. Guardar con F16 (Shift + F4)

8. Ir al Menu Administrador (ESC):
   - Pegar usuario (Q + kronos)
   - Pegar nombre
   - Presionar F2 para crear

9. El sistema generara la contrasena automatica

10. Llenar formato de Responsiva de Usuario e imprimir

11. Cerrar ticket en Intranet

================================================================================
"""
    return guia


def guia_cambiar_contrasena() -> str:
    """
    Genera una guia para cambiar contrasenas.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: CAMBIAR CONTRASENA DE USUARIOS - CEDIS CANCUN 427
================================================================================

PASOS:
------
1. Iniciar sesion en WM con usuario administrador

2. Presionar ESC para acceder al Menu Administrador

3. Colocar el usuario en "Asignacion de parametro"

4. Presionar F3 para asignar nueva contrasena

5. El sistema generara una nueva contrasena automaticamente

================================================================================
"""
    return guia


def guia_eliminar_usuario() -> str:
    """
    Genera una guia para eliminar usuarios.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: ELIMINAR USUARIOS EN WM - CEDIS CANCUN 427
================================================================================

IMPORTANTE: Solo eliminar usuarios del listado de bajas proporcionado por RH

PASOS:
------
1. Solicitar a RH el listado de bajas del mes

2. Ingresar a WM y navegar: 20 -> 7 (Maestro de Usuarios)

3. Buscar usuario: Q + kronos del colaborador

4. VERIFICAR que el nombre coincida con el listado de bajas

5. Seleccionar opcion 4 (Eliminar) + Enter

6. Confirmar con Shift + F4

ADVERTENCIA: La eliminacion es PERMANENTE. Siempre verificar antes de confirmar.

================================================================================
"""
    return guia


def guia_verificar_errores() -> str:
    """
    Genera una guia para verificar errores en WM.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: VERIFICAR ERRORES EN WM - CEDIS CANCUN 427
================================================================================

VERIFICAR USUARIO ATRAPADO:
---------------------------
1. Ingresar a WM: 20 -> 106 (Info errores trabajo)

2. Indicar fecha y hora donde buscar errores

3. Buscar errores con nombre "Inmv regist"

4. Seleccionar opcion 2 en el error

5. El usuario problematico aparece en "Datos/ID mj:"

6. Si es de otro CEDIS, solicitar al area que el usuario se salga

VERIFICAR ERRORES GENERALES:
----------------------------
1. Ingresar a WM: 20 -> 111 (Info errores detalle)

2. Revisar listado de errores

================================================================================
"""
    return guia


def guia_imprimir_wm() -> str:
    """
    Genera una guia para imprimir desde WM.

    Returns:
        String con la guia formateada
    """
    guia = """
================================================================================
    GUIA: IMPRIMIR DESDE WM - CEDIS CANCUN 427
================================================================================

IMPRIMIR CARTONES DE PRUEBA:
----------------------------
1. Navegar: 11 -> 67 -> 2

2. Colocar cualquier dato y presionar Enter

3. Ir al Menu Administrador (ESC)

4. Seleccionar opcion 10 (Administrar Spool)

5. En los trabajos listados, dar opcion 9 al trabajo a imprimir

6. Asociar al PRT de la etiquetadora activa:
   - PRTECAN51 -> IP 172.19.69.51
   - PRTECAN52 -> IP 172.19.69.36
   - PRTECAN53 -> IP 172.19.69.53
   - PRTECAN54 -> IP 172.19.69.54

AGREGAR/HABILITAR ETIQUETADORA:
-------------------------------
1. Iniciar sesion con: usuario=habilita, password=habilita

2. Colocar nombre de impresora (PRTECAN51, etc.)

3. La impresora cambiara de estado END a STR

ESTADOS DE IMPRESORA:
- END: Deshabilitada
- STR: Habilitada/En Pausa
- MSGW: Danada

VER TODAS LAS IMPRESORAS:
1. Presionar F22 (Shift + F10) para ver listado

================================================================================
"""
    return guia


# ===============================================================================
# FUNCION DE AYUDA PRINCIPAL
# ===============================================================================

def mostrar_ayuda_sac() -> str:
    """
    Muestra ayuda general del modulo de funciones CEDIS.

    Returns:
        String con el menu de ayuda
    """
    ayuda = """
================================================================================
     MODULO DE FUNCIONES BASICAS CEDIS - SAC
     Sistema de Automatizacion de Consultas - CEDIS Cancun 427
================================================================================

FUNCIONES DISPONIBLES:
----------------------

DIRECTORIO Y CONTACTOS:
  buscar_extension(termino)         - Buscar extension telefonica
  obtener_extension(departamento)   - Obtener extension de un depto
  listar_directorio_telefonico()    - Mostrar directorio completo
  buscar_contacto(termino)          - Buscar contacto importante
  listar_contactos_importantes()    - Mostrar contactos importantes

EQUIPOS Y CONFIGURACION:
  obtener_ip_etiquetadora(nombre)   - Obtener IP de etiquetadora
  listar_etiquetadoras()            - Mostrar todas las etiquetadoras

ATAJOS Y NAVEGACION WM:
  obtener_atajo_tecla_f(numero)     - Obtener combinacion para F13-F24
  listar_atajos_teclado()           - Mostrar atajos de teclado
  obtener_ruta_menu(nombre)         - Obtener ruta de menu WM
  listar_menus_wm()                 - Mostrar menus y rutas WM
  obtener_info_usuario_especial(u)  - Info de usuario especial
  listar_usuarios_especiales()      - Mostrar usuarios especiales

HAND HELDS:
  obtener_info_hand_held()          - Informacion de RF/Hand Helds

GUIAS PASO A PASO:
  guia_habilitar_usuario()          - Como habilitar usuarios
  guia_crear_usuario()              - Como crear usuarios
  guia_cambiar_contrasena()         - Como cambiar contrasenas
  guia_eliminar_usuario()           - Como eliminar usuarios
  guia_verificar_errores()          - Como verificar errores
  guia_imprimir_wm()                - Como imprimir desde WM

================================================================================
     Desarrollado por: Julian Alexander Juarez Alvarado (ADMJAJA)
     Jefe de Sistemas - CEDIS Chedraui Logistica Cancun
================================================================================
"""
    return ayuda


# ===============================================================================
# FUNCION DE DEMOSTRACION
# ===============================================================================

def demo_funciones_cedis():
    """Ejecuta una demostracion de las funciones del modulo"""
    print("\n" + "=" * 70)
    print("       DEMO: MODULO DE FUNCIONES BASICAS CEDIS")
    print("=" * 70)

    # Mostrar ayuda
    print(mostrar_ayuda_sac())

    print("\n--- EJEMPLO: Directorio Telefonico ---")
    print(listar_directorio_telefonico())

    print("\n--- EJEMPLO: Buscar extension 'sistemas' ---")
    resultados = buscar_extension('sistemas')
    for ext in resultados:
        print(f"  Encontrado: {ext.extension} - {ext.departamento}")

    print("\n--- EJEMPLO: Etiquetadoras ---")
    print(listar_etiquetadoras())

    print("\n--- EJEMPLO: Atajos de Teclado ---")
    print(listar_atajos_teclado())

    print("\n--- EJEMPLO: Menus WM ---")
    print(listar_menus_wm())

    print("\n--- EJEMPLO: Guia Habilitar Usuario ---")
    print(guia_habilitar_usuario())

    print("\nDemo completada!")


# ===============================================================================
# EXPORTACIONES
# ===============================================================================

__all__ = [
    # Constantes
    'CEDIS_CODE',
    'CEDIS_NAME',
    'VERSION_MODULO',
    # Enumeraciones
    'TipoContacto',
    'TipoEquipo',
    'EstadoDispositivo',
    # Dataclasses
    'ExtensionTelefonica',
    'ContactoImportante',
    'EquipoIP',
    'AtajoTeclado',
    'MenuWM',
    # Datos
    'DIRECTORIO_TELEFONICO',
    'CONTACTOS_IMPORTANTES',
    'IPS_ETIQUETADORAS',
    'ATAJOS_TECLADO_WM',
    'TECLAS_F_EXTENDIDAS',
    'MENUS_WM',
    'USUARIOS_ESPECIALES',
    'OPCIONES_USUARIO_WM',
    'HAND_HELD_INFO',
    'ATAJOS_RF',
    # Funciones de busqueda
    'buscar_extension',
    'obtener_extension',
    'listar_directorio_telefonico',
    'buscar_contacto',
    'listar_contactos_importantes',
    'obtener_ip_etiquetadora',
    'listar_etiquetadoras',
    'obtener_atajo_tecla_f',
    'listar_atajos_teclado',
    'obtener_ruta_menu',
    'listar_menus_wm',
    'obtener_info_usuario_especial',
    'listar_usuarios_especiales',
    'obtener_info_hand_held',
    # Guias
    'guia_habilitar_usuario',
    'guia_crear_usuario',
    'guia_cambiar_contrasena',
    'guia_eliminar_usuario',
    'guia_verificar_errores',
    'guia_imprimir_wm',
    # Ayuda
    'mostrar_ayuda_sac',
    'demo_funciones_cedis',
]


if __name__ == '__main__':
    demo_funciones_cedis()
