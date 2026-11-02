from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt

from .catastro_service import CatastroLookupError, refcat_en_coordenadas

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


class CatastroClickTool(QgsMapTool):
    """Consulta la parcela bajo el cursor y la envía al panel de resultados.

    La parcela se trata igual que una búsqueda manual: respeta el modo
    acumulativo, dibuja el perímetro y ofrece los botones de copiar y de
    abrir la ficha (nunca abre el navegador por sí sola).
    """

    def __init__(self, canvas, iface, panel):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        self.panel = panel

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
            refcat = refcat_en_coordenadas(point_wgs84.x(), point_wgs84.y())
        except CatastroLookupError as exc:
            self.iface.messageBar().pushWarning("Catastro", str(exc))
            return
        self.panel.mostrar_refcat(refcat)
