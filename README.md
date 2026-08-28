# Catastrofe

Plugin de QGIS: activa una herramienta de mapa y, al pulsar sobre una
parcela, abre en el navegador su ficha en la Sede Electrónica del Catastro.

Origen: [issue #9](https://github.com/fpsampayo/zoomrc/issues/9) en el
plugin *zoomrc*. Su autor (fpsampayo) respondió que su plugin no interactúa
con el mapa y que no era su objetivo, pero confirmó que la URL de la ficha
es fija a partir de la referencia catastral. Este plugin es nuevo, no un
fork de zoomrc.

## Cómo funciona

No depende de tener cargada ninguna capa de parcelas: usa directamente el
[servicio web libre del Catastro](https://www.catastro.hacienda.gob.es/ws/Webservices_Libres.pdf).

**Clic en el mapa:**
1. Transforma el punto pulsado a WGS84 (EPSG:4326).
2. `Consulta_RCCOOR`: coordenadas → referencia catastral (14 posiciones).
3. `Consulta_DNPRC`: referencia catastral → URL de la ficha gráfica
   (el propio Catastro la devuelve hecha en el campo `<igraf>`, no hay que
   construirla a mano).
4. Abre esa URL en una pestaña nueva del navegador por defecto.

Si el punto pulsado cae en la calle o fuera de una parcela, el Catastro
devuelve un error ("para esas coordenadas no hay referencia disponible")
y el plugin lo muestra en la barra de mensajes de QGIS en vez de abrir nada.

**Buscar parcela (menú Catastrofe → Buscar parcela…):** diálogo con dos
pestañas, sin necesidad de tener el mapa centrado en la zona:
- Por referencia catastral directa (14 caracteres).
- Por polígono y parcela rústicos (`Consulta_DNPPP`), dando la provincia y
  el municipio por su nombre (no código INE) más los números de polígono y
  parcela. Si una parcela tiene varias fincas asociadas (p.ej. una rústica y
  otra con edificación) se abre la primera y se avisa en el propio diálogo.

**Dato hídrico (opcional):** además de abrir la ficha, consulta el WFS
público del MITECO (`gis.miteco.gob.es/geoserver/agua`) para ese mismo punto
y muestra, si aplica:
- **Acuífero**: masa de agua subterránea en la que cae la parcela.
- **Zona inundable / dominio público hidráulico**: si la parcela está en
  zona de flujo preferente o en zona inundable (T10/T100/T500).

Es el único dato hídrico que estos servicios ofrecen de forma abierta y sin
login para toda España (incluidas cuencas intracomunitarias); no hay dato
público de concesiones de agua ni de comunidades de regantes. Cada aviso se
puede activar o desactivar por separado en **Catastrofe → Ajustes**
(persistente entre sesiones de QGIS; con ambos desactivados no se hace
ninguna consulta extra al MITECO).

**Limitación conocida:** el servicio del Catastro no cubre País Vasco ni
Navarra (tienen catastro foral propio, con sus propias sedes).

## Instalación (modo desarrollo)

```bash
ln -s ~/Projects/catastrofe ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/catastrofe
```

Luego, en QGIS: *Complementos → Administrar e instalar complementos →
Instalados* y activar "Catastrofe". El icono aparece en la barra de
herramientas.

## Pruebas sin QGIS

La lógica de consulta al Catastro (`catastro_service.py`) no depende de
PyQGIS y se puede probar aparte:

```bash
python3 test_catastro_service.py
```

## Pendiente

- Probar dentro de QGIS real (ya instalado en esta máquina, falta activar
  el complemento y probar clic + diálogo de búsqueda con QGIS abierto).
- Decidir si se publica en el repositorio de plugins de QGIS: hace falta
  LICENSE con el texto completo (por ahora solo GPL-3.0-or-later en
  `metadata.txt`/cabeceras, sin el texto íntegro) y una cuenta en
  `plugins.qgis.org`.
