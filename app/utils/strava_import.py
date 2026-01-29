from collections import Counter
from app.models import Activity, TerritoryInfluence
from app.utils.geo import polyline_to_h3


def process_strava_activity(db, user, strava_activity):
    polyline = strava_activity.get("map", {}).get("summary_polyline")
    if not polyline:
        return False

    # 🔁 evitar duplicados de actividad
    existing = (
        db.query(Activity)
        .filter(Activity.strava_activity_id == strava_activity["id"])
        .first()
    )
    if existing:
        return False

    # 1️⃣ guardar actividad
    activity = Activity(
        user_id=user.id,
        strava_activity_id=strava_activity["id"],
        polyline=polyline,
    )
    db.add(activity)

    # 2️⃣ hexágonos + conteo
    hexes = polyline_to_h3(polyline)
    hex_counter = Counter(hexes)

    # 3️⃣ actualizar influencia (1 vez por hex)
    for hex_id, count in hex_counter.items():
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
        else:
            db.add(
                TerritoryInfluence(
                    territory_id=hex_id,
                    user_id=user.id,
                    influence=count,
                )
            )

    return True
