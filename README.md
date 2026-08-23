# 🌐 SimpleBrowser Pro (Modern Desktop Browser)

Kevyt, moderni ja monivälilehtinen työpöytäselain Pythonilla ja PyQt6-WebEnginellä (Chromium-renderöinti). Sisältää automaattisen päivitystarkistimen, mainosten eston, sisäänrakennetun aloitussivun ja valmiin julkaisuputken nettiin.

---

## 🚀 Käynnistys kehitystilassa

```powershell
cd C:\Users\alexy\.gemini\antigravity\scratch\simple_browser
python main.py
```

---

## 📦 Kääntäminen itsenäiseksi `.exe` -ohjelmaksi

Voit luoda valmiin suoritettavan Windows-ohjelman paikallisesti:

```powershell
python build_exe.py
```

Käännetty ohjelma löytyy kansiosta `dist/SimpleBrowser/SimpleBrowser.exe`.

---

## 🌐 Julkaiseminen nettiin (GitHub & Automaattiset päivitykset)

### 1. Vie koodi GitHubiin:
```powershell
git init
git add .
git commit -m "Initial commit v1.0.0"
git remote add origin https://github.com/alexylivarvi-lang/simple-browser.git
git branch -M main
git push -u origin main
```

### 2. Julkaise uusi versio:
Aina kun haluat julkaista uuden päivityksen käyttäjille:
1. Päivitä versionumero tiedostosta [`updater.py`](file:///C:/Users/alexy/.gemini/antigravity/scratch/simple_browser/updater.py) (esim. `APP_VERSION = "1.1.0"`).
2. Luo ja lähetä uusi versiotagi:
```powershell
git add updater.py
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin v1.1.0
```
3. **GitHub Actions** kääntää automaattisesti uuden `SimpleBrowser-Windows.zip` -paketin ja liittää sen GitHub Releases -sivulle!
4. Kaikki selaimen olemassa olevat käyttäjät saavat automaattisesti ilmoituksen selaimen sisällä: *"Uusi versio v1.1.0 on saatavilla!"*.

---

## 📂 Käyttäjätietojen tallennus (`%APPDATA%`)

Päivitykset eivät koskaan ylikirjoita tai hävitä käyttäjän tietoja. Käyttäjän suosikit, historia ja asetukset säilytetään hakemistossa:
* **Windows:** `%APPDATA%\SimpleBrowser\` (`bookmarks.json`, `history.json`, `settings.json`)

---

## ✨ Tärkeimmät ominaisuudet

- **🛡️ AdBlock & Tracker Shield**: Reaaliaikainen mainosten ja seurannan esto estolaskurilla.
- **🪟 Speed Dial -aloitussivu**: Live-kello, päivämäärä, nopea hakukenttä ja pikalinkit.
- **🕵️ Incognito-yksityisselaus**: `Ctrl + Shift + N` avaa in-memory -profiilin ilman historian tallennusta.
- **📄 PDF-vienti**: `Ctrl + P` tallentaa minkä tahansa verkkosivun siistiksi PDF-asiakirjaksi.
- **🔊 Välilehtien mykistys**: Tunnistaa ääntä toistavat sivustot ja mahdollistaa mykistyksen (`🔇`).
- **🔍 Sivun sisäinen haku**: `Ctrl + F` hakukorostuksilla ja pikanäppäimillä.
- **📜 Selaushistoria**: `Ctrl + H` hakutoiminnolla.
- **🛠️ DevTools**: `F12` tai hiiren oikealla "Tarkasta elementti".
- **⚙️ Asetukset**: `Ctrl + ,` teeman vaihdolla (Dark/Light) ja päivitystarkistimella.
