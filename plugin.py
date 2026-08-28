import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

from .catastro_maptool import CatastroClickTool
from .dialog import BuscarParcelaDialog
from .settings import (
    mostrar_acuifero,
    mostrar_zona_inundable,
    set_mostrar_acuifero,
    set_mostrar_zona_inundable,
)


class CatastrofePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.menu = None
        self.action = None
        self.search_action = None
        self.map_tool = None
        self.previous_tool = None
        self.search_dialog = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "Abrir parcela en Sede Catastro", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.toggled.connect(self.toggle_tool)
        self.iface.addToolBarIcon(self.action)

        self.search_action = QAction("Buscar parcela (referencia o polígono/parcela)…", self.iface.mainWindow())
        self.search_action.triggered.connect(self.open_search_dialog)

        ajustes_menu = QMenu("Ajustes", self.iface.mainWindow())
        self.accion_acuifero = QAction("Mostrar acuífero (agua subterránea)", ajustes_menu)
        self.accion_acuifero.setCheckable(True)
        self.accion_acuifero.setChecked(mostrar_acuifero())
        self.accion_acuifero.toggled.connect(set_mostrar_acuifero)
        self.accion_zona_inundable = QAction("Mostrar zona inundable / dominio público hidráulico", ajustes_menu)
        self.accion_zona_inundable.setCheckable(True)
        self.accion_zona_inundable.setChecked(mostrar_zona_inundable())
        self.accion_zona_inundable.toggled.connect(set_mostrar_zona_inundable)
        ajustes_menu.addAction(self.accion_acuifero)
        ajustes_menu.addAction(self.accion_zona_inundable)

        self.menu = QMenu("Catastrofe", self.iface.mainWindow())
        self.menu.addAction(self.action)
        self.menu.addAction(self.search_action)
        self.menu.addMenu(ajustes_menu)
        self.iface.pluginMenu().addMenu(self.menu)

        self.map_tool = CatastroClickTool(self.iface.mapCanvas(), self.iface)
        self.map_tool.setAction(self.action)
        self.iface.mapCanvas().mapToolSet.connect(self.on_map_tool_changed)

    def unload(self):
        self.iface.mapCanvas().mapToolSet.disconnect(self.on_map_tool_changed)
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.iface.removeToolBarIcon(self.action)
        self.menu = None
        self.map_tool = None
        self.action = None
        self.search_action = None
        if self.search_dialog is not None:
            self.search_dialog.close()
            self.search_dialog = None

    def open_search_dialog(self):
        if self.search_dialog is None:
            self.search_dialog = BuscarParcelaDialog(self.iface.mainWindow())
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def toggle_tool(self, checked):
        if checked:
            self.previous_tool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.map_tool)
        elif self.iface.mapCanvas().mapTool() is self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)

    def on_map_tool_changed(self, new_tool, old_tool):
        if self.action is not None and new_tool is not self.map_tool:
            self.action.setChecked(False)
