import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QToolButton, QWidget

_ICON_PATH = os.path.join(os.path.dirname(__file__), "icon_copiar.svg")


def fila_copiable(etiqueta: str, valor: str) -> QWidget:
    """Fila "etiqueta: valor" con el valor en un campo de solo lectura y un
    botón al lado para copiarlo al portapapeles. Pensada para insertarse en
    la barra de mensajes o en el panel de búsqueda."""
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)

    campo = QLineEdit(valor)
    campo.setReadOnly(True)
    campo.setCursorPosition(0)
    ancho_texto = campo.fontMetrics().horizontalAdvance(valor)
    campo.setFixedWidth(ancho_texto + 24)

    boton = QToolButton()
    icono = QIcon(_ICON_PATH) if os.path.exists(_ICON_PATH) else QIcon()
    boton.setIcon(icono)
    boton.setToolTip("Copiar al portapapeles")
    boton.clicked.connect(lambda: QApplication.clipboard().setText(valor))

    layout.addWidget(QLabel(etiqueta))
    layout.addWidget(campo)
    layout.addWidget(boton)
    return contenedor
