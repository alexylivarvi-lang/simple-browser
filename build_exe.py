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
        "--name", "SimpleBrowser",
        "main.py",
    ]

    print(f"Suoritetaan komento: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist", "SimpleBrowser"))
        print("\n==========================================")
        print("✅ KÄÄNNÖS VALMIS ONNISTUNEESTI!")
        print(f"Valmis ohjelma löytyy kansiosta:\n{dist_path}")
        print("Voit käynnistää ohjelman tiedostosta: SimpleBrowser.exe")
        print("==========================================\n")
    else:
        print("\n❌ Käännös epäonnistui virhekoodilla:", result.returncode)


if __name__ == "__main__":
    build()
