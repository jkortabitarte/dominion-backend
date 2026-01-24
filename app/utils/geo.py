import polyline
import h3

H3_RESOLUTION = 9  # buen equilibrio ciudad

def polyline_to_h3(polyline_str: str) -> set[str]:
    coords = polyline.decode(polyline_str)  # [(lat, lon), ...]
    hexes = set()

    for lat, lon in coords:
        hex_id = h3.geo_to_h3(lat, lon, H3_RESOLUTION)
        hexes.add(hex_id)

    return hexes
