from qgis.core import QgsSettings
from qgis.PyQt.QtGui import QColor

CLAVE_ACUIFERO = "Catastrofe/mostrar_acuifero"
CLAVE_ZONA_INUNDABLE = "Catastrofe/mostrar_zona_inundable"

CLAVE_BORDE_COLOR = "Catastrofe/borde_color"
CLAVE_BORDE_ANCHO = "Catastrofe/borde_ancho"
CLAVE_RELLENO_ACTIVADO = "Catastrofe/relleno_activado"
CLAVE_RELLENO_COLOR = "Catastrofe/relleno_color"
CLAVE_RELLENO_OPACIDAD = "Catastrofe/relleno_opacidad"

POR_DEFECTO_BORDE_COLOR = "#e07020"
POR_DEFECTO_BORDE_ANCHO = 3
POR_DEFECTO_RELLENO_ACTIVADO = False
POR_DEFECTO_RELLENO_COLOR = "#e07020"
POR_DEFECTO_RELLENO_OPACIDAD = 60  # 0-100 %


def mostrar_acuifero() -> bool:
    return QgsSettings().value(CLAVE_ACUIFERO, True, type=bool)


def mostrar_zona_inundable() -> bool:
    return QgsSettings().value(CLAVE_ZONA_INUNDABLE, True, type=bool)


def set_mostrar_acuifero(valor: bool) -> None:
    QgsSettings().setValue(CLAVE_ACUIFERO, valor)


def set_mostrar_zona_inundable(valor: bool) -> None:
    QgsSettings().setValue(CLAVE_ZONA_INUNDABLE, valor)


def color_borde() -> QColor:
    return QColor(QgsSettings().value(CLAVE_BORDE_COLOR, POR_DEFECTO_BORDE_COLOR, type=str))


def set_color_borde(color: QColor) -> None:
    QgsSettings().setValue(CLAVE_BORDE_COLOR, color.name())


def ancho_borde() -> int:
    return QgsSettings().value(CLAVE_BORDE_ANCHO, POR_DEFECTO_BORDE_ANCHO, type=int)


def set_ancho_borde(valor: int) -> None:
    QgsSettings().setValue(CLAVE_BORDE_ANCHO, valor)


def relleno_activado() -> bool:
    return QgsSettings().value(CLAVE_RELLENO_ACTIVADO, POR_DEFECTO_RELLENO_ACTIVADO, type=bool)


def set_relleno_activado(valor: bool) -> None:
    QgsSettings().setValue(CLAVE_RELLENO_ACTIVADO, valor)


def color_relleno() -> QColor:
    return QColor(QgsSettings().value(CLAVE_RELLENO_COLOR, POR_DEFECTO_RELLENO_COLOR, type=str))


def set_color_relleno(color: QColor) -> None:
    QgsSettings().setValue(CLAVE_RELLENO_COLOR, color.name())


def opacidad_relleno() -> int:
    """Opacidad del relleno interior, de 0 (transparente) a 100 (opaco)."""
    return QgsSettings().value(CLAVE_RELLENO_OPACIDAD, POR_DEFECTO_RELLENO_OPACIDAD, type=int)


def set_opacidad_relleno(valor: int) -> None:
    QgsSettings().setValue(CLAVE_RELLENO_OPACIDAD, valor)
