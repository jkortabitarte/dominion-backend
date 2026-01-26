from app.models import Activity, TerritoryInfluence
from app.utils.geo import polyline_to_h3


def process_strava_activity(db, user, strava_activity):
    polyline = strava_activity.get("map", {}).get("summary_polyline")
    if not polyline:
        return False  # actividades sin GPS

    # 🔁 evitar duplicados
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

    # 2️⃣ convertir a hexágonos
    hexes = polyline_to_h3(polyline)

    # 3️⃣ actualizar influencia
    for hex_id in hexes:
        influence = (
            db.query(TerritoryInfluence)
            .filter_by(
                territory_id=hex_id,
                user_id=user.id,
            )
            .first()
        )

        if influence:
            influence.influence += 1
        else:
            db.add(
                TerritoryInfluence(
                    territory_id=hex_id,
                    user_id=user.id,
                    influence=1,
                )
            )

    return True
