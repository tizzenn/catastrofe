from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
)
from qgis.gui import QgsRubberBand
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QColor, QDesktopServices
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .catastro_service import (
    CatastroLookupError,
    formato_poligono_parcela,
    geometria_parcela,
    naturaleza_por_formato,
    naturaleza_y_referencia_completa,
    normalizar_referencia,
    punto_de_referencia,
    refcat_en_coordenadas,
    refcats_en_poligono_parcela,
    url_ficha_grafica,
)
from .portapapeles import fila_copiable
from . import settings

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
HUSOS_UTM = (28, 29, 30, 31)  # ETRS89: Canarias, Galicia/oeste, centro/este peninsular, Cataluña/Baleares

try:  # QGIS >= 3.30 (y 4.x)
    TIPO_POLIGONO = Qgis.GeometryType.Polygon
    TIPO_PUNTO = Qgis.GeometryType.Point
except AttributeError:  # QGIS 3.28
    from qgis.core import QgsWkbTypes

    TIPO_POLIGONO = QgsWkbTypes.PolygonGeometry
    TIPO_PUNTO = QgsWkbTypes.PointGeometry


# Indicio orientativo a partir de la naturaleza catastral; no es la clasificación del planeamiento.
INDICIO_SUELO = {
    "Urbana": "Suelo (indicio según Catastro): urbano",
    "Rústica": "Suelo (indicio según Catastro): no urbano",
}


def _icono_circulo():
    clase = QgsRubberBand
    return getattr(getattr(clase, "IconType", clase), "ICON_CIRCLE")


