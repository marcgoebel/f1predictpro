import os
import sys
import pandas as pd
import fastf1
import joblib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.feature_engineering import (
    get_track_affinity,
    get_team_strength,
    estimate_momentum
)

# 🔧 Fix für Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
fastf1.Cache.enable_cache("cache")

# 📍 Eingabe
YEAR = 2024
RACE_NAME = "Austria"

# Lade Modell
model = joblib.load("models/rf_model_position_classifier.pkl")

# Lade Session
session = fastf1.get_session(YEAR, RACE_NAME, "R")
session.load()
laps = session.laps.pick_quicklaps()
drivers = laps["Driver"].unique()

# Vorhersagen sammeln
predictions = []

for drv in drivers:
    d_laps = laps[laps["Driver"] == drv]
    if d_laps.empty:
        continue

    try:
        fastest_lap = d_laps["LapTime"].min().total_seconds()
        avg_lap = d_laps["LapTime"].mean().total_seconds()
        stints = d_laps["Stint"].nunique()
        pitstops = d_laps["PitOutTime"].count()
        laps_completed = d_laps["LapNumber"].max()
        team = d_laps["Team"].iloc[0]

        X = pd.DataFrame([{
            "fastest_lap": fastest_lap,
            "avg_lap": avg_lap,
            "stints": stints,
            "pitstops": pitstops,
            "laps_completed": laps_completed,
            "track_affinity": get_track_affinity(RACE_NAME, drv),
            "team_strength": get_team_strength(team),
            "momentum": estimate_momentum(drv)
        }])

        proba = model.predict_proba(X)[0]
        for i, p in enumerate(proba, start=1):
            predictions.append({
                "year": YEAR,
                "race": RACE_NAME,
                "driver": drv,
                "position": i,
                "probability": round(p * 100, 2)
            })

    except Exception as e:
        print(f"❌ Fehler bei {drv}: {e}")

# 🔁 Ergebnis speichern
df = pd.DataFrame(predictions)
os.makedirs("data/live", exist_ok=True)
out_path = f"data/live/position_probabilities_{YEAR}_{RACE_NAME}.csv"
df.to_csv(out_path, index=False)

print(f"\n✅ Live-Prognosen gespeichert unter: {out_path}")
print(df[df["position"] <= 3].sort_values("probability", ascending=False).head(10))
