import polyline
import h3

H3_RESOLUTION = 9  # buen equilibrio ciudad / barrio


def polyline_to_h3(polyline_str: str) -> set[str]:
    """
    Convierte una polyline de Strava/Google en un set de hexágonos H3
    """
    coords = polyline.decode(polyline_str)  # [(lat, lon), ...]

    hexes: set[str] = set()

    for lat, lon in coords:
        hex_id = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
        hexes.add(hex_id)

    return hexes
