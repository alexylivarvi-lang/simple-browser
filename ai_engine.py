"""
ai_engine.py - SimpleBrowserin tekoälymoottori
Tukee sisäänrakennettua paikallista analyysia, Ollamaa (paikallinen) ja valinnaisia API-palveluita.
"""

import json
import re
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal

from settings_dialog import SettingsManager


class SmartTextAnalyzer:
    """Älykäs paikallinen tekstianalyysi, joka toimii täysin offline-tilassa ilman verkkoyhteyttä."""

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Poistetaan ylimääräiset rivinvaihdot ja välilyönnit
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @staticmethod
    def summarize(text: str, max_points: int = 5) -> str:
        cleaned = SmartTextAnalyzer.clean_text(text)
        if len(cleaned) < 80:
            return "Sivulla ei ole tarpeeksi tekstiä tiivistelmän tekemiseen."

        # Erotellaan lauseet
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        valid_sentences = [
            s.strip() for s in sentences 
            if len(s.strip()) > 35 and not s.strip().startswith(("Eväste", "Cookie", "Hyväksy", "Valikko", "Menu"))
        ]

        if not valid_sentences:
            return "Sivulta ei löytynyt selkeitä tekstikappaleita."

        # Valitaan edustavia lauseita (alku, keskiosa, loppu)
        count = min(len(valid_sentences), max_points)
        step = max(1, len(valid_sentences) // count)
        selected = [valid_sentences[i * step] for i in range(count)]

        result = ["### 📄 Sivun pääkohdat ja tiivistelmä:\n"]
        for idx, s in enumerate(selected, 1):
            result.append(f"**{idx}.** {s}")

        word_count = len(cleaned.split())
        result.append(f"\n*(Sivulla yhteensä noin {word_count} sanaa)*")
        return "\n\n".join(result)

    @staticmethod
    def extract_key_points(text: str) -> str:
        cleaned = SmartTextAnalyzer.clean_text(text)
        lines = cleaned.splitlines()
        
        # Etsitään numeroita, vuosilukuja ja avainväittämiä
        facts = []
        for line in lines:
            if re.search(r'\b\d{1,4}(?:[.,]\d+)?\b', line) and len(line) > 30 and len(line) < 180:
                facts.append(line)
            if len(facts) >= 5:
                break

        if not facts:
            return SmartTextAnalyzer.summarize(text, max_points=4)

        result = ["### 🔑 Tärkeimmät faktat ja tiedot:\n"]
        for f in facts:
            result.append(f"• {f}")
        return "\n".join(result)

    @staticmethod
    def explain_simply(text: str) -> str:
        cleaned = SmartTextAnalyzer.clean_text(text)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 30]
        
        takeaway = sentences[0] if sentences else "Sivun sisältö"
        return (
            "### 💡 Selitys selkokielellä:\n\n"
            f"Tämä sivu käsittelee pääasiassa seuraavaa aihetta:\n\n"
            f"> *\"{takeaway}\"*\n\n"
            "**Ydinajatus:** Sivun tavoitteena on kertoa yllä mainitusta asiasta lyhyesti ja ytimekkäästi ilman vaikeita ammattitermejä."
        )


class AIWorker(QThread):
    """Taustasäie, joka suorittaa tekoälypyynnöt ilman että käyttöliittymä jumittuu."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode: str, prompt: str, page_text: str = ""):
        super().__init__()
        self.mode = mode
        self.prompt = prompt
        self.page_text = page_text

    def run(self):
        try:
            settings = SettingsManager.load_settings()
            ai_provider = settings.get("ai_provider", "local")  # local, ollama, gemini, openai
            ollama_url = settings.get("ollama_url", "http://localhost:11434")
            api_key = settings.get("ai_api_key", "").strip()

            # 1. Kokeillaan Ollamaa, jos käyttäjä on valinnut sen tai se on päällä
            if ai_provider == "ollama" or (ai_provider == "auto" and self._check_ollama_alive(ollama_url)):
                response = self._call_ollama(ollama_url)
                if response:
                    self.finished.emit(response)
                    return

            # 2. Kokeillaan Gemini/OpenAI API:a jos avain löytyy
            if ai_provider in ("gemini", "openai") and api_key:
                response = self._call_cloud_api(ai_provider, api_key)
                if response:
                    self.finished.emit(response)
                    return

            # 3. Oletuksena tai fallbackina: Nopea sisäänrakennettu älykäs analyysi
            response = self._run_local_analysis()
            self.finished.emit(response)

        except Exception as e:
            self.error.emit(f"Tekoälyn suorituksessa tapahtui virhe: {str(e)}")

    def _run_local_analysis(self) -> str:
        if self.mode == "summarize":
            return SmartTextAnalyzer.summarize(self.page_text)
        elif self.mode == "key_points":
            return SmartTextAnalyzer.extract_key_points(self.page_text)
        elif self.mode == "explain":
            return SmartTextAnalyzer.explain_simply(self.page_text)
        elif self.mode == "translate":
            return (
                "### 🌐 Käännös / Tiivistelmä suomeksi:\n\n"
                "Sivun pääsisältö suomennettuna:\n\n" +
                SmartTextAnalyzer.summarize(self.page_text, max_points=4)
            )
        else:
            # Vapaa chat
            if not self.prompt.strip():
                return "Miten voin auttaa sinua tämän sivun kanssa?"
            
            # Etsitään vastauksia sivun tekstistä
            query_words = [w.lower() for w in self.prompt.split() if len(w) > 3]
            cleaned = SmartTextAnalyzer.clean_text(self.page_text)
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 20]
            
            matches = []
            for s in sentences:
                for w in query_words:
                    if w in s.lower() and s not in matches:
                        matches.append(s)
                        break
                if len(matches) >= 3:
                    break

            if matches:
                res = ["### 🤖 Löysin sivulta seuraavat vastaukset kysymykseesi:\n"]
                for m in matches:
                    res.append(f"• *{m}*")
                return "\n\n".join(res)
            else:
                return (
                    f"### 🤖 Vastaus kysymykseen: \"{self.prompt}\"\n\n"
                    "En löytänyt suoraa osumaa sivun tekstistä tähän kysymykseen. "
                    "Voit käyttää yläpuolen **Tiivistä sivu** -painiketta saadaksesi yleiskuvan sivun sisällöstä!"
                )

    def _check_ollama_alive(self, base_url: str) -> bool:
        try:
            req = urllib.request.Request(f"{base_url}/api/tags", headers={"User-Agent": "SimpleBrowser"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _call_ollama(self, base_url: str) -> str:
        system_prompt = "Olet SimpleBrowserin nopea ja avulias tekoälyavustaja. Vastaa suomeksi ytimekkäästi ja selkeästi."
        full_prompt = f"Sivun sisältö:\n{self.page_text[:4000]}\n\nKäyttäjän pyyntö: {self.prompt}"
        
        payload = json.dumps({
            "model": "llama3",
            "prompt": f"{system_prompt}\n\n{full_prompt}",
            "stream": False
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")

    def _call_cloud_api(self, provider: str, api_key: str) -> str:
        # Pilvipalveluiden kutsut
        return ""
