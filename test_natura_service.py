"""Pruebas manuales contra el WFS real de Red Natura 2000 (sin QGIS).
Ejecutar: python3 test_natura_service.py
"""
from natura_service import espacios_en_punto

CASOS = [
    # (lon, lat, descripcion, se_espera_algun_espacio)
    (-6.35, 37.0, "dentro del parque de Doñana", True),
    (-3.7038, 40.4168, "Puerta del Sol, fuera de cualquier espacio protegido", False),
]


def main():
    fallos = 0
    for lon, lat, descripcion, se_espera in CASOS:
        espacios = espacios_en_punto(lon, lat)
        ok = bool(espacios) == se_espera
        print(f"[{'OK' if ok else 'FALLO'}] {descripcion}: {espacios or 'ninguno'}")
        fallos += 0 if ok else 1

    if fallos:
        raise SystemExit(f"{fallos} caso(s) fallido(s)")
    print("Todo correcto.")


if __name__ == "__main__":
    main()
