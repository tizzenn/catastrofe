from .natura_service import espacios_en_punto
from .settings import mostrar_red_natura


def resumen_red_natura(lon: float, lat: float) -> str:
    """Texto sobre la Red Natura 2000 en ese punto, si está activado en
    Ajustes. Cadena vacía si está desactivado o no hay nada que mostrar.
    No lanza excepción: un fallo de red no debe impedir el resto del flujo.
    """
    if not mostrar_red_natura():
        return ""
    try:
        espacios = espacios_en_punto(lon, lat)
    except Exception as exc:
        return f"Red Natura 2000 no disponible ({exc})"
    if not espacios:
        return ""
    return "Red Natura 2000: " + ", ".join(espacios)
