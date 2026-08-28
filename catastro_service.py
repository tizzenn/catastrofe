"""Cliente del servicio web libre de la Sede Electrónica del Catastro.

No depende de PyQGIS: se puede probar con Python normal y corriente.
Documentación oficial: https://www.catastro.hacienda.gob.es/ws/Webservices_Libres.pdf
"""
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

COORDENADAS_SVC = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/rest"
CALLEJERO_SVC = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/rest"
INSPIRE_CP_SVC = "http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"
NS = {"cat": "http://www.catastro.meh.es/"}
GML_NS = {"gml": "http://www.opengis.net/gml/3.2"}
USER_AGENT = "Mozilla/5.0 (QGIS catastro-parcela plugin)"
TIMEOUT = 8


class CatastroLookupError(Exception):
    """La consulta al Catastro no ha dado una referencia catastral utilizable."""


def normalizar_referencia(entrada: str) -> str:
    """Normaliza una referencia catastral escrita o pegada a mano.

    La referencia "completa" tiene 20 caracteres (14 de parcela + 4 de
    unidad constructiva + 2 de control), y así es como suele aparecer en
    recibos del IBI o escrituras, a veces con espacios entre grupos. Pero
    los 14 primeros ya identifican la parcela sin ambigüedad (el resto no
    hace falta para pedir su ficha gráfica), así que aceptamos cualquier
    longitud a partir de 14 y nos quedamos con esos 14 primeros caracteres.
    """
    limpia = "".join(entrada.split()).upper()
    if len(limpia) < 14:
        raise CatastroLookupError("La referencia catastral debe tener al menos 14 caracteres.")
    return limpia[:14]


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _check_errors(root: ET.Element) -> None:
    err = root.find(".//cat:lerr/cat:err", NS)
    if err is not None:
        des = err.findtext("cat:des", default="error desconocido", namespaces=NS)
        raise CatastroLookupError(des.capitalize())


def refcat_en_coordenadas(lon: float, lat: float, fetch=_fetch) -> str:
    """Referencia catastral (14 posiciones) de la parcela en esas coordenadas WGS84."""
    url = COORDENADAS_SVC + "/Consulta_RCCOOR?" + urllib.parse.urlencode(
        {"SRS": "EPSG:4326", "CoorX": lon, "CoorY": lat}
    )
    root = ET.fromstring(_fetch_or_raise(url, fetch))
    _check_errors(root)
    pc1 = root.findtext(".//cat:pc/cat:pc1", namespaces=NS)
    pc2 = root.findtext(".//cat:pc/cat:pc2", namespaces=NS)
    if not pc1 or not pc2:
        raise CatastroLookupError("El Catastro no ha devuelto una referencia catastral.")
    return pc1 + pc2


def _consulta_dnprc(refcat: str, fetch=_fetch) -> ET.Element:
    url = CALLEJERO_SVC + "/Consulta_DNPRC?" + urllib.parse.urlencode({"RefCat": refcat})
    root = ET.fromstring(_fetch_or_raise(url, fetch))
    _check_errors(root)
    return root


def _consulta_dnprc_bi(refcat14: str, fetch=_fetch):
    """Consulta_DNPRC como resultado único: (root, nodo <bi>).

    Si la referencia de 14 caracteres corresponde a un inmueble con varias
    unidades catastrales (p.ej. un edificio con varios locales o pisos,
    división horizontal), Catastro devuelve una lista (``lrcdnp``) sin URL
    de ficha ni naturaleza rústica/urbana. En ese caso se repite la consulta
    con la referencia completa (20 caracteres) de la primera unidad, que sí
    da un resultado único con toda la información.
    """
    root = _consulta_dnprc(refcat14, fetch=fetch)
    bi = root.find(".//cat:bico/cat:bi", NS)
    if bi is not None:
        return root, bi

    primera_rc = root.find(".//cat:lrcdnp/cat:rcdnp/cat:rc", NS)
    if primera_rc is None:
        raise CatastroLookupError("El Catastro no ha devuelto datos para esa referencia.")
    campos = ("pc1", "pc2", "car", "cc1", "cc2")
    refcat20 = "".join(primera_rc.findtext(f"cat:{campo}", default="", namespaces=NS) for campo in campos)
    root20 = _consulta_dnprc(refcat20, fetch=fetch)
    bi20 = root20.find(".//cat:bico/cat:bi", NS)
    if bi20 is None:
        raise CatastroLookupError("El Catastro no ha devuelto un resultado único para esa referencia.")
    return root20, bi20


NATURALEZA = {"RU": "Rústica", "UR": "Urbana"}


def datos_ficha(refcat14: str, fetch=_fetch) -> dict:
    """URL de la ficha gráfica y naturaleza (Rústica/Urbana) de la parcela,
    en una sola consulta a Consulta_DNPRC."""
    root, bi = _consulta_dnprc_bi(refcat14, fetch=fetch)
    igraf = root.findtext(".//cat:finca/cat:infgraf/cat:igraf", namespaces=NS)
    if not igraf:
        raise CatastroLookupError("El Catastro no ha devuelto un enlace a la ficha gráfica.")
    cn = bi.findtext("cat:idbi/cat:cn", namespaces=NS)
    return {"url": igraf, "naturaleza": NATURALEZA.get(cn)}


