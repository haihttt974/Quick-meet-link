import os
import shutil
import winreg
from pathlib import Path

KNOWN_BROWSERS = [
    {
        "name": "Google Chrome",
        "exe_names": ["chrome.exe"],
        "path_keywords": ["google\\chrome"],
        "common_paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ],
    },
    {
        "name": "Microsoft Edge",
        "exe_names": ["msedge.exe"],
        "path_keywords": ["microsoft\\edge"],
        "common_paths": [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
        ],
    },
    {
        "name": "Mozilla Firefox",
        "exe_names": ["firefox.exe"],
        "path_keywords": ["mozilla firefox"],
        "common_paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe",
        ],
    },
    {
        "name": "Brave",
        "exe_names": ["brave.exe"],
        "path_keywords": ["bravesoftware\\brave-browser"],
        "common_paths": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
    },
    {
        "name": "Opera",
        "exe_names": ["opera.exe"],
        "path_keywords": ["opera"],
        "common_paths": [
            r"C:\Program Files\Opera\launcher.exe",
            r"C:\Program Files\Opera\opera.exe",
            r"%LOCALAPPDATA%\Programs\Opera\opera.exe",
            r"%APPDATA%\Opera Software\Opera Stable\opera.exe",
        ],
    },
    {
        "name": "Opera GX",
        "exe_names": ["opera.exe"],
        "path_keywords": ["opera gx", "opera software\\opera gx stable"],
        "common_paths": [
            r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe",
            r"%APPDATA%\Opera Software\Opera GX Stable\opera.exe",
        ],
    },
    {
        "name": "Vivaldi",
        "exe_names": ["vivaldi.exe"],
        "path_keywords": ["vivaldi"],
        "common_paths": [
            r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
            r"C:\Program Files (x86)\Vivaldi\Application\vivaldi.exe",
            r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe",
        ],
    },
    {
        "name": "CocCoc",
        "exe_names": ["browser.exe"],
        "path_keywords": ["coccoc\\browser"],
        "common_paths": [
            r"C:\Program Files\CocCoc\Browser\Application\browser.exe",
            r"C:\Program Files (x86)\CocCoc\Browser\Application\browser.exe",
            r"%LOCALAPPDATA%\CocCoc\Browser\Application\browser.exe",
        ],
    },
]

REGISTRY_APP_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\{exe}",
]


def expand_env(path: str) -> str:
    return os.path.expandvars(path)


def norm(path: str) -> str:
    return str(Path(path)).strip().strip('"')


def exists_file(path: str) -> bool:
    try:
        return os.path.isfile(path)
    except OSError:
        return False


def canonical(path: str) -> str:
    try:
        return str(Path(path).resolve())
    except OSError:
        return path


def try_registry_value(root, subkey, value_name=None):
    try:
        with winreg.OpenKey(root, subkey) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except OSError:
        return None


def score_candidate(browser_def: dict, path: str) -> int:
    p = path.lower()
    exe = os.path.basename(p)
    score = 0

    if exe in [x.lower() for x in browser_def["exe_names"]]:
        score += 20

    keyword_hit = any(k in p for k in [x.lower() for x in browser_def["path_keywords"]])
    if keyword_hit:
        score += 80

    expanded_common = [norm(expand_env(x)).lower() for x in browser_def["common_paths"]]
    if p in expanded_common:
        score += 30

    if exe == "browser.exe" and not keyword_hit:
        return -1

    return score


def get_candidates_from_path():
    results = []
    seen = set()

    exe_names = sorted({exe for b in KNOWN_BROWSERS for exe in b["exe_names"]})
    for exe in exe_names:
        found = shutil.which(exe)
        if found:
            real = canonical(found)
            if real.lower() not in seen:
                results.append(real)
                seen.add(real.lower())

    return results


def get_candidates_from_registry():
    results = []
    seen = set()

    exe_names = sorted({exe for b in KNOWN_BROWSERS for exe in b["exe_names"]})

    for exe in exe_names:
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sub_fmt in REGISTRY_APP_PATHS:
                subkey = sub_fmt.format(exe=exe)
                val = try_registry_value(root, subkey)

                if isinstance(val, str):
                    val = norm(val)
                    if exists_file(val):
                        real = canonical(val)
                        if real.lower() not in seen:
                            results.append(real)
                            seen.add(real.lower())

    return results


def get_candidates_from_common_paths():
    results = []
    seen = set()

    for browser in KNOWN_BROWSERS:
        for path in browser["common_paths"]:
            p = norm(expand_env(path))
            if exists_file(p):
                real = canonical(p)
                if real.lower() not in seen:
                    results.append(real)
                    seen.add(real.lower())

    return results


def detect_default_browser():
    progid = try_registry_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
        "ProgId",
    )

    if not isinstance(progid, str):
        return None

    progid = progid.lower()

    mapping = {
        "chromehtml": "Google Chrome",
        "mseedgehtm": "Microsoft Edge",
        "firefoxurl": "Mozilla Firefox",
        "bravehtml": "Brave",
        "vivaldihtm": "Vivaldi",
        "opera": "Opera",
    }

    for key, name in mapping.items():
        if key in progid:
            return name

    return None


def classify_candidates(paths):
    best = {}

    for path in paths:
        for browser in KNOWN_BROWSERS:
            score = score_candidate(browser, path)
            if score < 20:
                continue

            name = browser["name"]
            current = best.get(name)

            if current is None or score > current["score"]:
                best[name] = {
                    "name": name,
                    "path": path,
                    "score": score,
                }

    return sorted(best.values(), key=lambda x: x["name"])


def get_installed_browsers():
    paths = []
    paths += get_candidates_from_path()
    paths += get_candidates_from_registry()
    paths += get_candidates_from_common_paths()

    unique = []
    seen = set()

    for p in paths:
        cp = canonical(p)
        if cp.lower() not in seen and exists_file(cp):
            unique.append(cp)
            seen.add(cp.lower())

    browsers = classify_candidates(unique)
    default = detect_default_browser()

    for b in browsers:
        b["is_default"] = (b["name"] == default)

    return {
        "default_browser_name": default,
        "browsers": browsers,
    }


if __name__ == "__main__":
    data = get_installed_browsers()
    print(data)