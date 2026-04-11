import re
import shutil
from pathlib import Path
from urllib.parse import unquote
from urllib.request import url2pathname
from config import resource_path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageGrab, ImageOps

try:
    import pytesseract
except ImportError:
    pytesseract = None

OCR_MEET_PATTERN = re.compile(
    r"https?://meet\.google\.com/[a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3}(?:[/?#][^\s]*)?",
    re.IGNORECASE,
)


def has_pytesseract() -> bool:
    return pytesseract is not None


def find_tesseract_cmd() -> str | None:
    if pytesseract is None:
        return None

    bundled_cmd = resource_path("tesseract/tesseract.exe")
    if Path(bundled_cmd).is_file():
        pytesseract.pytesseract.tesseract_cmd = str(bundled_cmd)
        return str(bundled_cmd)

    if getattr(pytesseract.pytesseract, "tesseract_cmd", None):
        cmd = pytesseract.pytesseract.tesseract_cmd
        if cmd and Path(cmd).is_file():
            return cmd

    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return found

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in common_paths:
        if Path(p).is_file():
            pytesseract.pytesseract.tesseract_cmd = p
            return p

    return None


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    prepared = image.convert("L")
    prepared = ImageOps.autocontrast(prepared)
    prepared = ImageEnhance.Contrast(prepared).enhance(2.0)
    prepared = prepared.filter(ImageFilter.MedianFilter(size=3))

    width, height = prepared.size
    upscale = 2 if max(width, height) < 1800 else 1
    if upscale > 1:
        prepared = prepared.resize((width * upscale, height * upscale), Image.LANCZOS)

    prepared = prepared.point(lambda px: 255 if px > 170 else 0)
    return prepared


def preprocess_image_for_ocr_soft(image: Image.Image) -> Image.Image:
    prepared = image.convert("L")
    prepared = ImageOps.autocontrast(prepared)
    prepared = ImageEnhance.Contrast(prepared).enhance(1.6)

    width, height = prepared.size
    upscale = 2 if max(width, height) < 1800 else 1
    if upscale > 1:
        prepared = prepared.resize((width * upscale, height * upscale), Image.LANCZOS)

    return prepared

def preprocess_image_for_ocr_invert(image: Image.Image) -> Image.Image:
    prepared = image.convert("L")
    prepared = ImageOps.autocontrast(prepared)
    prepared = ImageOps.invert(prepared)
    prepared = ImageEnhance.Contrast(prepared).enhance(2.2)

    width, height = prepared.size
    upscale = 2 if max(width, height) < 2200 else 1
    if upscale > 1:
        prepared = prepared.resize((width * upscale, height * upscale), Image.LANCZOS)

    prepared = prepared.filter(ImageFilter.MedianFilter(size=3))
    return prepared

