"""Pruebas manuales contra el servicio real del Catastro (sin QGIS).
Ejecutar: python3 test_catastro_service.py
"""
from catastro_service import CatastroLookupError, refcats_en_poligono_parcela, url_sedecatastro_para_punto

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


def main():
    fallos = 0
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

    if fallos:
        raise SystemExit(f"{fallos} caso(s) fallido(s)")
    print("Todo correcto.")


if __name__ == "__main__":
    main()
