def classFactory(iface):
    from .plugin import CatastrofePlugin

    return CatastrofePlugin(iface)
