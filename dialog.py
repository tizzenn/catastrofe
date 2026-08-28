import webbrowser

from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .catastro_service import (
    CatastroLookupError,
    punto_de_referencia,
    refcats_en_poligono_parcela,
    url_ficha_grafica,
)
from .hidro_info import resumen_hidrico


class BuscarParcelaDialog(QDialog):
    """Busca una parcela por referencia catastral o por polígono/parcela
    y abre su ficha en el navegador."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar parcela — Catastrofe")

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

        buscar_btn = QPushButton("Buscar")
        buscar_btn.setDefault(True)
        buscar_btn.clicked.connect(self.buscar)
        cerrar_btn = QPushButton("Cerrar")
        cerrar_btn.clicked.connect(self.close)

        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(buscar_btn)
        botones.addWidget(cerrar_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(self.status_label)
        layout.addLayout(botones)

    def buscar(self):
        self.status_label.setText("Consultando…")
        aviso_varias_fincas = ""
        try:
            if self.tabs.currentIndex() == 0:
                refcat = self._buscar_por_referencia()
            else:
                refcat, aviso_varias_fincas = self._buscar_por_poligono_parcela()
            url = url_ficha_grafica(refcat)
        except CatastroLookupError as exc:
            self.status_label.setText(str(exc))
            return
        except Exception as exc:
            self.status_label.setText(f"No se pudo completar la consulta: {exc}")
            return

        webbrowser.open(url)

        resumen = ""
        try:
            lon, lat = punto_de_referencia(refcat)
            resumen = resumen_hidrico(lon, lat)
        except CatastroLookupError:
            pass

        partes = [p for p in ["Abierta en el navegador.", aviso_varias_fincas, resumen] if p]
        self.status_label.setText(" ".join(partes))

    def _buscar_por_referencia(self) -> str:
        refcat = self.ref_edit.text().strip().upper()
        if not refcat:
            raise CatastroLookupError("Escribe una referencia catastral.")
        return refcat

    def _buscar_por_poligono_parcela(self):
        provincia = self.provincia_edit.text().strip()
        municipio = self.municipio_edit.text().strip()
        poligono = self.poligono_edit.text().strip()
        parcela = self.parcela_edit.text().strip()
        if not all([provincia, municipio, poligono, parcela]):
            raise CatastroLookupError("Rellena provincia, municipio, polígono y parcela.")

        refcats = refcats_en_poligono_parcela(provincia, municipio, poligono, parcela)
        aviso = f"Hay {len(refcats)} fincas asociadas; se ha abierto la primera." if len(refcats) > 1 else ""
        return refcats[0], aviso
