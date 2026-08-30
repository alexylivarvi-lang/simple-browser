"""
build_exe.py - Paketoi selaimen Windows .exe -ohjelmaksi PyInstallerilla
"""

import os
import subprocess
import sys


def build():
    print("=== Aloitetaan SimpleBrowser .exe -paketti ===")
    
    # Varmistetaan PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("Asennetaan PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon=icon.ico",
        "--name", "SimpleBrowser",
        "main.py",
    ]

    print(f"Suoritetaan komento: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist", "SimpleBrowser.exe"))
        print("\n==========================================")
        print("[OK] KAANNOS VALMIS ONNISTUNEESTI!")
        print(f"Valmis ohjelma loytyy tiedostosta:\n{dist_path}")
        print("==========================================\n")
    else:
        print("\n[VIRHE] Kaannos epaonnistui virhekoodilla:", result.returncode)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
