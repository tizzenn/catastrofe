from qgis.core import QgsSettings

CLAVE_ACUIFERO = "Catastrofe/mostrar_acuifero"
CLAVE_ZONA_INUNDABLE = "Catastrofe/mostrar_zona_inundable"


def mostrar_acuifero() -> bool:
    return QgsSettings().value(CLAVE_ACUIFERO, True, type=bool)


def mostrar_zona_inundable() -> bool:
    return QgsSettings().value(CLAVE_ZONA_INUNDABLE, True, type=bool)


def set_mostrar_acuifero(valor: bool) -> None:
    QgsSettings().setValue(CLAVE_ACUIFERO, valor)


def set_mostrar_zona_inundable(valor: bool) -> None:
    QgsSettings().setValue(CLAVE_ZONA_INUNDABLE, valor)
