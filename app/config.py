from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ML_MODELS_DIR = BASE_DIR / "ml_models"

APP_NAME = os.getenv("APP_NAME", "Lotto Edge")
APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/lottoedge.db")

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
ML_MODELS_DIR.mkdir(exist_ok=True)

# Game identifiers
GAMES = {
    "lotto": {
        "name": "Texas Lotto",
        "pick": 6,
        "pool": 54,
        "csv_file": DATA_DIR / "texas_lotto.csv",
    },
    "twostep": {
        "name": "Texas Two Step",
        "pick": 4,
        "pool": 35,
        "bonus_pool": 35,
        "csv_file": DATA_DIR / "texas_two_step.csv",
    },
    "powerball": {
        "name": "Powerball",
        "pick": 5,
        "pool": 69,
        "bonus_pool": 26,
        "csv_file": DATA_DIR / "powerball.csv",
    },
}