def preprocess_image_for_ocr_blue_selection(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    r, g, b = rgb.split()

    diff = ImageChops.subtract(b, r)
    diff = ImageOps.autocontrast(diff)
    diff = ImageEnhance.Contrast(diff).enhance(2.4)

    width, height = diff.size
    upscale = 2 if max(width, height) < 2200 else 1
    if upscale > 1:
        diff = diff.resize((width * upscale, height * upscale), Image.LANCZOS)

    diff = diff.point(lambda px: 255 if px > 90 else 0)
    diff = ImageOps.invert(diff)
    return diff

def normalize_ocr_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    replacements = {
        "http ://": "http://",
        "http: //": "http://",
        "http : //": "http://",
        "https ://": "https://",
        "https: //": "https://",
        "https : //": "https://",
        "meet. google. com": "meet.google.com",
        "meet.google. com": "meet.google.com",
        "meet. google.com": "meet.google.com",
        "meet .google .com": "meet.google.com",
        "meet . google . com": "meet.google.com",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    normalized = re.sub(
        r"(?i)h\s*t\s*t\s*p\s*(s?)\s*:\s*/\s*/",
        lambda m: f"http{'s' if m.group(1) else ''}://",
        normalized,
    )
    normalized = re.sub(r"(?i)(https?://)\s+", r"\1", normalized)
    normalized = re.sub(r"(?i)meet\s*\.\s*google\s*\.\s*com", "meet.google.com", normalized)
    normalized = re.sub(r"(?i)meet\s+google\s+com", "meet.google.com", normalized)
    normalized = re.sub(r"(?i)meet\.google,com", "meet.google.com", normalized)
    normalized = re.sub(r"(?i)meet\.google\.\.com", "meet.google.com", normalized)
    normalized = re.sub(r"(/)\s+", r"\1", normalized)
    normalized = re.sub(r"\s+([/?#.:])", r"\1", normalized)
    normalized = re.sub(r"([/?#.:])\s+", r"\1", normalized)
    normalized = re.sub(r"(?<=[A-Za-z0-9])\s*-\s*(?=[A-Za-z0-9])", "-", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def extract_meet_links_from_ocr_text(text: str) -> list[str]:
    normalized = normalize_ocr_text(text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]

    collected: list[str] = []

    for line in lines:
        line = line.replace("|", "l")
        line = line.replace("!", "l")
        line = line.replace("’", "-").replace("'", "-").replace("`", "-")
        line = line.replace("_", "-")
        line = line.replace(" ", "")

        line = re.sub(r"(?i)^https?//", "https://", line)
        line = re.sub(r"(?i)^https:/", "https://", line)
        line = re.sub(r"(?i)^http://", "https://", line)

        line = line.replace("meetgooglecom", "meet.google.com")
        line = line.replace("meet.google,com", "meet.google.com")
        line = line.replace("meet.google..com", "meet.google.com")
        line = line.replace("meet,google,com", "meet.google.com")

        if "meet.google.com/" not in line:
            m = re.search(r"(?i)([a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3})", line)
            if m:
                line = f"https://meet.google.com/{m.group(1)}"

        matches = OCR_MEET_PATTERN.findall(line)
        if matches:
            collected.extend(matches)
            continue

        fallback = re.search(r"(?i)([a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3})", line)
        if fallback:
            collected.append(f"https://meet.google.com/{fallback.group(1)}")

    return collected


def _score_ocr_text(text: str) -> tuple[int, int]:
    lowered = text.lower()
    score = 0
    score += lowered.count("https") * 8
    score += lowered.count("meet") * 6
    score += lowered.count("google") * 6
    score += len(extract_meet_links_from_ocr_text(text)) * 50
    score += sum(ch.isalnum() for ch in text) // 20
    return score, len(text.strip())


def image_to_text(image: Image.Image, lang: str = "eng") -> str:
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed")
    tesseract_cmd = find_tesseract_cmd()
    if not tesseract_cmd:
        raise RuntimeError("Tesseract OCR is not installed or not found in PATH")
    bundled_tessdata = resource_path("tesseract/tessdata")
    if Path(bundled_tessdata).is_dir():
        import os
        os.environ["TESSDATA_PREFIX"] = str(bundled_tessdata)
    candidates = []
    variants = [
        (image.convert("RGB"), "--oem 3 --psm 6"),
        (image.convert("RGB"), "--oem 3 --psm 11"),
        (preprocess_image_for_ocr(image), "--oem 3 --psm 6"),
        (preprocess_image_for_ocr(image), "--oem 3 --psm 11"),
        (preprocess_image_for_ocr_soft(image), "--oem 3 --psm 6"),
        (preprocess_image_for_ocr_soft(image), "--oem 3 --psm 11"),
        (preprocess_image_for_ocr_invert(image), "--oem 3 --psm 6"),
        (preprocess_image_for_ocr_invert(image), "--oem 3 --psm 11"),
        (preprocess_image_for_ocr_blue_selection(image), "--oem 3 --psm 6"),
        (preprocess_image_for_ocr_blue_selection(image), "--oem 3 --psm 11"),
    ]

    for prepared, config in variants:
        try:
            text = pytesseract.image_to_string(prepared, lang=lang, config=config)
        except Exception:
            continue
        candidates.append((_score_ocr_text(text), text))

    if not candidates:
        raise RuntimeError("OCR failed to read the image")

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def parse_clipboard_to_image_path(text: str) -> Path | None:
    text = text.strip().strip('"').strip()
    if not text:
        return None

    if text.lower().startswith("file:///"):
        try:
            local_path = url2pathname(unquote(text[8:]))
            return Path(local_path)
        except Exception:
            return None

    if "\n" in text:
        first_line = text.splitlines()[0].strip().strip('"')
        if first_line:
            return Path(first_line)

    return Path(text)


def get_image_from_clipboard(root) -> Image.Image | None:
    try:
        img = ImageGrab.grabclipboard()
    except Exception:
        img = None

    if isinstance(img, Image.Image):
        return img.convert("RGBA")

    try:
        clip_text = root.clipboard_get().strip()
    except Exception:
        clip_text = None

    if clip_text:
        img_path = parse_clipboard_to_image_path(clip_text)
        if img_path is not None and img_path.is_file():
            return Image.open(img_path).convert("RGBA")

    return None