def url_ficha_grafica(refcat14: str, fetch=_fetch) -> str:
    """URL de la Sede Electrónica del Catastro (visor gráfico) para esa referencia."""
    return datos_ficha(refcat14, fetch=fetch)["url"]


def naturaleza_parcela(refcat14: str, fetch=_fetch):
    """'Rústica' o 'Urbana' según el Catastro, o None si no viene informado."""
    _, bi = _consulta_dnprc_bi(refcat14, fetch=fetch)
    return NATURALEZA.get(bi.findtext("cat:idbi/cat:cn", namespaces=NS))


def _fetch_or_raise(url: str, fetch) -> bytes:
    try:
        return fetch(url)
    except CatastroLookupError:
        raise
    except Exception as exc:
        raise CatastroLookupError(f"No se pudo conectar con el Catastro: {exc}") from exc


def datos_sedecatastro_para_punto(lon: float, lat: float, fetch=_fetch) -> dict:
    """Punto en WGS84 (lon, lat) -> URL de la ficha gráfica y naturaleza de esa parcela."""
    refcat = refcat_en_coordenadas(lon, lat, fetch=fetch)
    return datos_ficha(refcat, fetch=fetch)


def url_sedecatastro_para_punto(lon: float, lat: float, fetch=_fetch) -> str:
    """Punto en WGS84 (lon, lat) -> URL de la ficha gráfica de esa parcela en Sede Catastro."""
    return datos_sedecatastro_para_punto(lon, lat, fetch=fetch)["url"]


def punto_de_referencia(refcat14: str, fetch=_fetch) -> tuple:
    """Referencia catastral -> (lon, lat) WGS84 del centroide de la parcela.

    Es la operación inversa de refcat_en_coordenadas. Provincia y Municipio
    son opcionales para esta consulta (RefCat basta para desambiguar).
    """
    url = COORDENADAS_SVC + "/Consulta_CPMRC?" + urllib.parse.urlencode(
        {"SRS": "EPSG:4326", "RefCat": refcat14}
    )
    root = ET.fromstring(_fetch_or_raise(url, fetch))
    _check_errors(root)
    lon = root.findtext(".//cat:coord/cat:geo/cat:xcen", namespaces=NS)
    lat = root.findtext(".//cat:coord/cat:geo/cat:ycen", namespaces=NS)
    if not lon or not lat:
        raise CatastroLookupError("El Catastro no ha devuelto coordenadas para esa referencia.")
    return float(lon), float(lat)


def refcats_en_poligono_parcela(provincia: str, municipio: str, poligono: str, parcela: str, fetch=_fetch) -> list:
    """Referencias catastrales (14 posiciones) de un polígono/parcela rústico.

    Provincia y Municipio son la denominación en texto (p.ej. "VALENCIA",
    "GODELLETA"), no un código INE. Puede haber más de una referencia si la
    parcela tiene varias fincas asociadas (p.ej. una rústica y otra con
    edificación): se deduplican por los 14 caracteres, que es lo único que
    hace falta para pedir la ficha gráfica.
    """
    url = CALLEJERO_SVC + "/Consulta_DNPPP?" + urllib.parse.urlencode(
        {"Provincia": provincia, "Municipio": municipio, "Poligono": poligono, "Parcela": parcela}
    )
    root = ET.fromstring(_fetch_or_raise(url, fetch))
    _check_errors(root)
    refcats = []
    for rc in root.findall(".//cat:rc", NS):
        pc1 = rc.findtext("cat:pc1", namespaces=NS)
        pc2 = rc.findtext("cat:pc2", namespaces=NS)
        if pc1 and pc2 and pc1 + pc2 not in refcats:
            refcats.append(pc1 + pc2)
    if not refcats:
        raise CatastroLookupError("El Catastro no ha devuelto ninguna referencia para ese polígono y parcela.")
    return refcats


def geometria_parcela(refcat14: str, fetch=_fetch) -> list:
    """Contorno (lon, lat) de la parcela, vía el WFS INSPIRE de parcelas
    catastrales (servicio distinto de los anteriores, sin relación con el
    PDF de Webservices_Libres). Si la parcela tiene varios recintos
    separados, se devuelve solo el primero.

    Pensada para usarse solo con un refcat14 ya validado por otra consulta
    (RCCOOR/DNPRC/DNPPP): con una referencia inventada este servicio puede
    devolver parcelas sin relación en vez de un error, así que no sirve
    como forma de comprobar si una referencia existe.
    """
    url = INSPIRE_CP_SVC + "?" + urllib.parse.urlencode(
        {
            "service": "wfs",
            "version": "2.0.0",
            "REQUEST": "GetFeature",
            "STOREDQUERIE_ID": "GetParcel",
            "refcat": refcat14,
            "srsname": "EPSG::4326",
        }
    )
    root = ET.fromstring(_fetch_or_raise(url, fetch))
    pos_list = root.find(".//gml:posList", GML_NS)
    if pos_list is None or not pos_list.text:
        raise CatastroLookupError("El Catastro no ha devuelto el contorno de esa parcela.")
    valores = [float(v) for v in pos_list.text.split()]
    # El WFS INSPIRE da pares (lat, lon); los invertimos a (lon, lat).
    return [(valores[i + 1], valores[i]) for i in range(0, len(valores), 2)]
