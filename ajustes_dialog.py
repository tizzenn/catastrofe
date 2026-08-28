from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from . import settings


class BotonColor(QPushButton):
    """Botón que muestra el color actual como fondo y abre un selector al pulsarlo."""

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.setFixedWidth(60)
        self.set_color(color)
        self.clicked.connect(self._elegir_color)

    def set_color(self, color: QColor):
        self._color = QColor(color)
        self.setStyleSheet(f"background-color: {self._color.name()};")

    def color(self) -> QColor:
        return QColor(self._color)

    def _elegir_color(self):
        elegido = QColorDialog.getColor(self._color, self, "Elige un color")
        if elegido.isValid():
            self.set_color(elegido)
            self.colorCambiado(elegido)

    def colorCambiado(self, color: QColor):
        """Se sobrescribe desde fuera (o se conecta) para reaccionar al cambio."""


class AjustesDialog(QDialog):
    """Preferencias del plugin: qué datos hídricos mostrar y cómo se resalta
    la parcela marcada en el mapa. Cada control aplica y guarda el cambio al
    momento, sin botón de guardar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustes — Catastrofe")

        grupo_hidrico = QGroupBox("Datos ambientales")
        self.check_acuifero = QCheckBox("Mostrar acuífero (agua subterránea)")
        self.check_acuifero.setChecked(settings.mostrar_acuifero())
        self.check_acuifero.toggled.connect(settings.set_mostrar_acuifero)
        self.check_zona_inundable = QCheckBox("Mostrar zona inundable / dominio público hidráulico")
        self.check_zona_inundable.setChecked(settings.mostrar_zona_inundable())
        self.check_zona_inundable.toggled.connect(settings.set_mostrar_zona_inundable)
        self.check_red_natura = QCheckBox("Mostrar si está en la Red Natura 2000")
        self.check_red_natura.setChecked(settings.mostrar_red_natura())
        self.check_red_natura.toggled.connect(settings.set_mostrar_red_natura)
        layout_hidrico = QVBoxLayout(grupo_hidrico)
        layout_hidrico.addWidget(self.check_acuifero)
        layout_hidrico.addWidget(self.check_zona_inundable)
        layout_hidrico.addWidget(self.check_red_natura)

        grupo_resaltado = QGroupBox("Resaltado de la parcela en el mapa")
        self.boton_color_borde = BotonColor(settings.color_borde())
        self.boton_color_borde.colorCambiado = self._cambiar_color_borde
        self.spin_ancho_borde = QSpinBox()
        self.spin_ancho_borde.setRange(1, 10)
        self.spin_ancho_borde.setSuffix(" px")
        self.spin_ancho_borde.setValue(settings.ancho_borde())
        self.spin_ancho_borde.valueChanged.connect(settings.set_ancho_borde)

        self.check_relleno = QCheckBox("Activar sombreado interior")
        self.check_relleno.setChecked(settings.relleno_activado())
        self.check_relleno.toggled.connect(self._cambiar_relleno_activado)

        self.boton_color_relleno = BotonColor(settings.color_relleno())
        self.boton_color_relleno.colorCambiado = self._cambiar_color_relleno
        self.spin_opacidad_relleno = QSpinBox()
        self.spin_opacidad_relleno.setRange(0, 100)
        self.spin_opacidad_relleno.setSuffix(" %")
        self.spin_opacidad_relleno.setValue(settings.opacidad_relleno())
        self.spin_opacidad_relleno.valueChanged.connect(settings.set_opacidad_relleno)

        fila_relleno_color = QHBoxLayout()
        fila_relleno_color.addWidget(self.boton_color_relleno)
        fila_relleno_color.addWidget(QLabel("Opacidad:"))
        fila_relleno_color.addWidget(self.spin_opacidad_relleno)
        fila_relleno_color.addStretch()

        form_resaltado = QFormLayout()
        form_resaltado.addRow("Color del borde:", self.boton_color_borde)
        form_resaltado.addRow("Ancho del borde:", self.spin_ancho_borde)

        layout_resaltado = QVBoxLayout(grupo_resaltado)
        layout_resaltado.addLayout(form_resaltado)
        layout_resaltado.addWidget(self.check_relleno)
        layout_resaltado.addLayout(fila_relleno_color)

        self._actualizar_estado_relleno(self.check_relleno.isChecked())

        cerrar_btn = QPushButton("Cerrar")
        cerrar_btn.clicked.connect(self.accept)
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(cerrar_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(grupo_hidrico)
        layout.addWidget(grupo_resaltado)
        layout.addLayout(fila_botones)

    def _cambiar_color_borde(self, color: QColor):
        settings.set_color_borde(color)

    def _cambiar_color_relleno(self, color: QColor):
        settings.set_color_relleno(color)

    def _cambiar_relleno_activado(self, activado: bool):
        settings.set_relleno_activado(activado)
        self._actualizar_estado_relleno(activado)

    def _actualizar_estado_relleno(self, activado: bool):
        self.boton_color_relleno.setEnabled(activado)
        self.spin_opacidad_relleno.setEnabled(activado)
