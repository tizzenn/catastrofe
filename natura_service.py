"""Cliente del WFS de la Red Natura 2000 (IEPNB, geoserver ligado al MITECO)
para consultar por punto.

No depende de PyQGIS. Servicio distinto del hídrico (hidro_service.py):
aquí solo se marcan espacios protegidos (ZEC/ZEPA), sin relación con agua.
"""
import json
import urllib.parse
import urllib.request

WFS_URL = "https://geoserver.iepnb.es/geoserver/RN2000/wfs"
TYPE_NAME = "RN2000:rn2000_2024"
USER_AGENT = "Mozilla/5.0 (QGIS catastrofe plugin)"
TIMEOUT = 8


class RedNaturaLookupError(Exception):
    """No se pudo completar la consulta al WFS de Red Natura 2000."""


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def espacios_en_punto(lon: float, lat: float, fetch=_fetch) -> list:
    """Espacios de la Red Natura 2000 (con su figura de protección) que
    incluyen ese punto WGS84. Lista vacía si no hay ninguno."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": TYPE_NAME,
        "outputFormat": "application/json",
        "cql_filter": f"INTERSECTS(geom,SRID=4326;POINT({lon} {lat}))",
    }
    url = WFS_URL + "?" + urllib.parse.urlencode(params)
    try:
        data = fetch(url)
    except Exception as exc:
        raise RedNaturaLookupError(f"No se pudo conectar con el servicio de Red Natura 2000: {exc}") from exc
    try:
        features = json.loads(data)["features"]
    except Exception as exc:
        raise RedNaturaLookupError(f"Respuesta inesperada del servicio de Red Natura 2000: {exc}") from exc

    espacios = []
    for feature in features:
        propiedades = feature.get("properties", {})
        if not propiedades.get("es_rn2000", True):
            continue
        nombre = propiedades.get("nombre")
        figura = propiedades.get("desc_figura")
        etiqueta = f"{nombre} ({figura})" if nombre and figura else (nombre or figura)
        if etiqueta and etiqueta not in espacios:
            espacios.append(etiqueta)
    return espacios