class CatastrofePanel(QDockWidget):
    """Panel de búsqueda catastral y resaltado de parcelas en el mapa."""

    def __init__(self, iface, activar_herramienta_clic, abrir_ajustes, parent=None):
        super().__init__("Buscar parcela", parent)
        self.iface = iface
        self.activar_herramienta_clic = activar_herramienta_clic
        # Cada registro: refcat, refcat_completa, poligono_parcela, naturaleza,
        # url, banda (QgsRubberBand), es_poligono y extension (rectángulo).
        self.resultados = []

        # Pestaña por referencia catastral.
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Ej. 32054A00100010")
        tab_referencia = QWidget()
        form_referencia = QFormLayout(tab_referencia)
        form_referencia.addRow("Referencia catastral:", self.ref_edit)

        # Pestaña por polígono y parcela rústicos.
        self.provincia_edit = QLineEdit()
        self.provincia_edit.setPlaceholderText("Ej. OURENSE")
        self.municipio_edit = QLineEdit()
        self.municipio_edit.setPlaceholderText("Ej. AVIÓN")
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

        # Pestaña por coordenadas UTM ETRS89.
        self.utm_x_edit = QLineEdit()
        self.utm_x_edit.setPlaceholderText("Ej. 580000")
        self.utm_y_edit = QLineEdit()
        self.utm_y_edit.setPlaceholderText("Ej. 4680000")
        tab_utm = QWidget()
        form_utm = QFormLayout(tab_utm)
        self.huso_combo = QComboBox()
        for huso in HUSOS_UTM:
            self.huso_combo.addItem(f"ETRS89 / UTM huso {huso}N (EPSG:258{huso})", huso)
        indice_huso = self.huso_combo.findData(settings.huso_utm())
        self.huso_combo.setCurrentIndex(max(indice_huso, 0))
        self.huso_combo.setToolTip("El huso elegido se recuerda para las próximas búsquedas.")
        self.huso_combo.currentIndexChanged.connect(
            lambda _: settings.set_huso_utm(self.huso_combo.currentData())
        )
        form_utm.addRow("Sistema:", self.huso_combo)
        form_utm.addRow("X (Este):", self.utm_x_edit)
        form_utm.addRow("Y (Norte):", self.utm_y_edit)

        self.tabs = QTabWidget()
        self.tabs.addTab(tab_referencia, "Por Ref")
        self.tabs.addTab(tab_poligono, "Por Pol-Parc")
        self.tabs.addTab(tab_utm, "Por UTM")
        self.tabs.setTabToolTip(0, "Buscar por referencia catastral")
        self.tabs.setTabToolTip(1, "Buscar por polígono y parcela (rústica)")
        self.tabs.setTabToolTip(2, "Buscar por coordenadas UTM ETRS89")
        self.tabs.tabBar().setExpanding(True)

        # Intro en cualquier campo lanza la búsqueda.
        for campo in (self.ref_edit, self.provincia_edit, self.municipio_edit, self.poligono_edit,
                      self.parcela_edit, self.utm_x_edit, self.utm_y_edit):
            campo.returnPressed.connect(self.buscar)

        self.buscar_btn = QPushButton("Buscar")
        self.buscar_btn.clicked.connect(self.buscar)

        self.acumulativo_check = QCheckBox("Modo acumulativo")
        self.acumulativo_check.setToolTip(
            "Mantiene en el mapa las parcelas anteriores y añade cada nueva búsqueda."
        )
        self.limpiar_btn = QPushButton("Limpiar")
        self.limpiar_btn.clicked.connect(self.limpiar)
        self.ajustes_btn = QToolButton()
        self.ajustes_btn.setText("⚙")
        self.ajustes_btn.setToolTip("Ajustes: color, grosor y relleno del resaltado")
        self.ajustes_btn.clicked.connect(lambda: abrir_ajustes())
        controles = QHBoxLayout()
        controles.addWidget(self.acumulativo_check)
        controles.addStretch()
        controles.addWidget(self.limpiar_btn)
        controles.addWidget(self.ajustes_btn)

        self.resultados_layout = QVBoxLayout()
        self.resultados_layout.setContentsMargins(0, 6, 0, 0)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.addWidget(self.tabs)
        layout.addWidget(self.buscar_btn)
        layout.addLayout(controles)
        layout.addWidget(self.status_label)
        layout.addLayout(self.resultados_layout)
        layout.addStretch()

        # Con muchas parcelas acumuladas la lista crece: el panel se desplaza.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(contenido)
        self.setWidget(scroll)

    # ------------------------------------------------------------------
    # Entradas públicas
    # ------------------------------------------------------------------

    def buscar(self):
        """Botón Buscar: usa la pestaña activa."""
        self._ejecutar(self._buscar_desde_pestana)

    def mostrar_refcat(self, refcat):
        """Usada por la herramienta de clic en el mapa: mismas reglas que Buscar."""
        self.show()
        self.raise_()
        self._ejecutar(lambda: self._procesar_refcats([refcat]))

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------

    def _ejecutar(self, funcion):
        if not self.buscar_btn.isEnabled():
            return  # ya hay una consulta en curso
        self.buscar_btn.setEnabled(False)
        self.status_label.setText("Consultando Catastro…")
        QApplication.processEvents()
        try:
            funcion()
        except Exception as exc:
            self.status_label.setText(f"No se pudo completar la consulta: {exc}")
        finally:
            self.buscar_btn.setEnabled(True)

    def _buscar_desde_pestana(self):
        indice = self.tabs.currentIndex()
        aviso = ""
        try:
            if indice == 0:
                refcats = [self._resolver_por_referencia()]
            elif indice == 1:
                refcat, aviso = self._resolver_por_poligono_parcela()
                refcats = [refcat]
            else:
                refcats = [self._resolver_por_utm()]
        except (CatastroLookupError, ValueError) as exc:
            self.status_label.setText(str(exc))
            return
        self._procesar_refcats(refcats, aviso=aviso)

    def _resolver_por_referencia(self):
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

    def _resolver_por_utm(self):
        try:
            x = float(self.utm_x_edit.text().strip().replace(",", "."))
            y = float(self.utm_y_edit.text().strip().replace(",", "."))
        except ValueError:
            raise CatastroLookupError("Introduce coordenadas UTM X e Y válidas.")
        utm = QgsCoordinateReferenceSystem(f"EPSG:258{self.huso_combo.currentData()}")
        transform = QgsCoordinateTransform(utm, WGS84, QgsProject.instance())
        punto_wgs84 = transform.transform(QgsPointXY(x, y))
        return refcat_en_coordenadas(punto_wgs84.x(), punto_wgs84.y())

    def _procesar_refcats(self, refcats, aviso=""):
        """Añade parcelas respetando el modo acumulativo.

        Sin modo acumulativo, las parcelas anteriores se retiran solo cuando
        se ha podido añadir al menos una nueva, para no perder el resultado
        previo si la consulta falla.
        """
        acumulativo = self.acumulativo_check.isChecked()
        anteriores = list(self.resultados)
        existentes = {r["refcat"] for r in anteriores} if acumulativo else set()
        nuevos, repetidas, fallos = [], 0, []

        for refcat in refcats:
            if refcat in existentes or any(r["refcat"] == refcat for r in nuevos):
                repetidas += 1
                continue
            try:
                nuevos.append(self._crear_registro(refcat))
            except Exception as exc:
                fallos.append(f"{refcat}: {exc}")

        if nuevos:
            if not acumulativo:
                for registro in anteriores:
                    self._quitar_banda(registro)
                self.resultados = []
            self.resultados.extend(nuevos)
            self._actualizar_resultados()
            self._hacer_zoom(nuevos)
            self.activar_herramienta_clic()

        partes = []
        if aviso:
            partes.append(aviso)
        if nuevos:
            if len(nuevos) == 1:
                partes.append("Parcela añadida al mapa." if acumulativo else "Parcela marcada en el mapa.")
            else:
                partes.append(f"{len(nuevos)} parcelas añadidas al mapa.")
            sin_enlace = sum(1 for r in nuevos if not r["url"])
            if sin_enlace:
                partes.append(f"No se pudo obtener el enlace a la ficha de {sin_enlace} parcela(s).")
        if repetidas:
            partes.append(
                "Esa parcela ya está en la lista acumulada." if repetidas == 1 and not nuevos and not fallos
                else (f"{repetidas} ya estaba en la lista." if repetidas == 1 else f"{repetidas} ya estaban en la lista.")
            )
        for fallo in fallos[:3]:
            partes.append(fallo)
        if len(fallos) > 3:
            partes.append(f"…y {len(fallos) - 3} consulta(s) más fallidas.")
        self.status_label.setText(" ".join(partes))

    # ------------------------------------------------------------------
    # Registros y mapa
    # ------------------------------------------------------------------

    def _crear_registro(self, refcat):
        lon, lat = punto_de_referencia(refcat)
        try:
            datos_refcat = naturaleza_y_referencia_completa(refcat)
        except Exception:
            datos_refcat = {}
        try:
            url = url_ficha_grafica(refcat)
        except Exception:
            url = None

        banda, extension, es_poligono = self._marcar_en_mapa(refcat, lon, lat)
        return {
            "refcat": refcat,
            "refcat_completa": datos_refcat.get("refcat_completa") or refcat,
            "poligono_parcela": formato_poligono_parcela(refcat),
            "naturaleza": datos_refcat.get("naturaleza") or naturaleza_por_formato(refcat),
            "url": url,
            "banda": banda,
            "es_poligono": es_poligono,
            "extension": extension,
        }

    def _crear_banda(self, geometria, es_poligono):
        canvas = self.iface.mapCanvas()
        banda = QgsRubberBand(canvas, TIPO_POLIGONO if es_poligono else TIPO_PUNTO)
        self._estilizar_banda(banda, es_poligono)
        try:
            banda.setToGeometry(geometria, QgsCoordinateReferenceSystem())
        except TypeError:  # firma antigua (QgsVectorLayer)
            banda.setToGeometry(geometria, None)
        return banda

    @staticmethod
    def _estilizar_banda(banda, es_poligono):
        color_borde = settings.color_borde()
        color_borde.setAlpha(255)
        banda.setStrokeColor(color_borde)
        banda.setWidth(settings.ancho_borde())
        if settings.relleno_activado():
            color_relleno = settings.color_relleno()
            color_relleno.setAlpha(round(settings.opacidad_relleno() * 255 / 100))
        else:
            color_relleno = QColor(0, 0, 0, 0)
        banda.setFillColor(color_relleno)
        if not es_poligono:
            banda.setIcon(_icono_circulo())
            banda.setIconSize(14)

    def restilizar(self):
        """Aplica los ajustes actuales a las parcelas que ya están en el mapa."""
        for registro in self.resultados:
            if registro.get("banda") is not None:
                self._estilizar_banda(registro["banda"], registro["es_poligono"])
        self.iface.mapCanvas().refresh()

    def _marcar_en_mapa(self, refcat, lon, lat):
        """Dibuja la parcela. Devuelve (banda, extensión en CRS del proyecto, es_poligono)."""
        canvas = self.iface.mapCanvas()
        project_crs = canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(WGS84, project_crs, QgsProject.instance())
        es_poligono = True
        try:
            anillo = geometria_parcela(refcat)
            puntos = [transform.transform(QgsPointXY(lon_p, lat_p)) for lon_p, lat_p in anillo]
            geometria = QgsGeometry.fromPolygonXY([puntos])
            extension = geometria.boundingBox()
        except Exception:
            es_poligono = False
            centro = transform.transform(QgsPointXY(lon, lat))
            geometria = QgsGeometry.fromPointXY(centro)
            extension = QgsRectangle(centro.x(), centro.y(), centro.x(), centro.y())
        return self._crear_banda(geometria, es_poligono), extension, es_poligono

    def _hacer_zoom(self, registros):
        """Encuadra las parcelas recién añadidas."""
        canvas = self.iface.mapCanvas()
        total = QgsRectangle(registros[0]["extension"])
        for registro in registros[1:]:
            total.combineExtentWith(registro["extension"])
        if total.isEmpty():  # un solo punto de respaldo, sin perímetro
            canvas.setCenter(total.center())
            canvas.zoomScale(2000)
        else:
            total.scale(2.5 if len(registros) == 1 else 1.2)
            canvas.setExtent(total)
        canvas.refresh()

    def _quitar_banda(self, registro):
        banda = registro.get("banda")
        if banda is None:
            return
        try:
            # QgsRubberBand es un elemento gráfico (no un QObject): basta con
            # sacarlo de la escena y soltar la referencia.
            self.iface.mapCanvas().scene().removeItem(banda)
        except RuntimeError:
            pass
        registro["banda"] = None

    # ------------------------------------------------------------------
    # Lista de resultados
    # ------------------------------------------------------------------

    def _actualizar_resultados(self):
        while self.resultados_layout.count():
            item = self.resultados_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.resultados:
            return

        # La más reciente va arriba.
        for posicion, registro in enumerate(reversed(self.resultados)):
            if posicion > 0:
                separador = QFrame()
                separador.setFrameShape(QFrame.Shape.HLine)
                separador.setFrameShadow(QFrame.Shadow.Sunken)
                self.resultados_layout.addWidget(separador)

            tarjeta = QWidget()
            tarjeta_layout = QVBoxLayout(tarjeta)
            tarjeta_layout.setContentsMargins(0, 2, 0, 2)
            tarjeta_layout.setSpacing(2)

            # Primera fila: indicio de suelo a la izquierda y ✕ a la derecha.
            fila_suelo = QHBoxLayout()
            indicio = INDICIO_SUELO.get(registro.get("naturaleza"))
            if indicio:
                etiqueta_suelo = QLabel(indicio)
                etiqueta_suelo.setToolTip(
                    "Es la naturaleza catastral (Urbana/Rústica), no la clasificación urbanística "
                    "del planeamiento. Puede no coincidir, p. ej. en núcleos rurales. Confirma en el planeamiento municipal."
                )
                fila_suelo.addWidget(etiqueta_suelo)
            fila_suelo.addStretch()
            quitar = QToolButton()
            quitar.setText("✕")
            quitar.setToolTip("Quitar esta parcela de la lista y del mapa")
            quitar.clicked.connect(lambda checked=False, r=registro: self.quitar_parcela(r))
            fila_suelo.addWidget(quitar)
            tarjeta_layout.addLayout(fila_suelo)

            tarjeta_layout.addWidget(fila_copiable("Referencia catastral:", registro["refcat_completa"]))
            if registro["poligono_parcela"]:
                tarjeta_layout.addWidget(fila_copiable("Polígono-parcela:", registro["poligono_parcela"]))
            if registro["url"]:
                abrir = QPushButton("Abrir ficha en Sede del Catastro")
                abrir.clicked.connect(
                    lambda checked=False, destino=registro["url"]: QDesktopServices.openUrl(QUrl(destino))
                )
                tarjeta_layout.addWidget(abrir)
            else:
                tarjeta_layout.addWidget(QLabel("Enlace a ficha no disponible"))
            self.resultados_layout.addWidget(tarjeta)

        if len(self.resultados) > 1:
            copiar_todas = QPushButton(f"Copiar las {len(self.resultados)} referencias")
            copiar_todas.setToolTip("Copia todas las referencias catastrales, una por línea")
            copiar_todas.clicked.connect(self._copiar_todas)
            self.resultados_layout.addWidget(copiar_todas)

    def _copiar_todas(self):
        texto = "\n".join(r["refcat_completa"] for r in self.resultados)
        QApplication.clipboard().setText(texto)
        self.status_label.setText(f"{len(self.resultados)} referencias copiadas al portapapeles.")

    def quitar_parcela(self, registro):
        """Quita una parcela concreta de la lista y de su dibujo en el mapa."""
        if registro not in self.resultados:
            return
        self.resultados.remove(registro)
        self._quitar_banda(registro)
        self._actualizar_resultados()
        self.iface.mapCanvas().refresh()
        self.status_label.setText("Parcela quitada.")

    def _vaciar_resultados_y_marcas(self):
        for registro in self.resultados:
            self._quitar_banda(registro)
        self.resultados.clear()
        self._actualizar_resultados()
        self.iface.mapCanvas().refresh()

    def limpiar(self):
        """Limpia resultados y marcas sin cambiar el estado acumulativo."""
        modo_acumulativo = self.acumulativo_check.isChecked()
        self._vaciar_resultados_y_marcas()
        self.status_label.setText(
            "Resultados y marcas eliminados. El modo acumulativo sigue activado."
            if modo_acumulativo else "Resultados y marcas eliminados."
        )

    def limpiar_marca(self):
        """Limpieza usada al descargar el complemento."""
        self._vaciar_resultados_y_marcas()
