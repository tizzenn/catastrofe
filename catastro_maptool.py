import webbrowser

from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt

from .catastro_service import CatastroLookupError, datos_sedecatastro_para_punto
from .hidro_info import resumen_hidrico
from .natura_info import resumen_red_natura

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


class CatastroClickTool(QgsMapTool):
    """Al pulsar sobre el lienzo, abre en el navegador la ficha de Sede Catastro
    de la parcela situada en ese punto."""

    def __init__(self, canvas, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface

    def canvasReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        point = self.toMapCoordinates(event.pos())
        project_crs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(project_crs, WGS84, QgsProject.instance())
        try:
            point_wgs84 = transform.transform(point)
        except Exception as exc:
            self.iface.messageBar().pushWarning("Catastro", f"Coordenadas no válidas: {exc}")
            return

        self.iface.messageBar().pushMessage(
            "Catastro", "Consultando parcela…", level=Qgis.MessageLevel.Info, duration=2
        )
        try:
            datos = datos_sedecatastro_para_punto(point_wgs84.x(), point_wgs84.y())
        except CatastroLookupError as exc:
            self.iface.messageBar().pushWarning("Catastro", str(exc))
            return

        webbrowser.open(datos["url"])

        partes = [
            f"Naturaleza: {datos['naturaleza']}" if datos["naturaleza"] else "",
            resumen_hidrico(point_wgs84.x(), point_wgs84.y()),
            resumen_red_natura(point_wgs84.x(), point_wgs84.y()),
        ]
        resumen = " · ".join(p for p in partes if p)
        if resumen:
            self.iface.messageBar().pushInfo("Catastrofe", resumen)
