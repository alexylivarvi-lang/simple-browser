"""
app_paths.py - Sovelluksen tietojen tallennussijaintien hallinta (%APPDATA%)
"""

import os
import shutil
import sys

APP_NAME = "SimpleBrowser"


def get_app_data_dir() -> str:
    """Palauttaa käyttäjäkohtaisen AppData-hakemiston ja luo sen tarvittaessa."""
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base_dir = os.path.expanduser("~/.config")

    app_dir = os.path.join(base_dir, APP_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_bookmarks_file() -> str:
    data_dir = get_app_data_dir()
    target_path = os.path.join(data_dir, "bookmarks.json")
    
    # Migraatio: jos paikallinen bookmarks.json on olemassa ja AppData-tiedosto puuttuu, kopioidaan se
    local_path = os.path.join(os.path.dirname(__file__), "bookmarks.json")
    if os.path.exists(local_path) and not os.path.exists(target_path):
        try:
            shutil.copy2(local_path, target_path)
        except Exception:
            pass

    return target_path


def get_history_file() -> str:
    data_dir = get_app_data_dir()
    target_path = os.path.join(data_dir, "history.json")
    
    local_path = os.path.join(os.path.dirname(__file__), "history.json")
    if os.path.exists(local_path) and not os.path.exists(target_path):
        try:
            shutil.copy2(local_path, target_path)
        except Exception:
            pass

    return target_path


def get_settings_file() -> str:
    data_dir = get_app_data_dir()
    target_path = os.path.join(data_dir, "settings.json")
    
    local_path = os.path.join(os.path.dirname(__file__), "settings.json")
    if os.path.exists(local_path) and not os.path.exists(target_path):
        try:
            shutil.copy2(local_path, target_path)
        except Exception:
            pass

    return target_path
