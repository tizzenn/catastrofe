"""Pruebas manuales contra el WFS real del MITECO (sin QGIS).
Ejecutar: python3 test_hidro_service.py
"""
from hidro_service import acuifero_en_punto, zonas_inundables_en_punto

CASOS = [
    # (lon, lat, descripcion, se_espera_acuifero)
    (-0.718034385933521, 39.4365562166977, "parcela real en Godelleta (Valencia)", True),
]


def main():
    fallos = 0
    for lon, lat, descripcion, se_espera_acuifero in CASOS:
        acuifero = acuifero_en_punto(lon, lat)
        ok = bool(acuifero) == se_espera_acuifero
        print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: acuífero -> {acuifero}")
        fallos += 0 if ok else 1

        zonas = zonas_inundables_en_punto(lon, lat)
        print(f"      zonas inundables -> {zonas or 'ninguna'}")

    if fallos:
        raise SystemExit(f"{fallos} caso(s) fallido(s)")
    print("Todo correcto.")


if __name__ == "__main__":
    main()
