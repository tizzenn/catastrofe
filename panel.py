from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .catastro_service import (
    CatastroLookupError,
    formato_poligono_parcela,
    geometria_parcela,
    naturaleza_y_referencia_completa,
    normalizar_referencia,
    punto_de_referencia,
    refcats_en_poligono_parcela,
)
from .hidro_info import resumen_hidrico
from .natura_info import resumen_red_natura
from .portapapeles import fila_copiable
from . import settings

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


class CatastrofePanel(QDockWidget):
    """Panel lateral: busca una parcela por referencia o por polígono/parcela,
    la marca en el mapa principal y activa la herramienta de clic, para que
    pulsar sobre ella abra su ficha en el navegador."""

    def __init__(self, iface, activar_herramienta_clic, parent=None):
        super().__init__("Buscar parcela", parent)
        self.iface = iface
        self.activar_herramienta_clic = activar_herramienta_clic
        self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.hide()

        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Ej. 46138A00100010")
        tab_referencia = QWidget()
        form_referencia = QFormLayout(tab_referencia)
        form_referencia.addRow("Referencia catastral:", self.ref_edit)

        self.provincia_edit = QLineEdit()
        self.provincia_edit.setPlaceholderText("Ej. VALENCIA")
        self.municipio_edit = QLineEdit()
        self.municipio_edit.setPlaceholderText("Ej. GODELLETA")
        self.poligono_edit = QLineEdit()
        self.poligono_edit.setPlaceholderText("Ej. 1")
        self.parcela_edit = QLineEdit()
        self.parcela_edit.setPlaceholderText("Ej. 10")
        tab_poligono = QWidget()
        form_poligono = QFormLayout(tab_poligono)
        form_poligono.addRow("Provincia:", self.provincia_edit)
        form_poligono.addRow("Municipio:", self.municipio_edit)
        form_poligono.addRow("Polígono:", self.poligono_edit)
        form_poligono.addRow("Parcela:", self.parcela_edit)

        self.tabs = QTabWidget()
        self.tabs.addTab(tab_referencia, "Por referencia")
        self.tabs.addTab(tab_poligono, "Por polígono y parcela")

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        self.copia_layout = QVBoxLayout()

        buscar_btn = QPushButton("Buscar")
        buscar_btn.setDefault(True)
        buscar_btn.clicked.connect(self.buscar)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.addWidget(self.tabs)
        layout.addWidget(buscar_btn)
        layout.addLayout(self.copia_layout)
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.setWidget(contenido)

    def buscar(self):
        self.status_label.setText("Consultando…")
        try:
            if self.tabs.currentIndex() == 0:
                refcat = self._resolver_por_referencia()
                aviso = ""
            else:
                refcat, aviso = self._resolver_por_poligono_parcela()
            lon, lat = punto_de_referencia(refcat)
        except CatastroLookupError as exc:
            self.status_label.setText(str(exc))
            return
        except Exception as exc:
            self.status_label.setText(f"No se pudo completar la consulta: {exc}")
            return

        try:
            datos_refcat = naturaleza_y_referencia_completa(refcat)
        except Exception:
            datos_refcat = {}
        naturaleza = datos_refcat.get("naturaleza")
        self._mostrar_referencia(refcat, datos_refcat.get("refcat_completa"))

        try:
            self._marcar_en_mapa(refcat, lon, lat)
        except Exception as exc:
            self.status_label.setText(f"No se pudo marcar la parcela en el mapa: {exc}")
            return
        self.activar_herramienta_clic()

        partes = [
            aviso,
            "Parcela marcada en el mapa: pulsa sobre ella para abrir su ficha.",
            f"Naturaleza: {naturaleza}" if naturaleza else "",
            resumen_hidrico(lon, lat),
            resumen_red_natura(lon, lat),
        ]
        self.status_label.setText(" ".join(p for p in partes if p))

    def _mostrar_referencia(self, refcat: str, refcat_completa=None):
        while self.copia_layout.count():
            widget = self.copia_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.copia_layout.addWidget(
            fila_copiable("Referencia catastral completa:", refcat_completa or refcat)
        )
        poligono_parcela = formato_poligono_parcela(refcat)
        if poligono_parcela:
            self.copia_layout.addWidget(fila_copiable("Polígono/parcela:", poligono_parcela))

    def _resolver_por_referencia(self) -> str:
        entrada = self.ref_edit.text().strip()
        if not entrada:
            raise CatastroLookupError("Escribe una referencia catastral.")
        return normalizar_referencia(entrada)

    def _resolver_por_poligono_parcela(self):
        provincia = self.provincia_edit.text().strip()
        municipio = self.municipio_edit.text().strip()
        poligono = self.poligono_edit.text().strip()
        parcela = self.parcela_edit.text().strip()
        if not all([provincia, municipio, poligono, parcela]):
            raise CatastroLookupError("Rellena provincia, municipio, polígono y parcela.")

        refcats = refcats_en_poligono_parcela(provincia, municipio, poligono, parcela)
        aviso = f"Hay {len(refcats)} fincas asociadas; se ha marcado la primera." if len(refcats) > 1 else ""
        return refcats[0], aviso

    def _marcar_en_mapa(self, refcat, lon, lat):
        canvas = self.iface.mapCanvas()
        project_crs = canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(WGS84, project_crs, QgsProject.instance())

        try:
            anillo = geometria_parcela(refcat)
            puntos = [transform.transform(QgsPointXY(lon_p, lat_p)) for lon_p, lat_p in anillo]
            geometria = QgsGeometry.fromPolygonXY([puntos])
        except Exception:
            # Cualquier fallo al obtener/transformar el contorno (respuesta
            # rara del Catastro, punto fuera del área de validez de la
            # transformación de coordenadas...) cae a marcar solo el centro,
            # que ya viene de una consulta distinta y más simple.
            geometria = QgsGeometry.fromPointXY(transform.transform(QgsPointXY(lon, lat)))

        self.rubber_band.reset(geometria.type())

        color_borde = settings.color_borde()
        color_borde.setAlpha(255)
        self.rubber_band.setStrokeColor(color_borde)
        self.rubber_band.setWidth(settings.ancho_borde())

        if settings.relleno_activado():
            color_relleno = settings.color_relleno()
            color_relleno.setAlpha(round(settings.opacidad_relleno() * 255 / 100))
        else:
            color_relleno = QColor(0, 0, 0, 0)
        self.rubber_band.setFillColor(color_relleno)

        if geometria.type() == QgsWkbTypes.PointGeometry:
            self.rubber_band.setIcon(QgsRubberBand.ICON_CIRCLE)
            self.rubber_band.setIconSize(14)
        self.rubber_band.setToGeometry(geometria, None)

        if geometria.type() == QgsWkbTypes.PolygonGeometry:
            extent = geometria.boundingBox()
            extent.scale(2.5)
            canvas.setExtent(extent)
        else:
            canvas.setCenter(transform.transform(QgsPointXY(lon, lat)))
            canvas.zoomScale(2000)
        canvas.refresh()

    def limpiar_marca(self):
        if self.rubber_band is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubber_band)
            self.rubber_band = None
