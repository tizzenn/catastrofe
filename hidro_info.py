from .hidro_service import HidroLookupError, acuifero_en_punto, zonas_inundables_en_punto
from .settings import mostrar_acuifero, mostrar_zona_inundable


def resumen_hidrico(lon: float, lat: float) -> str:
    """Texto con los datos hídricos activados en Ajustes para ese punto.

    Cadena vacía si ambos están desactivados o no hay nada que mostrar (para
    no molestar cuando no aporta información). No lanza excepción: un fallo
    de red en el servicio del MITECO no debe impedir abrir la ficha del
    Catastro, así que se convierte en un aviso dentro del propio texto.
    """
    if not mostrar_acuifero() and not mostrar_zona_inundable():
        return ""
    partes = []
    try:
        if mostrar_acuifero():
            acuifero = acuifero_en_punto(lon, lat)
            if acuifero:
                partes.append(f"Acuífero: {acuifero['nombre']} ({acuifero['demarcacion']})")
        if mostrar_zona_inundable():
            zonas = zonas_inundables_en_punto(lon, lat)
            if zonas:
                partes.append("Zona inundable: " + ", ".join(zonas))
    except HidroLookupError as exc:
        return f"Datos hídricos no disponibles ({exc})"
    return " · ".join(partes)
