"""
new_tab_page.py - Moderni sisäänrakennettu aloitussivu (Speed Dial Dashboard)
"""

from settings_dialog import SettingsManager


def get_new_tab_html(theme: str = "Dark") -> str:
    settings = SettingsManager.load_settings()
    engine = settings.get("search_engine", "DuckDuckGo")

    bg_color = "#121217" if theme == "Dark" else "#f4f6f9"
    card_bg = "rgba(34, 34, 46, 0.7)" if theme == "Dark" else "rgba(255, 255, 255, 0.85)"
    text_color = "#f0f0f5" if theme == "Dark" else "#1a1a24"
    sub_color = "#8b8b9e" if theme == "Dark" else "#636378"
    input_bg = "rgba(24, 24, 32, 0.8)" if theme == "Dark" else "rgba(255, 255, 255, 0.95)"
    input_border = "#3a3a4c" if theme == "Dark" else "#d0d4dc"
    hover_bg = "#2f2f42" if theme == "Dark" else "#e6eaf0"

    speed_dials = [
        {"name": "DuckDuckGo", "url": "https://duckduckgo.com", "icon": "🦆", "color": "#de5833"},
        {"name": "Google", "url": "https://www.google.com", "icon": "🔍", "color": "#4285f4"},
        {"name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️", "color": "#ff0000"},
        {"name": "GitHub", "url": "https://github.com", "icon": "🐙", "color": "#24292e"},
        {"name": "Wikipedia", "url": "https://fi.wikipedia.org", "icon": "📚", "color": "#636466"},
        {"name": "Yle Uutiset", "url": "https://yle.fi/uutiset", "icon": "📰", "color": "#00b4d8"},
        {"name": "Reddit", "url": "https://www.reddit.com", "icon": "💬", "color": "#ff4500"},
        {"name": "Python Docs", "url": "https://docs.python.org/3/", "icon": "🐍", "color": "#306998"},
    ]

    cards_html = ""
    for item in speed_dials:
        cards_html += f"""
        <a class="dial-card" href="{item['url']}">
            <div class="dial-icon" style="background-color: {item['color']}15;">{item['icon']}</div>
            <div class="dial-title">{item['name']}</div>
        </a>
        """

    html = f"""<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <title>Uusi välilehti</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            user-select: none;
        }}
        body {{
            background: {bg_color};
            color: {text_color};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
            transition: background 0.3s ease;
        }}
        .container {{
            max-width: 820px;
            width: 100%;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .clock {{
            font-size: 56px;
            font-weight: 300;
            letter-spacing: 2px;
            margin-bottom: 6px;
        }}
        .date {{
            font-size: 15px;
            color: {sub_color};
            margin-bottom: 32px;
            text-transform: capitalize;
        }}
        .search-form {{
            width: 100%;
            max-width: 600px;
            margin-bottom: 40px;
            position: relative;
        }}
        .search-input {{
            width: 100%;
            padding: 15px 22px;
            font-size: 16px;
            border-radius: 28px;
            border: 1px solid {input_border};
            background: {input_bg};
            color: {text_color};
            outline: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
            transition: all 0.2s ease;
        }}
        .search-input:focus {{
            border-color: #4361ee;
            box-shadow: 0 6px 20px rgba(67, 97, 238, 0.18);
        }}
        .dials-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            width: 100%;
        }}
        .dial-card {{
            background: {card_bg};
            border-radius: 14px;
            padding: 18px 12px;
            text-decoration: none;
            color: {text_color};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(8px);
            border: 1px solid transparent;
        }}
        .dial-card:hover {{
            background: {hover_bg};
            transform: translateY(-3px);
            border-color: rgba(67, 97, 238, 0.3);
            box-shadow: 0 8px 16px rgba(0,0,0,0.12);
        }}
        .dial-icon {{
            font-size: 26px;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            margin-bottom: 10px;
        }}
        .dial-title {{
            font-size: 13px;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="clock" id="clock">12:00</div>
        <div class="date" id="date">Maanantai, 1. tammikuuta</div>

        <form class="search-form" id="searchForm" onsubmit="handleSearch(event)">
            <input type="text" class="search-input" id="searchBar" placeholder="Hae hakukoneella ({engine}) tai siirry osoitteeseen..." autofocus autocomplete="off">
        </form>

        <div class="dials-grid">
            {cards_html}
        </div>
    </div>

    <script>
        function updateClock() {{
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('clock').textContent = `${{hours}}:${{minutes}}`;

            const options = {{ weekday: 'long', day: 'numeric', month: 'long' }};
            document.getElementById('date').textContent = now.toLocaleDateString('fi-FI', options);
        }}
        setInterval(updateClock, 1000);
        updateClock();

        function handleSearch(e) {{
            e.preventDefault();
            const val = document.getElementById('searchBar').value.trim();
            if (!val) return;
            if (val.startsWith('http://') || val.startsWith('https://')) {{
                window.location.href = val;
            }} else if (val.includes('.') && !val.includes(' ')) {{
                window.location.href = 'https://' + val;
            }} else {{
                window.location.href = 'https://duckduckgo.com/?q=' + encodeURIComponent(val);
            }}
        }}
    </script>
</body>
</html>
"""
    return html
