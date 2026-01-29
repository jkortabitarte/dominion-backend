from collections import Counter
from app.models import Activity, TerritoryInfluence
from app.utils.geo import polyline_to_h3


def process_strava_activity(db, user, strava_activity, influence_cache):
    polyline = strava_activity.get("map", {}).get("summary_polyline")
    if not polyline:
        return False

    # evitar duplicados de actividad
    existing = (
        db.query(Activity)
        .filter(Activity.strava_activity_id == strava_activity["id"])
        .first()
    )
    if existing:
        return False

    # guardar actividad
    activity = Activity(
        user_id=user.id,
        strava_activity_id=strava_activity["id"],
        polyline=polyline,
    )
    db.add(activity)

    hexes = polyline_to_h3(polyline)
    hex_counter = Counter(hexes)

    for hex_id, count in hex_counter.items():
        key = (hex_id, user.id)

        if key in influence_cache:
            influence_cache[key].influence += count
            continue

        influence = (
            db.query(TerritoryInfluence)
            .filter_by(
                territory_id=hex_id,
                user_id=user.id,
            )
            .first()
        )

        if influence:
            influence.influence += count
            influence_cache[key] = influence
        else:
            influence = TerritoryInfluence(
                territory_id=hex_id,
                user_id=user.id,
                influence=count,
            )
            db.add(influence)
            influence_cache[key] = influence

    return True
