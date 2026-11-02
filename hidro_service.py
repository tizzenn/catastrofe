"""Cliente del WFS público del MITECO (GeoServer nacional de aguas) para
consultar datos hídricos por punto.

No depende de PyQGIS. Es un servicio nacional único que cubre toda España,
incluidas las cuencas intracomunitarias (Cataluña, País Vasco...), porque
son los datos que España reporta consolidados a la UE.
Catálogo de capas: https://www.miteco.gob.es/es/cartografia-y-sig/ide/directorio_datos_servicios/agua/wms-inspire-agua.html
"""
import json
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import urllib.request

WFS_URL = "https://gis.miteco.gob.es/geoserver/agua/wfs"
USER_AGENT = "Mozilla/5.0 (QGIS catastrofe plugin)"
TIMEOUT = 8

CAPAS_ZONA_INUNDABLE = [
    ("agua:DPH_Estimado", "dominio público hidráulico (estimado)"),
    ("agua:ZI_Laminas_ZFP", "zona de flujo preferente"),
    ("agua:Zi_laminas_q10", "zona inundable, periodo de retorno 10 años"),
    ("agua:Zi_laminas_q100", "zona inundable, periodo de retorno 100 años"),
    ("agua:Zi_laminas_q500", "zona inundable, periodo de retorno 500 años"),
]


class HidroLookupError(Exception):
    """No se pudo completar la consulta al servicio hídrico del MITECO."""


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _get_feature(type_name: str, lon: float, lat: float, fetch=_fetch) -> list:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "outputFormat": "application/json",
        "cql_filter": f"INTERSECTS(shape,SRID=4326;POINT({lon} {lat}))",
    }
    url = WFS_URL + "?" + urllib.parse.urlencode(params)
    try:
        data = fetch(url)
    except Exception as exc:
        raise HidroLookupError(f"No se pudo conectar con el servicio del MITECO: {exc}") from exc
    try:
        return json.loads(data)["features"]
    except Exception as exc:
        raise HidroLookupError(f"Respuesta inesperada del servicio del MITECO: {exc}") from exc


def acuifero_en_punto(lon: float, lat: float, fetch=_fetch):
    """Masa de agua subterránea (acuífero) en ese punto WGS84, o None si no hay ninguna."""
    features = _get_feature("agua:masas_aguasub_2027", lon, lat, fetch=fetch)
    if not features:
        return None
    propiedades = features[0]["properties"]
    return {
        "nombre": propiedades.get("nom_masa"),
        "codigo": propiedades.get("cod_masa"),
        "demarcacion": propiedades.get("nom_ddhh"),
    }


def zonas_inundables_en_punto(lon: float, lat: float, fetch=_fetch) -> list:
    """Descripciones de las zonas inundables/DPH que afectan a ese punto (lista vacía si ninguna)."""
    # Cinco capas independientes: se consultan en paralelo para que la espera
    # sea la de la más lenta y no la suma de todas.
    with ThreadPoolExecutor(max_workers=len(CAPAS_ZONA_INUNDABLE)) as pool:
        hay = list(pool.map(lambda capa: bool(_get_feature(capa[0], lon, lat, fetch=fetch)), CAPAS_ZONA_INUNDABLE))
    return [etiqueta for (_, etiqueta), afecta in zip(CAPAS_ZONA_INUNDABLE, hay) if afecta]
