"""
Manual approval only
"""
import shutil

CONFIRMED = input("Promote model to LIVE? (yes/no): ")

if CONFIRMED == "yes":
    shutil.move(
        "models/model_candidate.joblib",
        "models/model_v1.1.0.joblib"
    )
    print("Model promoted — update ACTIVE_MODEL_VERSION manually")
