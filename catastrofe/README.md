# Catastrofe

Plugin de QGIS para consultar parcelas de la Sede Electrónica del Catastro y resaltarlas en el lienzo, sin necesidad de cargar una capa catastral.

## Búsqueda de parcelas

El panel lateral incluye tres métodos de búsqueda:

- **Por Ref**: referencia catastral (14 caracteres como mínimo).
- **Por Pol-Parc**: polígono y parcela rústicos, indicando provincia, municipio, polígono y parcela.
- **Por UTM**: coordenadas ETRS89, eligiendo el huso (28N, 29N, 30N o 31N; EPSG:25828-25831) e indicando X (Este) e Y (Norte). El huso elegido se guarda y se recupera la próxima vez (por defecto, 29N).

Se puede lanzar la búsqueda pulsando Intro en cualquier campo.

En cada resultado se muestra un **indicio de suelo urbano / no urbano** (deducido de la naturaleza catastral Urbana/Rústica; **no es la clasificación del planeamiento** y puede no coincidir, p. ej. en núcleos rurales), la referencia catastral y, cuando es una parcela rústica, el identificador **polígono-parcela** (por ejemplo, `1-10`). Ambos datos tienen su propio botón de copiar. También hay un botón para abrir manualmente la ficha en la Sede del Catastro.

## Modo acumulativo y limpieza

El interruptor **Modo acumulativo** permite conservar en el mapa las parcelas ya consultadas y añadir nuevas búsquedas. La parcela más reciente aparece arriba; las anteriores siguen disponibles debajo, con sus botones de copiar y abrir. Cada ficha tiene una **✕** (en la fila del indicio de suelo) para quitar solo esa parcela de la lista y del mapa, y con dos o más parcelas aparece **Copiar las N referencias** (una por línea). El panel se desplaza si la lista es larga.

Con el modo acumulativo desactivado, cada búsqueda sustituye el resultado y el resaltado anteriores. El botón **Limpiar** elimina todas las fichas y marcas. Si el modo acumulativo estaba activado, permanece activado después de limpiar, para poder empezar una nueva serie de consultas sin volver a marcar el interruptor.

El contorno se obtiene del WFS INSPIRE de parcelas catastrales del Catastro. Si no está disponible, el plugin marca el punto central de la parcela como alternativa.

## Ajustes

El botón **⚙** del panel (también en *Web → Catastrofe → Ajustes…*) permite configurar el color y el ancho del borde y el sombreado interior del resaltado. Los cambios se aplican al momento, también a las parcelas que ya están en el mapa.

## Clic en el mapa

La herramienta de clic consulta la parcela situada bajo el cursor y la envía al panel, con las mismas reglas que una búsqueda manual: dibuja el perímetro, respeta el modo acumulativo y muestra referencia y polígono-parcela con sus botones de copiar. No abre el navegador automáticamente: usa el botón **Abrir ficha en Sede del Catastro** cuando se quiera.

## Servicios

El plugin utiliza los servicios web libres de la Sede Electrónica del Catastro:

- `Consulta_RCCOOR`: coordenadas → referencia catastral.
- `Consulta_DNPRC`: referencia → datos y URL de ficha.
- `Consulta_DNPPP`: provincia, municipio, polígono y parcela → referencias catastrales.
- WFS INSPIRE de parcelas catastrales: geometría de la parcela.

**Limitación:** el servicio del Catastro no cubre País Vasco ni Navarra, que disponen de sus propios catastros forales.

## Instalación en modo desarrollo

Copia la carpeta del plugin en el directorio `python/plugins/catastrofe` del perfil de QGIS y actívalo desde *Complementos → Administrar e instalar complementos*.

## Pruebas

Los servicios se pueden probar con Python sin iniciar QGIS:

```bash
python3 tests/test_catastro_service.py
```

Las pruebas que consultan servicios remotos necesitan conexión a Internet.
