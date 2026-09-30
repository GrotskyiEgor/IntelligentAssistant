from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_JSON_PATH = ROOT / "core" / "commands.json"

ACTION_THRESHOLD = 80
APP_THRESHOLD = 60