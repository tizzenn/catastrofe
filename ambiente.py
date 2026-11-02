from .hidro_info import resumen_hidrico
from .natura_info import resumen_red_natura


def lineas_ambientales(lon: float, lat: float) -> list:
    """Líneas de texto con los datos ambientales activados en Ajustes
    (acuífero, zona inundable, Red Natura 2000) para un punto WGS84.
    Lista vacía si no hay nada que mostrar."""
    return [texto for texto in (resumen_hidrico(lon, lat), resumen_red_natura(lon, lat)) if texto]
