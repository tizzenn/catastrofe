"""Pruebas manuales contra el servicio real del Catastro (sin QGIS).
Ejecutar: python3 test_catastro_service.py
"""
from catastro_service import (
    CatastroLookupError,
    datos_ficha,
    formato_poligono_parcela,
    naturaleza_parcela,
    normalizar_referencia,
    refcats_en_poligono_parcela,
    url_sedecatastro_para_punto,
)

CASOS_NORMALIZACION = [
    # (entrada, esperado_o_None_si_debe_fallar, descripcion)
    ("46138A00100010", "46138A00100010", "14 caracteres, ya normalizada"),
    ("46138a00100010", "46138A00100010", "minúsculas"),
    (" 46138A0 0100010 ", "46138A00100010", "con espacios, como se copia a veces"),
    ("46138A001000100000WX", "46138A00100010", "20 caracteres (referencia completa con unidad+control)"),
    ("46138A0010001", None, "13 caracteres, insuficiente"),
]

CASOS_PUNTO = [
    # (lon, lat, descripcion, se_espera_url)
    (-0.645262634278451, 39.4080401884542, "parcela real en Godelleta (Valencia)", True),
    (-3.7038, 40.4168, "Puerta del Sol, vía pública sin parcela", False),
]

CASOS_POLIGONO_PARCELA = [
    # (provincia, municipio, poligono, parcela, descripcion, se_espera_resultado)
    ("VALENCIA", "GODELLETA", "1", "10", "polígono/parcela real en Godelleta", True),
    ("VALENCIA", "GODELLETA", "1", "1", "polígono/parcela inexistente en Godelleta", False),
]

CASOS_NATURALEZA = [
    # (refcat14, naturaleza_esperada, descripcion)
    ("46138A00100010", "Rústica", "Godelleta, resultado único"),
    ("0443104VK4704C", "Urbana", "Madrid Carretas 10, varias unidades catastrales"),
]

CASOS_POLIGONO_PARCELA_FORMATO = [
    # (refcat14, esperado, descripcion)
    ("46138A00100010", "1-10", "rústica con ceros a la izquierda"),
    ("46138A12312345", "123-12345", "rústica sin ceros a la izquierda"),
    ("0443104VK4704C", None, "urbana, no tiene polígono/parcela"),
]


def main():
    fallos = 0
    for entrada, esperado, descripcion in CASOS_NORMALIZACION:
        try:
            resultado = normalizar_referencia(entrada)
            ok = resultado == esperado
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {resultado!r}")
            fallos += 0 if ok else 1
        except CatastroLookupError as exc:
            ok = esperado is None
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: error -> {exc}")
            fallos += 0 if ok else 1

    for lon, lat, descripcion, se_espera_url in CASOS_PUNTO:
        try:
            url = url_sedecatastro_para_punto(lon, lat)
            ok = se_espera_url
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {url}")
            fallos += 0 if ok else 1
        except CatastroLookupError as exc:
            ok = not se_espera_url
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: error -> {exc}")
            fallos += 0 if ok else 1

    for provincia, municipio, poligono, parcela, descripcion, se_espera_resultado in CASOS_POLIGONO_PARCELA:
        try:
            refcats = refcats_en_poligono_parcela(provincia, municipio, poligono, parcela)
            ok = se_espera_resultado
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {refcats}")
            fallos += 0 if ok else 1
        except CatastroLookupError as exc:
            ok = not se_espera_resultado
            print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: error -> {exc}")
            fallos += 0 if ok else 1

    for refcat, esperado, descripcion in CASOS_NATURALEZA:
        naturaleza = naturaleza_parcela(refcat)
        ok = naturaleza == esperado
        print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {naturaleza}")
        fallos += 0 if ok else 1

        datos = datos_ficha(refcat)
        ok = bool(datos.get("url")) and datos.get("naturaleza") == esperado
        print(f"[{'OK' if ok else 'FALLO'}] {descripcion} (datos_ficha): {datos}")
        fallos += 0 if ok else 1

    for refcat, esperado, descripcion in CASOS_POLIGONO_PARCELA_FORMATO:
        resultado = formato_poligono_parcela(refcat)
        ok = resultado == esperado
        print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {resultado!r}")
        fallos += 0 if ok else 1

    if fallos:
        raise SystemExit(f"{fallos} caso(s) fallido(s)")
    print("Todo correcto.")


if __name__ == "__main__":
    main()
