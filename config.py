import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


APP_BG = "#0f172a"
CARD_BG = "#111827"
CARD_BG_2 = "#1f2937"
CARD_BG_3 = "#0f1b33"
TEXT_MAIN = "#f8fafc"
TEXT_SUB = "#94a3b8"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#ef4444"
BORDER = "#334155"
TEXTBOX_BG = "#020c1b"
SELECT_BORDER = "#60a5fa"

ICON_BOX_SIZE = 42
ICON_IMAGE_SIZE = 26

AUTHOR_NAME = "Ngọc Trinh"

BASE_DIR = resource_path(".")
IMG_DIR = resource_path("img")

APP_ICON_PATH = IMG_DIR / "logo-app.png"

BROWSER_LOGOS = {
    "Google Chrome": IMG_DIR / "chrome.png",
    "Microsoft Edge": IMG_DIR / "edge.png",
    "Mozilla Firefox": IMG_DIR / "firefox.png",
    "Brave": IMG_DIR / "brave.png",
    "Opera": IMG_DIR / "opera.png",
    "Opera GX": IMG_DIR / "opera_gx.png",
    "Vivaldi": IMG_DIR / "vivaldi.png",
    "CocCoc": IMG_DIR / "coccoc.png",
}