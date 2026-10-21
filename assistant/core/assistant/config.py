from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_JSON_PATH = ROOT / "core" / "commands.json"

ACTION_THRESHOLD = 80
APP_THRESHOLD = 60

SETTIGNS_JSON_PATH = ROOT / "settings.json"
ASSISTANT_NAMES = ["омі", "оми"]
NAME_THRESHOLD = 80