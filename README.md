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
3. `Consulta_DNPRC`: referencia catastral → URL de la ficha gráfica (en el
   campo `<igraf>`) y naturaleza (rústica/urbana, campo `<cn>`). Si la
   referencia tiene varias unidades catastrales asociadas (un edificio con
   varios locales o pisos, división horizontal), Catastro no da esos datos
   para la referencia de 14 caracteres a secas: el plugin repite la
   consulta con la referencia completa (20 caracteres) de la primera
   unidad, que sí los da.
4. Abre esa URL en una pestaña nueva del navegador por defecto.
5. Muestra en la barra de mensajes de QGIS la referencia catastral completa
   (20 caracteres, con la unidad constructiva y los dos dígitos de control
   que ya calcula el propio Catastro — la que aparece en el recibo del IBI)
   y, si la parcela es rústica, también el polígono/parcela en formato
   `polígono-parcela` (p.ej. `1-10`), cada uno con un botón para copiarlo al
   portapapeles.

Si el punto pulsado cae en la calle o fuera de una parcela, el Catastro
devuelve un error ("para esas coordenadas no hay referencia disponible")
y el plugin lo muestra en la barra de mensajes de QGIS en vez de abrir nada.

**Buscar parcela (menú Catastrofe → Buscar parcela, panel lateral):** dos
pestañas, sin necesidad de tener el mapa centrado en la zona ni conocer sus
coordenadas:
- Por referencia catastral directa (14 caracteres).
- Por polígono y parcela rústicos (`Consulta_DNPPP`), dando la provincia y
  el municipio por su nombre (no código INE) más los números de polígono y
  parcela. Si una parcela tiene varias fincas asociadas (p.ej. una rústica y
  otra con edificación) se marca la primera y se avisa en el propio panel.

Al buscar, el panel ya muestra la referencia catastral completa (20
caracteres) y, si es rústica, el polígono/parcela — con su botón de copiar al
portapapeles cada uno — sin necesidad de pulsar después sobre la parcela en
el mapa. Además dibuja su contorno real (vía el WFS INSPIRE de parcelas
catastrales del propio Catastro) y hace zoom hasta ella; si ese contorno no
está disponible, marca al menos su centro. También activa la misma
herramienta de clic de siempre, así que si además se quiere abrir la ficha en
el navegador basta con pulsar sobre la parcela ya marcada.

**Datos ambientales (opcionales):** al pulsar sobre una parcela (o al
marcarla desde el panel de búsqueda) también se consulta, para ese mismo
punto:
- **Acuífero** y **zona inundable / dominio público hidráulico**: WFS
  público del MITECO (`gis.miteco.gob.es/geoserver/agua`). Es el único dato
  hídrico que ofrece de forma abierta y sin login para toda España
  (incluidas cuencas intracomunitarias); no hay dato público de concesiones
  de agua ni de comunidades de regantes.
- **Red Natura 2000**: si la parcela está dentro de un espacio protegido
  (ZEC/ZEPA), vía el WFS del IEPNB (`geoserver.iepnb.es/geoserver/RN2000`).

Se descartó mostrar el uso agrícola tipo SIGPAC (labor, olivar, viñedo...):
el servicio nacional solo tiene WMS con `GetFeatureInfo` por píxel, no WFS
por punto — bastante más frágil que los otros tres, así que no se integró.

**Ajustes (menú Catastrofe → Ajustes…):**
- Activar/desactivar cada uno de los tres avisos anteriores por separado
  (con los tres desactivados no se hace ninguna consulta ambiental extra).
- Estilo del resaltado de la parcela en el mapa: color y ancho del borde,
  y sombreado interior opcional (activarlo, color y opacidad).

Todo se guarda al momento (sin botón de guardar) y persiste entre sesiones
de QGIS.

**Limitación conocida:** el servicio del Catastro no cubre País Vasco ni
Navarra (tienen catastro foral propio, con sus propias sedes).

## Instalación (modo desarrollo)

```bash
ln -s ~/Projects/catastrofe ~/.local/share/QGIS/QGIS4/profiles/default/python/plugins/catastrofe
```

(La carpeta de perfil es `QGIS4` desde QGIS 4.x; en versiones 3.x sería `QGIS3`.)

Luego, en QGIS: *Complementos → Administrar e instalar complementos →
Instalados* y activar "Catastrofe". Aparecen dos iconos en la barra de
herramientas: el de clic en el mapa y el de "Buscar parcela" (abre el panel
lateral).

## Pruebas sin QGIS

La lógica de consulta al Catastro (`catastro_service.py`), al MITECO
(`hidro_service.py`) y a Red Natura 2000 (`natura_service.py`) no depende
de PyQGIS y se puede probar aparte:

```bash
python3 test_catastro_service.py
python3 test_hidro_service.py
python3 test_natura_service.py
```

Probado también dentro de QGIS real (QGIS 4.2.1) con `qgis.testing`
(mock de `iface` + `QgsApplication` en modo *offscreen*): clic en el mapa,
panel de búsqueda por referencia y por polígono/parcela, marcado en el mapa,
avisos ambientales, y el caso de parcela urbana con varias unidades
catastrales.

## Pendiente

- Decidir si se publica en el repositorio de plugins de QGIS: hace falta
  una cuenta en `plugins.qgis.org` (el `LICENSE` con el texto completo de
  la GPL-3.0-or-later ya está en el repo).
