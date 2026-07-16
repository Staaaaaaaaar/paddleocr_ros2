from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = SERVICE_ROOT / "config"
ASSETS_DIR = SERVICE_ROOT / "assets"
TEMPLATE_DIR = ASSETS_DIR / "digit_templates"
OUTPUT_DIR = SERVICE_ROOT / "output"

ROI_CONFIG = CONFIG_DIR / "rois.json"
COMPASS_CONFIG = CONFIG_DIR / "compass.json"
DIGIT_SLOTS_CONFIG = CONFIG_DIR / "digit_slots.json"
